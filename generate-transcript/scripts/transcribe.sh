#!/usr/bin/env bash
# generate-transcript: 本地把音频/视频/URL 转录成 txt/srt/vtt/json。
# 依赖: mlx_whisper (Apple Silicon), ffmpeg, yt-dlp(仅 URL 时需要)。
#
# 用法:
#   transcribe.sh <文件路径|URL> [model] [lang] [outdir]
#
#   model : tiny|small|medium|turbo|large-v3  或完整 HF repo id。默认 turbo。
#   lang  : zh|en|ja... 或 auto(自动检测)。默认 auto。
#   outdir: 输出目录。默认 ./transcripts。
#
# 例:
#   transcribe.sh talk.mp3                          # 自动语言, turbo
#   transcribe.sh talk.mp4 large-v3 zh              # 中文, 最高精度
#   transcribe.sh "https://youtu.be/XXXX" turbo en  # 下载后转录
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# large-v3 权重放哪 — 可用 WHISPER_LARGE_V3_DIR 覆盖。
LARGE_V3_DIR="${WHISPER_LARGE_V3_DIR:-$HOME/models/whisper-large-v3-mlx}"

INPUT="${1:?用法: transcribe.sh <文件路径|URL> [model] [lang] [outdir]}"
MODEL="${2:-turbo}"
LANG="${3:-auto}"
OUTDIR="${4:-./transcripts}"

# 短名 → 完整 mlx-community repo id
case "$MODEL" in
  tiny)              MODEL="mlx-community/whisper-tiny" ;;
  base)              MODEL="mlx-community/whisper-base-mlx" ;;
  small)             MODEL="mlx-community/whisper-small-mlx" ;;
  medium)            MODEL="mlx-community/whisper-medium-mlx" ;;
  turbo|large-v3-turbo) MODEL="mlx-community/whisper-large-v3-turbo" ;;
  large|large-v3)
    # large-v3 走 Xet 后端, huggingface_hub / HF CDN 在受限网络下会卡死/断流。
    # 故不交给 mlx_whisper 自己拉: 缺失时用 fetch-large-v3.sh 经 hf-mirror 稳健
    # 续传到 $LARGE_V3_DIR, 再以本地路径加载。可用 WHISPER_LARGE_V3_DIR 改位置。
    if [ ! -f "$LARGE_V3_DIR/weights.npz" ]; then
      echo ">> large-v3 未就绪, 经镜像稳健下载到 $LARGE_V3_DIR (规避 Xet)..." >&2
      "$SCRIPT_DIR/fetch-large-v3.sh" "$LARGE_V3_DIR"
    fi
    MODEL="$LARGE_V3_DIR"
    ;;
  *)                 : ;;  # 其它一律当作完整 repo id 直接用
esac

command -v mlx_whisper >/dev/null || { echo "缺少 mlx_whisper: pip install mlx-whisper" >&2; exit 1; }
command -v ffmpeg      >/dev/null || { echo "缺少 ffmpeg: brew install ffmpeg" >&2; exit 1; }

mkdir -p "$OUTDIR"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 1) 拿到媒体文件(URL 则先下载音频)
if [[ "$INPUT" =~ ^https?:// ]]; then
  command -v yt-dlp >/dev/null || { echo "缺少 yt-dlp: pip install yt-dlp" >&2; exit 1; }
  echo ">> 下载音频: $INPUT"
  yt-dlp -x --audio-format mp3 --no-playlist -o "$WORK/media.%(ext)s" "$INPUT" >&2
  SRC="$(ls "$WORK"/media.* | head -1)"
  BASE="$(yt-dlp --no-playlist --get-title "$INPUT" 2>/dev/null | head -1 | tr -cd '[:alnum:] ._-' | tr ' ' '_')"
  [ -z "$BASE" ] && BASE="transcript"
else
  [ -f "$INPUT" ] || { echo "文件不存在: $INPUT" >&2; exit 1; }
  SRC="$INPUT"
  BASE="$(basename "${INPUT%.*}")"
fi

# 2) 统一转 16kHz 单声道 wav(whisper 原生输入, 规避各种解码坑)。
#    用 BASE 命名, 这样 mlx_whisper 的输出文件名就是 BASE.{txt,srt,...}
WAV="$WORK/$BASE.wav"
echo ">> 预处理为 16kHz 单声道 wav"
ffmpeg -hide_banner -loglevel error -i "$SRC" -ar 16000 -ac 1 "$WAV" -y

# 3) 转录。lang=auto 时不传 --language(让 whisper 自动检测;不能传字面 'auto')
LANGARG=()
[ "$LANG" != "auto" ] && LANGARG=(--language "$LANG")
echo ">> 转录中 (model=$MODEL, lang=$LANG) ..."
mlx_whisper "$WAV" --model "$MODEL" "${LANGARG[@]}" \
  --output-dir "$OUTDIR" --output-format all

echo ">> 完成, 产物:"
ls -1 "$OUTDIR/$BASE".* 2>/dev/null | sed 's/^/   /'

# 4) 自动验证门 — whisper(尤其 large-v3) 会在长段语音上退化成"同句无限复读"的
#    幻觉, 或整段漏转, 只看开头根本发现不了。这里强制跑一遍 verify_transcript.py:
#    抓重复循环 / 覆盖率缺口 / 低置信聚集。FAIL 时退出码非 0, 提醒不要直接交付。
echo ">> 验证产出 (verify_transcript.py) ..."
if python3 "$SCRIPT_DIR/verify_transcript.py" "$OUTDIR/$BASE.json" --audio "$SRC"; then
  :
else
  echo ">> ⚠️ 验证未通过(见上面的 FAIL)。常见修法: 默认 turbo 比 large-v3 更不易循环;" >&2
  echo ">>    或先用 ffmpeg 去头尾静音/音乐再转。请勿在未核对该段前直接交付。" >&2
  exit 3
fi
