---
name: generate-transcript
description: 本地把音频/视频文件或在线视频 URL 转录成文字稿(txt/srt/vtt/json)。基于 Apple Silicon 上的 mlx_whisper,支持中英文等多语言、自动语言检测、模型规格选择。当用户想要"转录""生成字幕/文稿/transcript""把这段音频/视频转成文字""提取台词""做 SRT 字幕",或给出一个音视频文件/YouTube 等链接要文字内容时使用。
user_invocable: true
---

# generate-transcript

在本机(Apple Silicon / MLX)把音频、视频或在线视频链接转录成文字稿。纯本地、免费、不上传。

这是 ASR(语音识别)这一步;**它不做翻译**。要"翻译成另一种语言"时,先用本 skill 转录,再由你(Claude)翻译文字,需要配音则交给 IndexTTS2(TTS)。

## 何时用

- "把这段音频/视频转成文字" / "生成字幕" / "做个 SRT"
- 给了一个本地 `.mp3/.wav/.m4a/.mp4/...` 文件要文稿
- 给了一个 YouTube/Bilibili 等链接,只要里面的话

## 怎么用

统一调用脚本(`$SKILL_DIR` 为本 skill 目录):

```bash
bash "$SKILL_DIR/scripts/transcribe.sh" <文件路径|URL> [model] [lang] [outdir]
```

参数:
- `model`:`tiny | small | medium | turbo | large-v3`,或完整 HF repo id。**默认 `turbo`**。
- `lang`:`zh | en | ja | ...` 或 `auto`(自动检测)。**默认 `auto`**。
- `outdir`:输出目录。默认 `./transcripts`。

产出:同名 `.txt / .srt / .vtt / .tsv / .json`(`--output-format all`)。

### 例子

```bash
# 本地文件, 自动语言, turbo
bash "$SKILL_DIR/scripts/transcribe.sh" talk.mp3

# 中文音频, 要最高精度
bash "$SKILL_DIR/scripts/transcribe.sh" 讲座.m4a large-v3 zh ./out

# YouTube 链接, 英文, 默认 turbo
bash "$SKILL_DIR/scripts/transcribe.sh" "https://youtu.be/RNF0FvRjGZk" turbo en
```

## 选哪个模型

| 短名 | 参数量 | 中文 | 速度 | 适用 |
|---|---|---|---|---|
| `tiny` | 39M | 弱(同音字/术语易错) | 最快 | 快速预览、英文清晰口播 |
| `small` | 244M | 尚可 | 快 | 一般英文 |
| `medium` | 769M | 好 | 中 | 较高要求 |
| `turbo`(默认) | 809M | 强,接近 large | 比 large 快 ~8× | **多数场景的最佳平衡** |
| `large-v3` | 1550M | 最好 | 慢 | 中文/嘈杂/术语密集、要最高精度 |

经验:**英文清晰口播** turbo 足够;**中文、嘈杂环境、专业术语**优先 `large-v3`。tiny 会把 three→free、embedding→bedding 这类近音听错,中文错得更多。

## 注意事项(踩过的坑)

- **不要给 `--language auto`**:mlx_whisper 不接受字面 `auto`;要自动检测就**不传** `--language`。脚本已处理(`lang=auto` 时省略该参数)。
- **`--output-format` 不接受逗号列表**:用 `all` 一次出全部格式,或多次调用。脚本用的是 `all`。
- 脚本会先用 ffmpeg 统一转 **16kHz 单声道 wav** 再喂给 whisper,规避各种容器/编码解码问题。
- 输出文件名取自输入名:脚本把中间 wav 命名为 `<原名>.wav`,所以产物就是 `<原名>.txt/.srt/...`。

## 模型存放位置

`tiny / small / medium / turbo` 都在 **HuggingFace 标准缓存** `~/.cache/huggingface/hub/`(`models--mlx-community--whisper-*`),首次用某规格自动下载、之后复用,无需任何配置,mlx_whisper 自动发现。

**`large-v3` 例外(Xet 坑)**:它的 `weights.npz`(~2.9GB)走 HF 的 **Xet 后端**,`huggingface_hub` 在受限网络下会卡死,直连 CDN 也频繁断流。所以本 skill **不**让 mlx_whisper 自己拉,而是:

- 首次请求 `large-v3` 且本地缺失时,自动调用 `scripts/fetch-large-v3.sh`,经 **hf-mirror.com 镜像 + `curl` 断点续传**稳健下载到本地目录,再以本地路径加载——这条绕坑路径已固化在脚本里,任何人 clone 后都能复现。
- 默认目录 `~/models/whisper-large-v3-mlx/`,用 **`WHISPER_LARGE_V3_DIR`** 覆盖;镜像用 **`HF_ENDPOINT`** 覆盖(默认 `https://hf-mirror.com`)。
- 也可手动预下载:`bash scripts/fetch-large-v3.sh [目标目录]`。

> 网络通畅、不需要镜像的用户,把 `WHISPER_LARGE_V3_DIR` 指向空目录后照样能下;或直接用 `turbo`(接近 large、快 ~8×),多数场景够用。

## 依赖

- `mlx_whisper`(`pip install mlx-whisper`)— Apple Silicon
- `ffmpeg`(`brew install ffmpeg`)
- `yt-dlp`(`pip install yt-dlp`)— 仅处理 URL 时需要
