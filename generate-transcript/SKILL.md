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

转录结束后脚本会**自动跑验证门** `verify_transcript.py`(见下「验证产出」),抓到复读幻觉/漏转会以非 0 退出码报 FAIL。

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

经验:**绝大多数场景默认 `turbo`,中文也包括在内。** turbo 在长音频上稳。tiny 会把 three→free、embedding→bedding 这类近音听错,中文错得更多。

> ⚠️ **`large-v3` 有重复循环坍缩风险,不要无脑选它。** 实测一段 22 分钟中文播客,large-v3 在两段真实语音上退化成"同一句无限复读"(8:42→18:13 复读 569 次 + 18:42→22:43 复读 241 次),**62% 的字幕是幻觉**;同一段音频 turbo 完整正确转出。`large-v3` 只在 turbo 明显听错、且你**会跑验证门核对**时才用。模型越大 ≠ 转录越好。

## 验证产出(必做,别只看开头)

**这个 skill 最容易翻的车:whisper 在长段语音/静音/音乐上会退化成"同一句无限复读"的幻觉,或整段漏转。只扫开头几句一切正常,中间/结尾可能整段是垃圾。** 所以**转完必须验证,不能只采样开头就宣布完成**。

脚本已内置自动验证;也可手动对任意 SRT/JSON 跑:

```bash
python3 "$SKILL_DIR/scripts/verify_transcript.py" 转录.json --audio 原音频.wav [--reference 参考.srt]
```

三道门(全部来自 whisper 自己的 JSON 元数据,无需额外模型):
1. **覆盖率缺口** — 音频时长 vs 末条字幕结束时间。缺口大 ⇒ 漏转/被错误截断。
2. **重复循环** — 连续相同文本 ≥4 条,或某句占比 >4% ⇒ 复读幻觉(报出时间区间)。
3. **低置信聚集** — `compression_ratio>2.4`(whisper 内置重复度指标)/ `avg_logprob` 过低 / `no_speech_prob` 过高。

退出码 `2`=FAIL。**FAIL 时绝不直接交付**:换 `turbo` 重跑、或先 ffmpeg 去头尾静音、或人工核对该段。有参考答案时加 `--reference` 比对覆盖时长。

> 教训:删/截字幕前,先确认那段到底有没有真实语音(对 ground-truth 或听原音),别把"我以为是静音/音乐"当依据 —— 复读幻觉常常正是发生在**真实语音**上。

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
