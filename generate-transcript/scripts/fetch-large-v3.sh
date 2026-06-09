#!/usr/bin/env bash
# 稳健下载 whisper-large-v3-mlx 权重, 规避 HuggingFace Xet 后端在受限网络下的卡死/断流。
#
# 背景: mlx-community/whisper-large-v3-mlx 的 weights.npz(~2.9GB)走 Xet
# (cas-bridge.xethub.hf.co)。huggingface_hub 客户端会卡死 / LocalEntryNotFoundError,
# 直连 HF CDN 每 2-3MB 断流。实测可靠的办法: 从 hf-mirror.com 用 curl 断点续传直拉。
#
# 用法:  fetch-large-v3.sh [目标目录]
#   目标目录默认 $HOME/models/whisper-large-v3-mlx (与 transcribe.sh 默认一致)。
#   镜像可用 HF_ENDPOINT 覆盖 (默认 https://hf-mirror.com)。
set -euo pipefail

DEST="${1:-$HOME/models/whisper-large-v3-mlx}"
REPO="mlx-community/whisper-large-v3-mlx"
ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
BASE="$ENDPOINT/$REPO/resolve/main"

command -v curl >/dev/null || { echo "缺少 curl" >&2; exit 1; }
mkdir -p "$DEST"

echo ">> 下载 $REPO → $DEST (源: $ENDPOINT)" >&2
for f in config.json weights.npz; do
  # -C - 断点续传; 已完整的文件 curl 会立即返回。失败自动重试。
  echo ">> $f ..." >&2
  curl -L -C - --retry 50 --retry-all-errors --retry-delay 2 --fail \
    -o "$DEST/$f" "$BASE/$f"
done

# 粗校验: weights.npz 应为数 GB; 太小说明拿到的是错误页而非权重。
SZ=$(wc -c < "$DEST/weights.npz" | tr -d ' ')
if [ "$SZ" -lt 1000000000 ]; then
  echo "!! weights.npz 仅 $SZ 字节, 不像完整权重 — 请删除后重试。" >&2
  exit 1
fi
echo ">> 完成: weights.npz = $SZ 字节" >&2
