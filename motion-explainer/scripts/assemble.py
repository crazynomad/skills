#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow>=10"]
# ///
"""assemble — manifest.json → 一条成片 MP4(+ 旁挂 final.srt)。

补上 gflow 完全没有的三块能力:把旁白混到 clip 的原生音之上(并把原生音压下去)、
把字幕烧进画面、把 N 块拼成一条。

    uv run --script assemble.py --manifest run/manifest.json --out run/final.mp4

设计要点(改动前先读 references/assembly.md):

  * 两遍走。先逐块归一化到完全一致的流参数,再用 concat demuxer + `-c copy` 拼。
    不用单个 N 输入的 filter_complex:任意一条 Veo clip 的坏时基会毒化整张图,
    而且第 5 块失败要全量重来。
  * `-c copy` 只有在所有块的 W/H/SAR/pix_fmt/fps/timescale/profile/音频参数
    完全一致时才安全 —— 不一致时 concat demuxer **不报错**,只产生逐块累积的
    音画漂移。所以拼接前有一道强制的 ffprobe 一致性闸门。
  * 字幕默认走 Pillow 渲 PNG + overlay:本机 ffmpeg 不含 libass,`subtitles` 与
    `drawtext` 滤镜都不存在(homebrew-core 的 ffmpeg 公式本身就不带)。脚本会
    探测,将来 ffmpeg 修好了自动走 subtitles 滤镜。
  * 字幕按块烧、时间戳是块内 0 基的,所以烧录路径完全没有全局偏移算术。
    合并成一条全局 final.srt 只是给 YouTube 用的旁挂文件,纯文本操作。
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

TIMESCALE = 15360        # 统一时基,防 concat 逐块累积漂移
VO_DELAY_MS = 120        # 旁白开头留一点气口,免得第一个音素贴着切点被削掉
MAX_ATEMPO = 1.12        # 再快纪录片男声就听得出来了
MAX_FREEZE = 0.80        # 冻结尾帧的硬上限(见下)

FONT_CANDIDATES = [
    Path.home() / "Library/Fonts/Anton-Regular.ttf",
    Path("/Library/Fonts/Anton-Regular.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Black.ttf"),
    Path("/System/Library/Fonts/Supplemental/Impact.ttf"),
    Path("/System/Library/Fonts/Helvetica.ttc"),
]

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def die(msg: str, code: int = 1) -> None:
    print(f"{RED}[assemble] {msg}{RESET}", file=sys.stderr)
    sys.exit(code)


def info(msg: str) -> None:
    print(f"{DIM}[assemble] {msg}{RESET}", file=sys.stderr)


def run(cmd: list[str], timeout: int = 3600) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def ffprobe_json(path: Path) -> dict:
    p = run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
             "-of", "json", str(path)], timeout=120)
    if p.returncode != 0:
        die(f"ffprobe 失败 {path}: {p.stderr.strip()[-300:]}")
    return json.loads(p.stdout)


def duration_of(path: Path) -> float:
    return float(ffprobe_json(path)["format"]["duration"])


def has_audio(path: Path) -> bool:
    return any(s["codec_type"] == "audio" for s in ffprobe_json(path)["streams"])


def newer(out: Path, *ins: Path) -> bool:
    if not out.exists():
        return False
    t = out.stat().st_mtime
    return all((not i.exists()) or i.stat().st_mtime <= t for i in ins)


# --------------------------------------------------------------------------- #
# 字幕
# --------------------------------------------------------------------------- #
def pick_font(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser()
        if not p.exists():
            die(f"字体不存在: {p}")
        return p
    for f in FONT_CANDIDATES:
        if f.exists():
            return f
    die("找不到任何可用字体,用 --font 指定一个 .ttf/.otf")


def render_cue_png(text: str, w: int, h: int, font_path: Path, dst: Path,
                   upper: bool = True) -> None:
    """把一条字幕渲染成整帧透明 PNG。

    整帧而不是"只画文字块 + 在 ffmpeg 里算位置":位置算错是最烦人的一类 bug,
    而整帧 PNG 让 overlay 永远是 x=0:y=0。代价只是几十 KB。
    """
    from PIL import Image, ImageDraw, ImageFont

    if upper:
        text = text.upper()
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    size = max(18, int(w / 15))
    margin = int(w * 0.08)
    stroke = max(2, size // 9)

    # 逐步缩字号,直到 3 行以内放得下
    while size > 12:
        font = ImageFont.truetype(str(font_path), size)
        avg = draw.textlength("ABCDEFGHIJ", font=font) / 10 or 1
        cols = max(6, int((w - 2 * margin) / avg))
        lines = textwrap.wrap(text, width=cols) or [text]
        widest = max(draw.textlength(l, font=font) for l in lines)
        if len(lines) <= 3 and widest <= w - 2 * margin:
            break
        size = int(size * 0.9)
    else:  # pragma: no cover
        font = ImageFont.truetype(str(font_path), size)
        lines = textwrap.wrap(text, width=24) or [text]

    line_h = int(size * 1.18)
    total_h = line_h * len(lines)
    y = h - int(h * 0.11) - total_h          # 底部安全区之上
    for line in lines:
        tw = draw.textlength(line, font=font)
        draw.text(((w - tw) / 2, y), line, font=font, fill=(255, 255, 255, 255),
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 235))
        y += line_h
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)


def srt_ts(sec: float) -> str:
    sec = max(0.0, sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


# --------------------------------------------------------------------------- #
# 时长调和
# --------------------------------------------------------------------------- #
def reconcile(clip_sec: float, narr_sec: float, pad: float) -> dict:
    """决定这一块的最终时长 D,以及画面/旁白各自要怎么迁就对方。

    优先级:什么都不做 > 给旁白提速 > 冻结尾帧 > 失败。

    冻结尾帧排在提速后面是有原因的:每条 clip 都被写成在运动模糊里结束(假一镜),
    克隆那一帧会让"一镜到底"变成"卡住了"。轻微提速几乎听不出来,视觉停滞很明显。
    """
    deficit = (narr_sec + pad) - clip_sec
    if deficit <= 0:
        return {"D": clip_sec, "tempo": 1.0, "freeze": 0.0, "mode": "clip-wins"}

    tempo = narr_sec / max(0.05, clip_sec - pad)
    if tempo <= MAX_ATEMPO:
        return {"D": clip_sec, "tempo": tempo, "freeze": 0.0, "mode": "atempo"}

    if deficit <= MAX_FREEZE:
        return {"D": narr_sec + pad, "tempo": 1.0, "freeze": deficit, "mode": "freeze"}

    return {"D": None, "tempo": tempo, "freeze": deficit, "mode": "fail",
            "why": (f"旁白 {narr_sec:.2f}s 比 clip {clip_sec:.2f}s 长 {deficit:.2f}s;"
                    f"提速要 {tempo:.2f}×(上限 {MAX_ATEMPO})、冻结要 {deficit:.2f}s"
                    f"(上限 {MAX_FREEZE}s)。改短这一块的文案,或把 clip 升到更大的桶")}


# --------------------------------------------------------------------------- #
# Pass 1 —— 逐块归一化
# --------------------------------------------------------------------------- #
def normalize_block(blk: dict, mf: dict, paths: dict, opts: argparse.Namespace,
                    font: Path, use_libass: bool) -> dict:
    n = blk["n"]
    clip = Path(blk["clip"])
    narr = Path(blk["narration"])
    if not clip.exists():
        die(f"block {n}: clip 不存在 {clip}")
    if not narr.exists():
        die(f"block {n}: 旁白不存在 {narr}")

    W, H, FPS = mf["width"], mf["height"], mf["fps"]
    pad = mf.get("tail_pad", 0.25)
    clip_sec = duration_of(clip)
    narr_sec = blk.get("narration_sec") or duration_of(narr)

    r = reconcile(clip_sec, narr_sec, pad)
    if r["mode"] == "fail":
        die(f"block {n}: {r['why']}", code=3)
    D = r["D"]
    tempo, freeze = r["tempo"], r["freeze"]
    delay = VO_DELAY_MS / 1000.0

    out = paths["norm"] / f"block{n:02d}.mp4"

    # 字幕 cue:块内 0 基,再按提速/气口平移。这两处忘了改就是字幕整体飘。
    cues = []
    for c in (blk.get("cues") or []):
        s = c["start"] / tempo + delay
        e = min(D, c["end"] / tempo + delay)
        if e > s + 0.05 and c.get("text"):
            cues.append({"start": s, "end": e, "text": c["text"]})

    cue_pngs: list[Path] = []
    if not opts.no_subs and not use_libass:
        for i, c in enumerate(cues):
            png = paths["cues"] / f"block{n:02d}_{i:02d}.png"
            if opts.force or not newer(png, narr):
                render_cue_png(c["text"], W, H, font, png, upper=not opts.no_upper)
            cue_pngs.append(png)

    deps = [clip, narr, *cue_pngs]
    if not opts.force and newer(out, *deps):
        info(f"block{n:02d}: 跳过归一化(已是最新)")
        return {"n": n, "path": out, "D": D, "cues": cues, "mode": r["mode"],
                "tempo": tempo, "freeze": freeze}

    # ---- 组装 ffmpeg 调用 -------------------------------------------------- #
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-i", str(narr)]
    # Veo 的 clip 一定带原生音,但测试素材/别处来的片子未必 —— 没有音轨就补一条静音,
    # 否则 [0:a] 这个 label 不存在,整张 filter graph 直接报错。
    if has_audio(clip):
        bed_idx, png_base = "0:a", 2
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        bed_idx, png_base = "2:a", 3
    for png in cue_pngs:
        cmd += ["-i", str(png)]

    # 视频链
    vf = ["setpts=PTS-STARTPTS"]
    if freeze > 0:
        vf.append(f"tpad=stop_mode=clone:stop_duration={freeze:.3f}")
    vf += [
        f"scale={W}:{H}:force_original_aspect_ratio=decrease",
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black",
        "setsar=1", f"fps={FPS}", f"settb=1/{TIMESCALE}",
    ]
    chains = ["[0:v]" + ",".join(vf) + "[vbase]"]

    last = "vbase"
    if opts.no_subs or not cues:
        chains.append(f"[{last}]null[vout]")
    elif use_libass:
        srt = paths["cues"] / f"block{n:02d}.srt"
        srt.write_text("\n".join(
            f"{i+1}\n{srt_ts(c['start'])} --> {srt_ts(c['end'])}\n{c['text']}\n"
            for i, c in enumerate(cues)), encoding="utf-8")
        esc = str(srt).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
        style = (f"FontName={font.stem},Fontsize={max(18,int(W/22))},"
                 f"PrimaryColour=&H00FFFFFF,BorderStyle=1,Outline=3,Shadow=0,"
                 f"Alignment=2,MarginV={int(H*0.11)}")
        chains.append(f"[{last}]subtitles='{esc}':force_style='{style}'[vout]")
    else:
        for i, c in enumerate(cues):
            nxt = f"v{i}" if i < len(cues) - 1 else "vout"
            chains.append(
                f"[{last}][{png_base + i}:v]"
                f"overlay=0:0:eof_action=repeat:enable='between(t,{c['start']:.3f},{c['end']:.3f})'"
                f"[{nxt}]")
            last = nxt

    # 音频链:两条腿都先对齐成 fltp/48k/stereo,否则 sidechaincompress 会报错或静默失常
    # (vox 出的是 24kHz mono,Veo 出的是 48kHz stereo)
    afmt = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"
    vo_chain = [f"[1:a]{afmt}", "aresample=48000"]
    if tempo > 1.0001:
        vo_chain.append(f"atempo={tempo:.4f}")
    vo_chain += [f"adelay={VO_DELAY_MS}|{VO_DELAY_MS}", "apad",
                 f"atrim=0:{D:.3f}", "asetpts=PTS-STARTPTS"]
    chains.append(",".join(vo_chain) + "[vo]")

    if opts.bed_gain <= 0.0001:
        chains.append(f"[vo]atrim=0:{D:.3f}[aout]")
    else:
        chains.append(
            f"[{bed_idx}]{afmt},aresample=48000:async=1:first_pts=0,"
            f"volume={opts.bed_gain},apad,atrim=0:{D:.3f},asetpts=PTS-STARTPTS[bed]")
        chains.append("[vo]asplit=2[vo1][sc]")
        chains.append(
            f"[bed][sc]sidechaincompress=threshold={opts.duck_threshold}:ratio=8:"
            f"attack=15:release=350:makeup=1[ducked]")
        chains.append("[ducked][vo1]amix=inputs=2:duration=first:normalize=0[aout]")

    cmd += [
        "-filter_complex", ";".join(chains),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", opts.preset, "-crf", str(opts.crf),
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
        "-r", str(FPS), "-g", str(FPS * 2), "-keyint_min", str(FPS * 2), "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-video_track_timescale", str(TIMESCALE),
        "-movflags", "+faststart", "-t", f"{D:.3f}", str(out),
    ]

    if opts.dry_run:
        print(" ".join(f"'{c}'" if " " in c or ";" in c else c for c in cmd))
        return {"n": n, "path": out, "D": D, "cues": cues, "mode": r["mode"],
                "tempo": tempo, "freeze": freeze}

    out.parent.mkdir(parents=True, exist_ok=True)
    p = run(cmd)
    if p.returncode != 0:
        die(f"block {n} 归一化失败:\n{p.stderr.strip()[-1500:]}")

    return {"n": n, "path": out, "D": D, "cues": cues, "mode": r["mode"],
            "tempo": tempo, "freeze": freeze}


# --------------------------------------------------------------------------- #
# Pass 2 —— 一致性闸门 + 拼接
# --------------------------------------------------------------------------- #
SIG_V = ("width", "height", "sample_aspect_ratio", "pix_fmt", "r_frame_rate",
         "codec_name", "profile", "time_base")
SIG_A = ("codec_name", "sample_rate", "channels", "channel_layout")


def signature(path: Path) -> tuple:
    js = ffprobe_json(path)
    v = next((s for s in js["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in js["streams"] if s["codec_type"] == "audio"), {})
    return (tuple(str(v.get(k)) for k in SIG_V), tuple(str(a.get(k)) for k in SIG_A))


def concat(parts: list[Path], out: Path, workdir: Path) -> None:
    """concat demuxer + -c copy。参数不一致时它不报错,只会逐块累积漂移 ——
    所以先做一道强制的签名闸门。"""
    sigs = {p: signature(p) for p in parts}
    base = sigs[parts[0]]
    bad = [p for p in parts if sigs[p] != base]
    if bad:
        msg = [f"归一化后的块流参数不一致,concat 会静默漂移。基准 {parts[0].name}:",
               f"  video {dict(zip(SIG_V, base[0]))}",
               f"  audio {dict(zip(SIG_A, base[1]))}"]
        for p in bad:
            msg.append(f"不一致 {p.name}:")
            msg.append(f"  video {dict(zip(SIG_V, sigs[p][0]))}")
            msg.append(f"  audio {dict(zip(SIG_A, sigs[p][1]))}")
        die("\n".join(msg), code=4)

    lst = workdir / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    p = run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)])
    if p.returncode != 0:
        die(f"拼接失败:\n{p.stderr.strip()[-1200:]}")


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None, help="默认 <manifest 同级>/final.mp4")
    ap.add_argument("--no-subs", action="store_true", help="不烧字幕")
    ap.add_argument("--no-upper", action="store_true", help="字幕不转大写")
    ap.add_argument("--font", default=None, help="字幕字体文件")
    ap.add_argument("--bed-gain", type=float, default=0.30,
                    help="clip 原生音在混音里的增益,0 = 完全静音("
                         "Veo 有时会自己加人声,那时用 0)")
    ap.add_argument("--duck-threshold", type=float, default=0.030,
                    help="旁白压低原生音的触发阈值")
    ap.add_argument("--crf", type=int, default=20)
    ap.add_argument("--preset", default="medium")
    ap.add_argument("--force", action="store_true", help="忽略幂等,全部重做")
    ap.add_argument("--dry-run", action="store_true", help="只打印 ffmpeg 命令")
    opts = ap.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        die("找不到 ffmpeg/ffprobe")

    mf = json.loads(opts.manifest.read_text(encoding="utf-8"))
    blocks = sorted(mf["blocks"], key=lambda b: b["n"])
    missing = [b["n"] for b in blocks if not b.get("clip")]
    if missing:
        die(f"manifest 里这些块还没回填 clip 路径: {missing}")

    run_dir = opts.manifest.parent
    out = opts.out or run_dir / "final.mp4"
    paths = {"norm": run_dir / "norm", "cues": run_dir / "cues"}
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

    # 字幕分层探测:有 libass 就用原生 subtitles 滤镜,没有就 Pillow overlay。
    filters = run(["ffmpeg", "-hide_banner", "-filters"], timeout=60).stdout
    use_libass = any(len(l.split()) > 2 and l.split()[1] == "subtitles"
                     for l in filters.splitlines() if l.startswith(" "))
    font = pick_font(opts.font)
    if not opts.no_subs:
        info(f"字幕: {'tier-1 libass' if use_libass else 'tier-2 Pillow overlay'}  字体 {font.name}")

    results = []
    for blk in blocks:
        results.append(normalize_block(blk, mf, paths, opts, font, use_libass))

    if opts.dry_run:
        return 0

    for r in results:
        tag = {"clip-wins": "画面为准", "atempo": f"旁白提速 {r['tempo']:.3f}×",
               "freeze": f"冻结尾帧 {r['freeze']:.2f}s"}[r["mode"]]
        print(f"  block{r['n']:02d}  {r['D']:5.2f}s  {tag}", file=sys.stderr)

    concat([r["path"] for r in results], out, run_dir)

    # 全局 SRT(旁挂给 YouTube 用)—— 纯文本偏移,不碰视频
    srt_lines, idx, base = [], 1, 0.0
    for r in results:
        for c in r["cues"]:
            srt_lines.append(f"{idx}\n{srt_ts(base + c['start'])} --> "
                             f"{srt_ts(base + c['end'])}\n{c['text']}\n")
            idx += 1
        base += r["D"]
    (out.with_suffix(".srt")).write_text("\n".join(srt_lines), encoding="utf-8")

    total = duration_of(out)
    expect = sum(r["D"] for r in results)
    print(f"\n{GREEN}✓{RESET} {out}", file=sys.stderr)
    print(f"  {len(results)} 块  实际 {total:.2f}s / 预期 {expect:.2f}s"
          f"  {mf['width']}×{mf['height']}", file=sys.stderr)
    print(f"  字幕旁挂: {out.with_suffix('.srt')}", file=sys.stderr)
    if abs(total - expect) > 0.25:
        print(f"{YELLOW}  ⚠ 实际时长与预期差 {abs(total-expect):.2f}s — "
              f"检查是否有块的流参数不一致{RESET}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
