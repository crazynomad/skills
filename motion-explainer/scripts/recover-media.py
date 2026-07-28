#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.45"]
# ///
"""recover-media — 把「已扣积分但没下载下来」的 Flow 产物取回本地。

## 为什么需要它

gflow 0.44.0 有一个高频失败模式(本机实测约 1/3 概率):Veo 那边生成**成功**了
(日志里 `poll_terminal → MEDIA_GENERATION_STATUS_SUCCESSFUL`,积分已扣),
紧接着在取回产物那一步抛一个裸 `Error` 崩掉。结果是:钱花了,片子留在 Flow 上,
本地 `local_path` 是 null。

gflow 自己**没有**「下载已有 media」的命令:
  - `gflow data media <id>` 只给元数据,没有地址
  - `gflow scene create` 要 workflowId,而本地 assets 表里那一列**是空的**
  - `--har` 也救不了 —— 崩溃发生在发起下载请求之前,HAR 里只有静态资源

但下载本身是个**确定性的 URL**(见 gflow 源码 `api/routes.py:49` 与
`api/transports/ui_automation_video.py::_download_video`):

    https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<media_id>

它 302 到一个签名的 GCS 地址。所以只要用同一个 profile 的浏览器上下文发这个
请求,就能把产物拿回来 —— 这正是本脚本做的事。

## 根因(2026-07-27 实测,三次失败堆栈完全一致)

    APIRequestContext.get: Client network socket disconnected
    before secure TLS connection was established
      → GET .../media.getMediaUrlRedirect?name=<media_id>

**是到 labs.google 的 TLS 握手被掐断,不是 gflow 的逻辑 bug。** gflow 不重试
这个错,直接抛成裸 `UnexpectedError` —— 于是一次网络抖动 = 一个积分打水漂。

同一条网络问题还表现为:`gflow auth login` 的验证步骤报 ConnectError(其实登录
成功了)、`FlowAppError`「Flow web app crashed before the editor rendered」、
HuggingFace 拉模型无限期挂住。**在到 Google 链路不稳的网络环境下,这些都会反复出现。**

所以本脚本的核心不是「事后补救」,而是**把那一发免费且幂等的 GET 重试到成功**。

## 用法

    # 取回指定的 media(默认重试 6 次,指数退避)
    uv run --script recover-media.py --out ./clips <media_id> [<media_id>…]

    # 自动找出所有「成功但没落盘」的视频并取回
    uv run --script recover-media.py --out ./clips --auto

    # 取回后按块号重命名
    uv run --script recover-media.py --out ./clips <media_id> --as block02.mp4

前置:没有其它 gflow 进程正握着 profile(单 profile 不能并发)。
veo-gen 退出后 profile 就是空闲的,所以出片失败后可以**立即**调用本脚本。
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
import sys
from pathlib import Path

DOWNLOAD_URL = "https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name={}"
GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def gflow_home() -> Path:
    return Path(os.environ.get("GFLOW_CLI_HOME") or
                Path.home() / "Library/Application Support/gflow-cli")


def profile_dir(name: str) -> Path:
    d = gflow_home() / f"profile_{name}"
    if not d.is_dir():
        sys.exit(f"{RED}找不到 profile 目录 {d}{RESET}")
    return d


def channel_for(profile: Path) -> str | None:
    """gflow 在 profile 里留了一个 .gflow_browser_strategy 标记。

    标记是 chrome 就必须用 channel="chrome" —— Playwright 自带的 Chromium
    打不开 Chrome 130+ 建的 profile(会以 exit 33 的清理失败告终)。
    """
    marker = profile / ".gflow_browser_strategy"
    if marker.exists() and marker.read_text(errors="replace").strip() == "chrome":
        return "chrome"
    return None


def orphans(profile_name: str) -> list[tuple[str, str, float]]:
    """从 gflow 的本地库里找出「状态成功但没有本地文件」的视频。"""
    db = gflow_home() / "gflow.db"
    if not db.exists():
        return []
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = con.execute(
            """
            SELECT a.flow_media_id, a.flow_project_id, COALESCE(a.duration_seconds, 0)
            FROM assets a
            LEFT JOIN local_files f ON f.asset_id = a.id
            WHERE a.kind = 'video'
              AND a.profile_name = ?
              AND f.id IS NULL
            ORDER BY a.created_at DESC
            """, (profile_name,)).fetchall()
    except sqlite3.Error:
        # 表结构变了就退回「全部视频」,由调用方自己筛
        rows = con.execute(
            "SELECT flow_media_id, flow_project_id, COALESCE(duration_seconds,0) "
            "FROM assets WHERE kind='video' AND profile_name=? ORDER BY created_at DESC",
            (profile_name,)).fetchall()
    finally:
        con.close()
    return rows


async def _get_with_retry(ctx, mid: str, tries: int, quiet: bool = False):
    """下载那一发 GET,带指数退避重试。

    根因就在这里:实测三次「生成成功但没取回来」,底层异常完全一致 ——
      APIRequestContext.get: Client network socket disconnected
      before secure TLS connection was established
    也就是到 labs.google 的 TLS 握手被掐断。gflow 不重试它,直接抛成裸
    UnexpectedError,于是一次网络抖动 = 一个积分打水漂。

    这个 GET **免费且幂等**(只是换一个签名 URL 再取一遍已经生成好的文件),
    所以没有任何理由不重试。
    """
    last = None
    for attempt in range(1, tries + 1):
        try:
            resp = await ctx.request.get(DOWNLOAD_URL.format(mid),
                                         max_redirects=5, timeout=180_000)
            if resp.status < 400:
                return resp
            last = f"HTTP {resp.status}"
            if resp.status == 404:      # 链接过期,重试没用
                return None
        except Exception as e:
            last = str(e).splitlines()[0][:120]
        if attempt < tries:
            delay = min(2 ** attempt, 30)
            if not quiet:
                print(f"{DIM}   第 {attempt} 次失败({last}),{delay}s 后重试{RESET}")
            await asyncio.sleep(delay)
    print(f"{RED}✗ {mid}: {tries} 次都失败,最后 {last}{RESET}")
    return None


async def fetch(media_ids: list[str], out_dir: Path, profile: Path,
                names: list[str] | None, tries: int) -> int:
    from playwright.async_api import async_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    ok = 0
    async with async_playwright() as pw:
        kwargs: dict = {"user_data_dir": str(profile), "headless": False}
        ch = channel_for(profile)
        if ch:
            kwargs["channel"] = ch
        ctx = await pw.chromium.launch_persistent_context(**kwargs)
        try:
            # 不做 page.goto:那是又一次会被同样的网络抖动打断的请求
            # (实测栽在 ERR_CONNECTION_CLOSED 上)。持久化上下文本身就带着
            # profile 里的 cookie,ctx.request 直接可用。
            for i, mid in enumerate(media_ids):
                name = (names[i] if names and i < len(names) else f"{mid}.mp4")
                dest = out_dir / name
                if dest.exists():
                    print(f"{DIM}跳过(已存在) {dest.name}{RESET}")
                    ok += 1
                    continue
                resp = await _get_with_retry(ctx, mid, tries)
                if resp is None:
                    continue
                body = await resp.body()
                if len(body) < 10_000:
                    print(f"{RED}✗ {mid}: 只拿到 {len(body)} 字节,大概率不是视频{RESET}")
                    continue
                dest.write_bytes(body)
                print(f"{GREEN}✓{RESET} {dest}  ({len(body)/1e6:.1f} MB)")
                ok += 1
        finally:
            await ctx.close()
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("media_ids", nargs="*", help="要取回的 Flow media id")
    ap.add_argument("--out", type=Path, required=True, help="输出目录")
    ap.add_argument("--profile", default="", help="gflow profile 名(默认取唯一的那个)")
    ap.add_argument("--auto", action="store_true",
                    help="自动找出本地库里「成功但没落盘」的视频")
    ap.add_argument("--tries", type=int, default=6,
                    help="每条的下载重试次数(免费且幂等,默认 6)")
    ap.add_argument("--as", dest="names", nargs="*", default=None,
                    help="按顺序给取回的文件重命名,如 block02.mp4 block04.mp4")
    args = ap.parse_args()

    pname = args.profile
    if not pname:
        cand = sorted(p.name[len("profile_"):] for p in gflow_home().glob("profile_*") if p.is_dir())
        if len(cand) != 1:
            sys.exit(f"{RED}有 {len(cand)} 个 profile,请用 --profile 指定: {cand}{RESET}")
        pname = cand[0]

    ids = list(args.media_ids)
    if args.auto:
        found = orphans(pname)
        print(f"{DIM}本地库里「成功但没落盘」的视频 {len(found)} 条{RESET}")
        for mid, proj, dur in found:
            print(f"  {mid}  {dur:.0f}s  project={proj}")
            if mid not in ids:
                ids.append(mid)
    if not ids:
        sys.exit(f"{YELLOW}没有要取回的 media —— 给几个 id,或用 --auto{RESET}")

    prof = profile_dir(pname)
    print(f"{DIM}profile {pname} · {len(ids)} 条待取回{RESET}")
    n = asyncio.run(fetch(ids, args.out, prof, args.names, args.tries))
    print(f"\n{GREEN if n == len(ids) else YELLOW}取回 {n}/{len(ids)}{RESET}")
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
