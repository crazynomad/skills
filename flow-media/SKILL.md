---
name: flow-media
description: Generate images (Nano Banana Pro / Imagen) and videos (Veo 3.1) through Google Flow using the account's Ultra/Pro SUBSCRIPTION credits instead of the metered Gemini/Vertex API — no per-call API cost. Use when the user wants to create a thumbnail, cover, poster, b-roll clip, image, or short video with AI and wants to avoid API billing, or explicitly mentions Flow / gflow / Veo / Nano Banana via subscription. Wraps the gflow-cli tool; encodes this machine's Flow new-UI quirk (PREFER_CLASSIC) and credit-safe retry rules learned the hard way. NOT for the paid Gemini-API nano-banana-pro path (that costs money) — this is the subscription path.
version: 0.1.0
---

# flow-media — 用 Flow 订阅额度生图 + 生视频

用 `gflow-cli`(github.com/ffroliva/gflow-cli)驱动 Google Flow,吃 **Ultra/Pro 订阅额度**生成图片和视频,**不产生 Gemini/Vertex API 费用**。同一个 Nano Banana Pro / Veo 模型,从订阅入口进 = 免费(已付月费),从 API 进 = 按次计费。

## When to trigger

**Use when:**
- 要做 **封面/缩略图/海报/配图/b-roll/氛围短片**,且想省钱(走订阅额度而非付费 API)。
- 用户提到 Flow / gflow / Veo / Nano Banana(订阅版)/「用订阅额度生成」。
- 需要 **首尾帧补间**(i2v)或 **纯文生视频**(t2v)。

**Don't use when:**
- 用户明确要走 **付费 Gemini API**(那用 `nano-banana-pro` skill)。
- 只是要 HTML+截图的图表/版式图(非 AI 生成)。
- 要真实历史照片/真实数据/真实人物(诚信红线,用真档案)。

## ⚠️ 本机账号的两条硬规律(血泪换来,务必遵守)

1. **视频命令必须 `GFLOW_CLI_PREFER_CLASSIC=1`。** 若本机 Flow 账号被灰度到新版「全页媒体库 + AI 助手」UI(agentic cohort),裸调 `gflow video` 会在"新建 project"步 RuntimeError。加这个环境变量会退回经典 UI、正确命中首尾帧端点。**用 `scripts/veo-gen` 封装已内置,不用自己记。**(生**图**路径原生兼容新 UI,通常不需要,但加了也无害。)
2. **成功判据 = gflow 退出码 0**(权威),别只信 `--json` 解析——结构化日志行也带 `status` 键会污染解析。
3. **重试的额度安全线(关键):**
   - **提交前失败**(HTTP 503 / UI 抖动 / 浏览器会话断,日志**无** `generate_captured`):模型没跑,**不扣额度**,可自动重试。
   - **提交后失败**(日志有 `generate_captured` + `MEDIA_GENERATION_STATUS_FAILED`):模型已跑,**已扣额度**,**绝不自动重试**(否则空烧,曾一次烧掉 8 额度)。
   - `scripts/veo-gen` 已按此区分。裸调时务必自己守。

## 前置(一次性)

```bash
# 1. 安装(国内用清华镜像,直连 PyPI 的 40MB playwright wheel 会断)
UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" uv tool install gflow-cli
# 2. 登录(需真 Chrome;它另开一个专属 profile 的 Chrome 窗口,登到 Flow 编辑器后关那个窗口,gflow 自动验证落盘)
gflow auth login --browser chrome        # macOS 必须 --browser chrome
gflow auth status                         # 确认 cookies_present: True
```
> Chromium 引擎(`playwright install chromium`)在国内走 `PLAYWRIGHT_DOWNLOAD_HOST=https://cdn.npmmirror.com/binaries/playwright`;但 `--browser chrome` 用系统 Chrome,通常不需要 bundled Chromium。

## 生图(Image)

生图路径原生兼容新 UI,通常**第一次就成**。输出是 **`.jpg`**(不是 png),落在 `<out>/images/<YYYY-MM-DD>/<media>_<n>.jpg`(--out 会再套一层日期目录)。

```bash
# 文生图。模型:nano-pro=Nano Banana Pro(Gemini 3 Pro Image,推荐)/ nano2 / imagen4
gflow image t2i "你的英文 prompt" --model nano-pro --aspect 16:9 -n 1 --out ./out --json
# 参考图生图
gflow image i2i "prompt" --reference-image ref.png --model nano-pro --aspect 16:9 --out ./out
# 批量(多 prompt / 一次多图)
gflow image t2i --prompts-file prompts.txt --model nano-pro
gflow image t2i "variations" -n 4 --aspect 1:1
# 升分辨率(Ultra 才能 4k;返回 5504×3072 级别)。需 media_id + project
gflow image upscale <media_id> --scale 4k --project <project_id> --out ./out   # ⚠ upscale 不支持 --json
```
- aspect: `9:16`(默认竖屏)/ `16:9` / `1:1` / `4:3` / `3:4`。**YouTube 封面记得写 `16:9`**。
- 若拿不到本地文件:结果 JSON 的 `images[0].fife_url` 是 Flow CDN 签名直链,可 `curl` 下载。
- 撞 503(WireFormatError)= 后端瞬时,重跑即可(提交前,不扣额度)。

**封面/缩略图技巧(客观规律):** 大字少词、单一焦点、高对比、三分法、好奇缺口。中文标题可交给 Nano Banana Pro(渲染意外地准),但**只放一处关键中文**、其余用数字/拉丁字母,把翻车面收窄。

## 生视频(Video)—— 用 `scripts/veo-gen` 封装

**永远用 `scripts/veo-gen`,别裸调 `gflow video`**(封装内置 PREFER_CLASSIC + 提交前/后区分的安全重试 + 成功即停 + 自动重命名)。

```bash
# 首尾帧补间(i2v):接首/尾帧图 → 视频
scripts/veo-gen --final out/V01-final.mp4 -- \
  i2v --initial-frame V01-start.png --end-frame V01-end.png \
  --aspect 16:9 --model veo-lite --duration 4 --out-dir out "motion prompt"

# 纯文生视频(t2v):只给 prompt
scripts/veo-gen --final out/scene01.mp4 -- \
  t2v "英文 prompt" --aspect 16:9 --model veo-lite --duration 4 --out-dir out
```
- 模型:`veo-lite`(默认省)/`veo-fast`/`veo-quality`(Veo 3.1);`omni-flash` 仅 t2v、支持 10s(i2v 会丢帧,别用)。
- `--aspect` 默认 `9:16` 竖屏,**YouTube 写 `16:9`**;`--duration` 4/6/8(10 需 omni-flash);`--count` >1 按倍数扣额度。
- 输出 H.264 1280×720 带 Veo 原生音频。撞 503 会自动重试(不扣额度);连续 503 说明后端忙,稍后再来。

## Common errors

| 现象 | 含义 | 处理 |
|---|---|---|
| `RuntimeError` / new_project 不跳转 | 视频裸调撞新版 UI | 用 veo-gen(带 PREFER_CLASSIC) |
| `WireFormatError` HTTP 503 | 后端瞬时(提交前) | 重试(不扣额度);veo-gen 自动 |
| `MEDIA_GENERATION_STATUS_FAILED` | 提交后失败(已扣额度) | **别重试**,查 prompt/帧/内容策略 |
| `AuthExpiredError` / 401 | 会话过期 | 重跑 `gflow auth login --browser chrome` |
| `--json` 报 No such option | upscale 不支持 --json | upscale 命令去掉 --json |

## 成本护栏
- `--tool creative-director`(提示词扩写)走**付费 Gemini API**(需 `GFLOW_CLI_GEMINI_API_KEY`),不设不产生费用。想省钱自己写好 prompt。
- 每次 AI 生成后按项目规范记 prompt(如频道的 `asset/{type}-prompts.md`)。

## 备注
- 非官方工具,靠 Flow 登录态;Google 改版可能失灵,跟进 gflow-cli issues(尤其 #174 新 UI 适配)。
- `scripts/veo-gen` 是本 skill 内的可移植副本;若在某项目的 `tools/` 下另有一份,保持同步(逻辑一致)。
