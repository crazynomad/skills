#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""narrate — 旁白生成 + 时长测量 + 选桶,产出 assemble.py 要吃的 manifest.json。

这是「音频驱动变长 block」的实现:先把旁白做出来,量出真实秒数,再由它决定
每块视频该生成几秒。顺序反过来(先出片再配音)就会退回 Higgsfield 那套
「短音居中听着不同步 / 长音提速听着赶」的老毛病。

两种用法:

  1) vox 本地合成(默认)
       uv run --script narrate.py --blocks blocks.json --run ./run --voice vivian

  2) 只测量(旁白已由别处生成,比如 ElevenLabs MCP)
       把 wav 放成 <run>/vo/blockNN.wav,然后:
       uv run --script narrate.py --blocks blocks.json --run ./run --measure-only

blocks.json:
    {"aspect": "9:16", "blocks": [{"n": 1, "text": "..."}, {"n": 2, "text": "..."}]}
  或直接给一个数组 [{"n":1,"text":"..."}, ...]

产物: <run>/vo/blockNN.wav(原始) blockNN.norm.wav(响度归一) blockNN.srt
      <run>/manifest.json

幂等:产物比输入新就跳过。--force 强制重做。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# i2v 只接受 4/6/8 秒 —— 10 秒是 omni-flash 独有,而 omni-flash 会静默丢弃首帧
# (gflow issue #125),所以走关键帧→i2v 这条路时 10 秒不可用。
BUCKETS = (4, 6, 8)
TAIL_PAD = 0.25          # 旁白结束到切点之间留的呼吸,秒
TARGET_LUFS = -16.0      # 旁白响度目标(人声在 -16 LUFS,片底噪声再压下去)

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def die(msg: str) -> None:
    print(f"{RED}[narrate] {msg}{RESET}", file=sys.stderr)
    sys.exit(1)


def info(msg: str) -> None:
    print(f"{DIM}[narrate] {msg}{RESET}", file=sys.stderr)


def run(cmd: list[str], timeout: int = 1800) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def probe_duration(path: Path) -> float:
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)], timeout=60)
    if p.returncode != 0:
        die(f"ffprobe 读不出 {path}: {p.stderr.strip()}")
    return float(p.stdout.strip())


def load_blocks(path: Path) -> tuple[dict, list[dict]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {}, data
    return data, data.get("blocks", [])


def newer(out: Path, *ins: Path) -> bool:
    """out 存在且比所有输入都新 → 可以跳过。"""
    if not out.exists():
        return False
    t = out.stat().st_mtime
    return all((not i.exists()) or i.stat().st_mtime <= t for i in ins)


# --------------------------------------------------------------------------- #
def synth_vox(text: str, out_dir: Path, prefix: str, voice: str, model: str,
              speed: float, allow_download: bool) -> Path:
    """跑一次 vox speak,返回生成的 wav 路径。

    用 -n <prefix> 逐条合成而不是 `vox batch`:batch 没有 --name,块号与文件的
    对应关系要靠输出顺序去猜,猜错就是静默的音画错位 —— 那是最贵的一类 bug。
    想省掉模型反复加载的开销,先在另一个终端跑 `vox serve`。

    默认强制 HF_HUB_OFFLINE=1。实测:模型已缓存时,离线跑完整条只要约 1.8 秒
    (模型加载 1.4s);不加这个变量,HuggingFace 的联网检查会**无限期挂住** ——
    卡十分钟不出一个字符,而且没有任何提示。模型没缓存时会立刻报错,
    那时用 --allow-download 单独跑一次把模型拉下来。
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob(f"{prefix}*"):
        stale.unlink()
    cmd = ["vox", "speak", text, "-v", voice, "-m", model,
           "-o", str(out_dir), "-n", prefix, "--subtitle", "srt"]
    if speed != 1.0:
        cmd += ["-s", str(speed)]

    env = dict(os.environ)
    if not allow_download:
        env["HF_HUB_OFFLINE"] = "1"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900, env=env)
    except subprocess.TimeoutExpired:
        die(f"vox speak 超时({prefix})。若不是加了 --allow-download,"
            f"这不该发生 —— 检查 vox 是否卡在模型加载")
    if p.returncode != 0:
        msg = (p.stderr or p.stdout).strip()[-500:]
        hint = ""
        if not allow_download and ("offline" in msg.lower() or "not found" in msg.lower()
                                   or "cache" in msg.lower()):
            hint = (f"\n  看起来是模型 '{model}' 没缓存。先单独跑一次把它拉下来:"
                    f"\n    vox speak \"test\" -m {model} -o /tmp"
                    f"\n  或本次加 --allow-download(会联网,可能很慢)")
        die(f"vox speak 失败({prefix}): {msg}{hint}")

    wavs = sorted(w for w in out_dir.glob(f"{prefix}*.wav")
                  if not w.name.endswith(".norm.wav"))
    if not wavs:
        die(f"vox 跑完了但 {out_dir} 下找不到 {prefix}*.wav — 检查 vox 版本的输出命名")
    return wavs[0]


def loudnorm(src: Path, dst: Path) -> None:
    """响度归一到 TARGET_LUFS,并统一成 48k 立体声。

    必须在这里做、并且量时长要量归一后的文件:loudnorm 会把时长改动几十毫秒,
    「先量原始 wav → 选桶 → 再归一」会让选桶依据失效。
    """
    p = run(["ffmpeg", "-y", "-v", "error", "-i", str(src),
             "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11,aresample=48000",
             "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(dst)], timeout=300)
    if p.returncode != 0:
        die(f"loudnorm 失败 {src}: {p.stderr.strip()[-400:]}")


def pick_bucket(dur: float) -> tuple[int | None, str]:
    need = dur + TAIL_PAD
    for b in BUCKETS:
        if b >= need:
            note = ""
            if b == BUCKETS[0]:
                note = ("只需 4s — 考虑和相邻块合并:每条 clip 无论 4s 还是 8s "
                        "都是 1 积分,切点越密越贵也越碎")
            return b, note
    return None, (f"旁白 {dur:.2f}s 超过最长桶 {BUCKETS[-1]}s — 必须改写这一块 "
                  f"(目标 ≤{BUCKETS[-1] - TAIL_PAD:.2f}s,约 {int((BUCKETS[-1]-TAIL_PAD)*2.2)} 词以内)")


def offset_srt(srt: Path) -> list[dict]:
    """把一块的 SRT 读成 [{start,end,text}] (块内 0 基秒)。"""
    if not srt.exists():
        return []
    cues: list[dict] = []
    pat = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d{1,3})")

    def secs(m: re.Match) -> float:
        h, mnt, s, ms = (int(g) for g in m.groups())
        return h * 3600 + mnt * 60 + s + ms / 1000.0

    for chunk in re.split(r"\n\s*\n", srt.read_text(encoding="utf-8", errors="replace").strip()):
        lines = [l for l in chunk.splitlines() if l.strip()]
        if len(lines) < 2:
            continue
        tl = next((l for l in lines if "-->" in l), None)
        if not tl:
            continue
        ts = list(pat.finditer(tl))
        if len(ts) < 2:
            continue
        text = " ".join(lines[lines.index(tl) + 1:]).strip()
        if text:
            cues.append({"start": secs(ts[0]), "end": secs(ts[1]), "text": text})
    return cues


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--blocks", required=True, type=Path, help="blocks.json")
    ap.add_argument("--run", required=True, type=Path, help="运行目录(产物都落这里)")
    ap.add_argument("--voice", default="vivian", help="vox 音色,`vox voices` 可列出")
    ap.add_argument("--model", default="large", help="vox 模型 small/large/large-hq")
    ap.add_argument("--speed", type=float, default=1.0, help="vox 语速倍率")
    ap.add_argument("--aspect", default=None, help="9:16 或 16:9(覆盖 blocks.json 里的值)")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--measure-only", action="store_true",
                    help="不合成,只对已存在的 <run>/vo/blockNN.wav 做归一+测量+选桶")
    ap.add_argument("--allow-download", action="store_true",
                    help="允许 vox 联网拉模型(默认强制离线 —— HF 的联网检查会无限期挂住)")
    ap.add_argument("--force", action="store_true", help="忽略幂等,全部重做")
    args = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        die("找不到 ffmpeg/ffprobe")
    if not args.measure_only and not shutil.which("vox"):
        die("找不到 vox。要么装 vox,要么用 --measure-only 配合别的 TTS")

    meta, blocks = load_blocks(args.blocks)
    if not blocks:
        die(f"{args.blocks} 里没有 blocks")

    aspect = args.aspect or meta.get("aspect") or "9:16"
    if aspect not in ("9:16", "16:9"):
        die(f"aspect 只支持 9:16 / 16:9,给的是 {aspect}(gflow 视频侧不接受 1:1)")
    width, height = (720, 1280) if aspect == "9:16" else (1280, 720)

    vo = args.run / "vo"
    vo.mkdir(parents=True, exist_ok=True)

    # 已有 manifest 里的 clip 路径要保住 —— 那些是已经花过积分的产物。
    # 「改一句文案重配音」不该把整批 clip 的引用冲掉。
    mpath = args.run / "manifest.json"
    prev_clips: dict[int, str] = {}
    prev_hash: dict[int, str] = {}
    if mpath.exists():
        try:
            for b in json.loads(mpath.read_text(encoding="utf-8")).get("blocks", []):
                n = int(b["n"])
                if b.get("clip"):
                    prev_clips[n] = b["clip"]
                if b.get("text_sha"):
                    prev_hash[n] = b["text_sha"]
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    out_blocks: list[dict] = []
    problems: list[str] = []
    srt_warned = False

    for blk in blocks:
        n = int(blk["n"])
        text = (blk.get("text") or "").strip()
        if not text:
            die(f"block {n} 没有 text")
        prefix = f"block{n:02d}"
        text_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        norm = vo / f"{prefix}.norm.wav"
        srt = vo / f"{prefix}.srt"

        if args.measure_only:
            cand = sorted(vo.glob(f"{prefix}*.wav"))
            cand = [c for c in cand if not c.name.endswith(".norm.wav")]
            if not cand:
                die(f"--measure-only 但找不到 {vo}/{prefix}*.wav")
            raw = cand[0]
        elif not args.force and norm.exists() and prev_hash.get(n) == text_sha:
            # 幂等判据用「这一块文案的哈希」,不用 blocks.json 的 mtime。
            # 用 mtime 的话,改任何一句都会让全部块重新合成 —— 而 vox 的时长
            # 是不可复现的(实测同一句两次能差 1.6 秒),于是每块的桶位都重新
            # 掷一次骰子,改一处引发连锁超长,变成打地鼠。
            info(f"{prefix}: 跳过(文案未变)")
            raw = next((c for c in sorted(vo.glob(f"{prefix}*.wav"))
                        if not c.name.endswith(".norm.wav")), norm)
        else:
            info(f"{prefix}: vox speak …")
            raw = synth_vox(text, vo, prefix, args.voice, args.model, args.speed,
                            args.allow_download)

        if args.force or not newer(norm, raw):
            loudnorm(raw, norm)

        dur = probe_duration(norm)
        bucket, note = pick_bucket(dur)
        cues = offset_srt(srt)
        if not cues:
            # vox 的 --subtitle 依赖一个单独的强制对齐模型(Qwen3-ForcedAligner)。
            # 没缓存 + 离线 → 静默失败,但音频是好的。整块一条 cue 是完全可用的兜底
            # (整句字幕本来就是这个片种的常规做法),只是不如词级精细。
            cues = [{"start": 0.0, "end": dur, "text": text}]
            if not srt_warned:
                info("字幕退化为「整块一条 cue」—— vox 的强制对齐模型没缓存。"
                     "想要词级字幕,单独跑一次联网的:"
                     "vox speak \"test\" -m large -o /tmp --subtitle srt")
                srt_warned = True

        badge = f"{GREEN}{bucket}s{RESET}" if bucket else f"{RED}超长{RESET}"
        print(f"  block{n:02d}  {dur:5.2f}s → 桶 {badge}"
              f"{'  ' + YELLOW + note + RESET if note else ''}", file=sys.stderr)
        if bucket is None:
            problems.append(f"block {n}: {note}")

        out_blocks.append({
            "n": n,
            "text": text,
            "narration": str(norm),
            "narration_sec": round(dur, 3),
            "srt": str(srt) if srt.exists() else None,
            "cues": cues,
            "bucket": bucket,
            "text_sha": text_sha,
            # 出片阶段回填。旧 manifest 里已有的优先保留(见上)。
            "clip": blk.get("clip") or prev_clips.get(n),
        })

    manifest = {
        "aspect": aspect, "width": width, "height": height, "fps": args.fps,
        "voice": None if args.measure_only else args.voice,
        "tail_pad": TAIL_PAD,
        "blocks": out_blocks,
    }
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if problems:
        print(f"\n{RED}✗ 有 {len(problems)} 块旁白超长,必须先改写再出片:{RESET}", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(f"\n{DIM}manifest 已写到 {mpath},但超长块的 bucket 是 null —— "
              f"改完文案重跑本脚本,别急着出片。{RESET}", file=sys.stderr)
        return 3

    total = sum(b["bucket"] for b in out_blocks)
    done = sum(1 for b in out_blocks if b.get("clip"))
    print(f"\n{GREEN}✓{RESET} {mpath}", file=sys.stderr)
    print(f"  {len(out_blocks)} 块,视频总长 {total}s,"
          f"待出片 {len(out_blocks) - done} 条 = {len(out_blocks) - done} 积分"
          f"(每条 clip 1 积分,与时长无关)", file=sys.stderr)
    if done:
        print(f"  {done} 条 clip 已在 manifest 里,本次保留未动", file=sys.stderr)
    print(f"  下一步:按每块的 bucket 出片 → 回填 clip 路径 → assemble.py", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
