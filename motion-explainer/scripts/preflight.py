#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""preflight — motion-explainer 开跑前的只读能力探针。

不生成任何东西、不花任何积分(除非 --probe-auth,那会跑一次 *免费* 的
gflow 图像生成来验证 Flow 会话是否真的活着)。

    uv run --script preflight.py                # 本地能力检查
    uv run --script preflight.py --probe-auth   # 额外做一次免费图像探活(~40s)

退出码: 0 = 全部 GO / 1 = 有 NO-GO 项。WARN 不影响退出码。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# 装配必需的 ffmpeg 滤镜。缺任何一个 assemble.py 都跑不了。
REQUIRED_FILTERS = [
    "scale", "pad", "setsar", "fps", "settb", "setpts", "tpad", "overlay",
    "concat", "aformat", "aresample", "adelay", "apad", "atrim", "atempo",
    "volume", "asplit", "sidechaincompress", "amix",
]
REQUIRED_ENCODERS = ["libx264", "aac"]

# 字幕烧录的字体候选,按偏好排序。Anton 是 Vox 风格的原味选择。
FONT_CANDIDATES = [
    Path.home() / "Library/Fonts/Anton-Regular.ttf",
    Path("/Library/Fonts/Anton-Regular.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Black.ttf"),
    Path("/System/Library/Fonts/Supplemental/Impact.ttf"),
]

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"

rows: list[tuple[str, str, str, str]] = []  # (verdict, item, detail, hint)


def add(verdict: str, item: str, detail: str = "", hint: str = "") -> None:
    rows.append((verdict, item, detail, hint))


def run(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


# --------------------------------------------------------------------------- #
# ffmpeg / ffprobe
# --------------------------------------------------------------------------- #
def check_ffmpeg() -> dict:
    info: dict = {"subtitle_tier": None}
    ff = shutil.which("ffmpeg")
    fp = shutil.which("ffprobe")
    if not ff or not fp:
        add("NO-GO", "ffmpeg / ffprobe", "未安装", "brew install ffmpeg")
        return info

    rc, out, _ = run([ff, "-hide_banner", "-version"])
    ver = out.splitlines()[0].split()[2] if out else "?"
    add("GO", "ffmpeg", f"{ver}  {ff}")

    rc, filters, _ = run([ff, "-hide_banner", "-filters"])
    have = {ln.split()[1] for ln in filters.splitlines() if len(ln.split()) > 2 and ln.startswith(" ")}
    missing = [f for f in REQUIRED_FILTERS if f not in have]
    if missing:
        add("NO-GO", "ffmpeg 滤镜", f"缺: {', '.join(missing)}", "换一个功能更全的 ffmpeg 构建")
    else:
        add("GO", "ffmpeg 滤镜", f"装配所需 {len(REQUIRED_FILTERS)} 个滤镜齐全")

    rc, encs, _ = run([ff, "-hide_banner", "-encoders"])
    for enc in REQUIRED_ENCODERS:
        if f" {enc} " not in encs:
            add("NO-GO", f"编码器 {enc}", "缺失")

    # 字幕分层:有 subtitles 滤镜(libass)最好,没有就走 Pillow overlay。
    if "subtitles" in have:
        info["subtitle_tier"] = 1
        add("GO", "字幕", "tier-1: ffmpeg 有 subtitles 滤镜(libass),直接烧 SRT")
    else:
        info["subtitle_tier"] = 2
        add("WARN", "字幕", "tier-2: ffmpeg 无 libass → 走 Pillow 渲 PNG + overlay",
            "这是本机的正常状态;homebrew-core 的 ffmpeg 公式本身不含 libass")
    return info


def check_font() -> None:
    for f in FONT_CANDIDATES:
        if f.exists():
            tag = "GO" if "Anton" in f.name else "WARN"
            note = "" if tag == "GO" else "想要原味 Vox 观感: brew install --cask font-anton"
            add(tag, "字幕字体", str(f), note)
            return
    add("NO-GO", "字幕字体", "找不到任何候选字体",
        "brew install --cask font-anton,或用 assemble.py --font 指定")


def check_pillow() -> None:
    rc, out, err = run(["uv", "run", "--quiet", "--with", "pillow>=10",
                        "python", "-c", "import PIL;print(PIL.__version__)"], timeout=120)
    if rc == 0:
        add("GO", "Pillow", f"{out.strip()} (uv 按需装,字幕渲染用)")
    else:
        add("WARN", "Pillow", "uv 拉取失败", "首次联网时 uv 会自动装;离线环境需预装")


# --------------------------------------------------------------------------- #
# vox (TTS)
# --------------------------------------------------------------------------- #
def check_vox() -> None:
    vox = shutil.which("vox")
    if not vox:
        add("NO-GO", "vox (TTS)", "未安装", "见 references/narration.md;或改用 ElevenLabs 后端")
        return
    rc, out, err = run([vox, "--version"])
    add("GO", "vox", f"{(out or err).strip() or 'ok'}  {vox}")

    rc, out, err = run([vox, "voices"], timeout=60)
    if rc == 0:
        n = len([l for l in out.splitlines() if l.strip()])
        add("GO", "vox 音色", f"voices 可列出({n} 行输出)")
    else:
        add("WARN", "vox 音色", "vox voices 失败", (err or out).strip()[:120])


# --------------------------------------------------------------------------- #
# gflow
# --------------------------------------------------------------------------- #
def check_gflow(probe_auth: bool) -> None:
    gflow = shutil.which("gflow")
    if not gflow:
        add("NO-GO", "gflow", "未安装", "uv tool install gflow-cli")
        return
    rc, out, err = run([gflow, "--version"])
    add("GO", "gflow", f"{(out or err).strip()}  {gflow}")

    # profile 数直接数目录 —— `gflow auth list` 是 rich 表格,列会换行,按行数统计必错。
    gflow_home = Path(os.environ.get("GFLOW_CLI_HOME") or
                      Path.home() / "Library/Application Support/gflow-cli")
    profiles = sorted(p.name[len("profile_"):] for p in gflow_home.glob("profile_*") if p.is_dir())
    if not profiles:
        add("NO-GO", "gflow profile", f"{gflow_home} 下没有 profile_*",
            "gflow auth login --browser chrome")
        return
    add("WARN" if len(profiles) == 1 else "GO", "gflow 并发度",
        f"{len(profiles)} 个 profile: {', '.join(profiles)}",
        "单 profile = 同时只能跑一个生成,全流程串行,6 块约 20 分钟。"
        "加并发需要第二个 Google 账号" if len(profiles) == 1 else "")

    # Chrome profile 有没有被标记成「崩溃过」。
    # 这不只是弹个「Restore pages?」气泡烦人 —— 那个气泡会**盖住 Flow 的输入框**,
    # 直接导致 UiSelectorDriftError / mode_switch_miss。
    # 成因几乎总是有人对 Chrome 用了 kill -9(清理卡住的 profile 时最容易犯)。
    pref = gflow_home / f"profile_{profiles[0]}/Default/Preferences"
    if pref.exists():
        try:
            prof = json.loads(pref.read_text(errors="replace")).get("profile", {})
            if prof.get("exit_type") not in (None, "Normal"):
                add("WARN", "Chrome profile", f"被标记为 {prof.get('exit_type')}",
                    "启动时会弹 Restore pages? 气泡并可能盖住 Flow 输入框 → 选择器失配。"
                    "关掉 Chrome 后把 Preferences 里 profile.exit_type 改成 Normal。"
                    "别再用 kill -9 收 Chrome")
        except (json.JSONDecodeError, OSError):
            pass

    # 最近的错误记录:今天有 auth-expired 就是强信号
    rc, out, _ = run([gflow, "data", "list", "errors", "--json", "--limit", "5"], timeout=60)
    if rc == 0 and out.strip():
        try:
            data = json.loads(out)
            errs = data if isinstance(data, list) else data.get("errors", [])
            slugs = [e.get("error_type") or e.get("type") or "" for e in errs[:5]]
            if any("auth" in (s or "") for s in slugs):
                add("WARN", "gflow 最近错误", f"含认证类: {', '.join(s for s in slugs if s)[:80]}",
                    "会话可能已过期,建议加 --probe-auth 实测")
        except (json.JSONDecodeError, AttributeError):
            pass

    if not probe_auth:
        add("WARN", "gflow 会话存活", "未探测(auth status 只查文件存在,不代表会话有效)",
            "加 --probe-auth 跑一次免费图像生成来实测")
        return

    with tempfile.TemporaryDirectory() as td:
        add("…", "gflow 会话存活", "正在跑一次免费图像生成(约 40-90s)…")
        _flush()
        rows.pop()
        rc, out, err = run(
            [gflow, "image", "t2i", "a plain grey square, flat color, nothing else",
             "--model", "nano2", "--aspect", "1:1", "-n", "1", "--out", td, "--json"],
            timeout=300)
        if rc == 0:
            add("GO", "gflow 会话存活", "免费图像生成通过 → Flow 会话有效")
        else:
            tail = (err or out).strip().splitlines()[-1:] or [""]
            add("NO-GO", "gflow 会话存活", f"exit={rc} {tail[0][:100]}",
                "gflow auth login --browser chrome,登录后等 5 秒再 Cmd+Q 整个 Chrome")


def _iter_mcp_servers(obj, path="root"):
    """递归找出配置里所有的 mcpServers 字典。

    不能用 'gflow' 子串匹配整个文件 —— .claude.json 里存着每个项目的路径,
    而用户恰好有一个 ~/Github/gflow-cli 目录,子串匹配必然假阳性。
    """
    if isinstance(obj, dict):
        servers = obj.get("mcpServers")
        if isinstance(servers, dict):
            for name, spec in servers.items():
                yield path, name, spec
        for k, v in obj.items():
            if k != "mcpServers":
                yield from _iter_mcp_servers(v, f"{path}/{k}")


def check_veo_gen() -> None:
    """CLI 路线的关键依赖:出片永远通过 veo-gen(它带信用取证与白名单重试)。"""
    vg = Path(__file__).resolve().parent / "veo-gen"
    if not vg.exists():
        add("NO-GO", "veo-gen", f"缺失 {vg}", "从 skills/flow-media/scripts/ 复制并按 SKILL.md 改两处")
        return
    if not os.access(vg, os.X_OK):
        add("NO-GO", "veo-gen", "不可执行", f"chmod +x {vg}")
        return
    body = vg.read_text(encoding="utf-8", errors="replace")
    if "GFLOW_CLI_UI_MODE" not in body:
        add("WARN", "veo-gen", "没看到 GFLOW_CLI_UI_MODE",
            "本机账号被灰度到 agentic UI,视频必须走 classic")
        return
    add("GO", "veo-gen", "就位,UI_MODE=classic + generate_captured 信用取证")

    rec = Path(__file__).resolve().parent / "recover-media.py"
    if not rec.exists():
        add("WARN", "recover-media", "缺失",
            "gflow 约 1/3 概率「生成成功但没取回来」,没有它这些积分就白花了")
        return
    # 顺带报一下现在有多少已扣分但没落盘的产物待取回
    try:
        import sqlite3
        db = (Path(os.environ.get("GFLOW_CLI_HOME") or
                   Path.home() / "Library/Application Support/gflow-cli") / "gflow.db")
        n = 0
        if db.exists():
            con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            n = con.execute("SELECT COUNT(*) FROM assets a LEFT JOIN local_files f "
                            "ON f.asset_id=a.id WHERE a.kind='video' AND f.id IS NULL"
                            ).fetchone()[0]
            con.close()
        if n:
            add("WARN", "recover-media", f"就位 — 有 {n} 条已扣分但没落盘的视频",
                "uv run --script scripts/recover-media.py --out <dir> --auto 取回")
        else:
            add("GO", "recover-media", "就位,没有待取回的产物")
    except Exception:
        add("GO", "recover-media", "就位")


def check_mcp_registration() -> None:
    """gflow MCP 是否已注册。默认流程走 CLI,所以这里只是 info,不影响 GO/NO-GO。"""
    hits = []
    for cfg in (Path.home() / ".claude.json",
                Path.home() / ".claude/settings.json",
                Path.home() / ".mcp.json"):
        if not cfg.exists():
            continue
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for scope, name, spec in _iter_mcp_servers(data):
            blob = json.dumps(spec, ensure_ascii=False)
            if "gflow" in name.lower() or "gflow" in blob:
                hits.append((cfg.name, scope, name, spec))

    if not hits:
        add("GO", "gflow MCP", "未注册 —— 默认流程走 CLI,不需要它")
        return

    cfgname, scope, name, spec = hits[0]
    env = spec.get("env") or {}
    tool_timeout = int(os.environ.get("MCP_TOOL_TIMEOUT") or 0)
    notes = []
    if env.get("GFLOW_CLI_UI_MODE") != "classic":
        notes.append("env 缺 GFLOW_CLI_UI_MODE=classic")
    if tool_timeout and tool_timeout < 300_000:
        notes.append(f"MCP_TOOL_TIMEOUT={tool_timeout}ms < 300s")
    if notes:
        add("WARN", "gflow MCP", f"{name} @ {cfgname}(可选路线):{'; '.join(notes)}",
            "只在真要用 MCP 时才需要修;默认走 CLI 不受影响")
    else:
        add("GO", "gflow MCP", f"{name} @ {cfgname},配置正确(可选路线)")


def check_disk() -> None:
    st = shutil.disk_usage(Path.home())
    free_gb = st.free / 1024 ** 3
    add("GO" if free_gb > 5 else "WARN", "磁盘", f"{free_gb:.1f} GB 可用",
        "" if free_gb > 5 else "一次 6 块的运行大约要 1-2 GB")


# --------------------------------------------------------------------------- #
def _flush() -> None:
    sys.stdout.flush()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--probe-auth", action="store_true",
                    help="额外跑一次免费的 gflow 图像生成,实测 Flow 会话是否有效(约 40-90s)")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    ffinfo = check_ffmpeg()
    check_font()
    check_pillow()
    check_vox()
    check_gflow(args.probe_auth)
    check_veo_gen()
    check_mcp_registration()
    check_disk()

    nogo = [r for r in rows if r[0] == "NO-GO"]

    if args.json:
        print(json.dumps({
            "go": not nogo,
            "subtitle_tier": ffinfo.get("subtitle_tier"),
            "rows": [{"verdict": v, "item": i, "detail": d, "hint": h} for v, i, d, h in rows],
        }, ensure_ascii=False, indent=2))
        return 1 if nogo else 0

    w = max(len(r[1]) for r in rows) + 2
    print(f"\n{DIM}motion-explainer preflight{RESET}\n")
    for verdict, item, detail, hint in rows:
        color = {"GO": GREEN, "NO-GO": RED, "WARN": YELLOW}.get(verdict, DIM)
        print(f"  {color}{verdict:<6}{RESET} {item:<{w}} {detail}")
        if hint:
            print(f"  {'':<6} {'':<{w}} {DIM}↳ {hint}{RESET}")
    print()
    if nogo:
        print(f"{RED}NO-GO{RESET} — 先修上面 {len(nogo)} 项再开跑。\n")
        return 1
    print(f"{GREEN}GO{RESET} — 可以开跑。"
          f"{'' if args.probe_auth else ' (会话存活未实测,加 --probe-auth 更稳)'}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
