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
# 2. 登录(需真 Chrome;它另开一个专属 profile 的 Chrome 窗口)。⚠ 三步缺一不可(2026-07-24 定为标准 SOP):
gflow auth login --browser chrome        # macOS 必须 --browser chrome
#    a) 登到 Flow 编辑器(labs.google/fx/tools/flow 出现即 NextAuth session 已铸);
#    b) 【关键·防日抛】同一窗口再开 google.com 标签页确认已登录(通常 OAuth 后已自动带上;
#       若右上角无头像则登录一次)——把 SID/LSID 等【账号层长效 cookie】留在 profile 里。
#       原理:Flow 的 NextAuth session 服务端 ~24h 滚动、闲置即死;有 SID 层,session 死后
#       labs.google 的 OAuth 跳转会经 accounts.google.com 静默重铸,日抛→月抛(nlm 同款存父凭据思路);
#       veo-gen 已内置认证失效单次兜底重试。无 SID 层则每次闲置>1天都要人工重登。
#    c) 等 ≥5 秒再 Cmd+Q 整个退出该 Chrome(cookie 异步落盘,关快了丢)。
gflow auth status                         # 确认 cookies_present: True(⚠只查文件存在,非会话有效)
~/.claude/skills/flow-media/scripts/session-probe --verbose | grep google_sid   # 确认 google_sid_present: true
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
| `UiSelectorDriftError` / 连 classic 切换元件都找不到 | gflow-cli 版本过旧、Flow 前端已改版(PREFER_CLASSIC 也救不了)。发生在**提交前·不扣额度** | **先 `uv tool upgrade gflow-cli`** 再试(EP14:0.24.0→0.35.0 即通;镜像慢可 `--index https://pypi.tuna.tsinghua.edu.cn/simple`) |
| `WireFormatError` HTTP 503 | 后端瞬时(提交前) | 重试(不扣额度);veo-gen 自动 |
| `MEDIA_GENERATION_STATUS_FAILED` | 提交后失败(已扣额度) | **别重试**,查 prompt/帧/内容策略 |
| `AuthExpiredError` / 401 | 会话过期。⚠ `auth status` 的 `cookies_present: True` **只查 cookie 文件存在,不代表会话有效**——久未使用先跑一次便宜生图探活,别信 status | **先原样重跑一次**(profile 有 SID 层时首次 401 的访问往往已静默重铸好新 session;veo-gen 自动兜);二连败才 `gflow auth login --browser chrome`(按前置 SOP 三步含补 SID)。⚠ macOS 关窗≠退程序:登录完成后必须**整个退出**那个 gflow 专属 Chrome 实例(Cmd+Q 或 kill 其主进程),gflow 等的是浏览器进程退出才落盘 cookies |
| 连续快速提交反复 `UnexpectedError` | Flow 对连发节流(2026-07-17 实测:批量中不歇气的条目连撞 4 次,单发的全一次过) | **批量生成条目之间歇 ≥20s**;veo-gen 的退避只管单条内,不管条目间 pacing |
| profile 锁 / `SingletonLock` 类失败 | 残留 Chrome 进程占着 gflow profile(常见于 auth login 没退干净) | `pgrep -f profile_greentrainpodcast` 找到残留进程 kill 掉再跑 |
| `--json` 报 No such option | upscale 不支持 --json | upscale 命令去掉 --json |
| 「每日 401」排错 | **已定案(2026-07-21 实锤)**:服务端作废——token 创建 07-20 09:19/客户端有效期 30 天/探针 7 连报健在,闲置 ≈35h 后 401。模型=NextAuth 会话服务端 ~24h 滚动时效:**使用即续签、闲置即死**(所以像"日抛")。且 profile 全程无 google.com SID(`google_sid_present:false`)→ 会话死后无 SSO 可静默续签,只能交互登录。**改造已落地(2026-07-24,参考 nlm 存父凭据思路)**:登录 SOP 升级为三步(含补 google.com SID 层,见前置)+ veo-gen 认证失效单次兜底(首撞 401 的访问往往已被 SSO 静默重铸,重试即过)——SID 在则日抛→月抛,保活 cron 不再需要。⚠ 登录后别立刻 kill Chrome(cookie 异步落盘会丢),等 5s。⚠ 待长闲置(>36h)实测验证一轮后此案彻底关闭 | 查 `session-health.log` 时间线 |
| 0.40 `--project` 进已有项目崩溃 | 新 UI unhandled error / classic UiSelectorDrift(2026-07-20 实测,双路皆断) | 暂散建 scratch(台账注明例外),等上游;别 --adopt-latest 认领 scratch |

## 项目复用(通用机制 + 本地约定)

- `gflow image/video` 均支持 `--project <id>`:在既有 Flow 项目里生成,媒体库不碎片化,且 i2v 可用 in-project 素材 UUID 免重复上传。
- `scripts/veo-gen` 认环境变量 **`GFLOW_PROJECT`**(自动追加 --project;命令行已带则不覆盖)。
- **项目 id 从哪来是各仓库的本地约定,本 skill 不做仓库/集数探测**。例:绿皮火车 studio 仓库用 `tools/flow/ep-project.sh`(remote 校验→定位 epXX→读写集根 `.flow-project`;首次生成后 `--adopt-latest` 认领)。其他项目可自定义同类解析器。
- 首次链路:第 1 次生成不带 --project(Flow 自动建项目)→ 认领其 id → 后续全部带上。

## 成本护栏
- `--tool creative-director`(提示词扩写)走**付费 Gemini API**(需 `GFLOW_CLI_GEMINI_API_KEY`),不设不产生费用。想省钱自己写好 prompt。
- 每次 AI 生成后按项目规范记 prompt(如频道的 `asset/{type}-prompts.md`)。

## 备注
- 非官方工具,靠 Flow 登录态;Google 改版可能失灵,跟进 gflow-cli issues(尤其 #174 新 UI 适配)。
- `scripts/veo-gen` 是本 skill 内的可移植副本;若在某项目的 `tools/` 下另有一份,保持同步(逻辑一致)。
