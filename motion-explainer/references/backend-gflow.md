# 后端适配:gflow(Google Flow · Veo 3.1 / Nano Banana)

默认后端。**走 CLI(shell out 到 `gflow`),MCP 是可选备选。**

**一句话心智模型:图像免费、视频 1 积分。** 所有的策略都由这一条推出来 ——
把风格判断、构图判断、道具一致性统统压到免费的图像阶段解决,
视频阶段只负责"让这张已经确认过的图动起来"。

---

## 为什么是 CLI 而不是 MCP

| | CLI | MCP |
|---|---|---|
| **信用取证** | **完整 stderr → `generate_captured` 判据,能判断积分扣没扣** | 失败只返回 `{status, task_id, error}`,**判断不了钱花没花** |
| 限流 | 无 | 令牌桶:容量 8,20 秒补 1,图像视频共用。一次 6 块要 13 次调用,第 9 次起撞限流 |
| 超时 | 不涉及 | 受 MCP 客户端超时管;没抬到 ≥300s 就是**扣完积分才失败** |
| `--ui-mode` | 图像命令有 | 图像工具有,**视频工具没有** |
| 独有能力 | `image batch` · `video chain` · `scene create` · `upscale` · `--dry-run` · `--resume-from` | — |
| 结构化输出 | `--json` | 原生 |

MCP 唯一的好处是调用形态干净,但 `--json` 也给结构化输出。**所以默认走 CLI。**

MCP 仍然可用(见文末),适合"只想快速出一张图"这类一次性场景。

---

## 能力对照(创作层只依赖这些)

| 能力 | gflow 实现 | 成本 | 阻塞时长 |
|---|---|---|---|
| C1 风格键 | `gflow image t2i` + `--model nano-pro` | 免费 | ~40-90s |
| C2 关键帧 | `gflow image i2i --ref <风格键>` | 免费 | ~40-90s |
| C3 出片 | `scripts/veo-gen -- i2v --initial-frame <关键帧>` | **1 积分** | ~120s |
| C4 旁白 | **后端没有** → `scripts/narrate.py`(vox)或 ElevenLabs MCP | 免费/按量 | 视模型 |
| C5 装配 | **后端没有** → `scripts/assemble.py` | 免费 | 秒级 |
| C6 字幕 | **后端没有** → `assemble.py` 内的 Pillow overlay | 免费 | 秒级 |
| C7 失败分类 | `veo-gen` 内建 + 下面的规则 | — | — |

`gflow scene create` 能做免费的服务端拼接,但**混不了外部音轨**,对本流程无用。
只在想要一条无旁白的快速预览时才用得上。

---

## 主路线:免费关键帧 → i2v

### ① 风格键(整片一次,免费)

```bash
gflow image t2i "<style-*.md 里的 STYLE KEY 提示词>" \
  --model nano-pro --aspect 9:16 -n 1 \
  --out <run>/style --project-name "<片名>" \
  --ui-mode classic --json
```

从 `--json` 结果里取两样都要存下:
- `images[0].local_path` —— 本地路径,后面 `--ref` 用。**扩展名是 `.jpg` 不是 `.png`**
  (Flow 的 CDN 按实际字节返回,gflow 会据此改扩展名)—— 别硬编码后缀,读返回值
- `project_id` —— 后续所有生成都传 `--project <这个 id>`,让素材留在同一个 Flow
  项目里(媒体库不碎片化,而且项目内的 media UUID 可以直接当 `--ref` 复用,不必重传)

### ② 每块的关键帧(每块一次,免费 —— 跑偏就重来,不心疼)

```bash
gflow image i2i "<Block N 的 SCENE 描述,写成一张静止画面>" \
  --ref <run>/style/<风格键>.png \
  --ref <道具1>.png --ref <道具2>.png \
  --model nano-pro --aspect 9:16 \
  --out <run>/keyframes --project <project_id> \
  --ui-mode classic --json
```

`--ref` 接本地路径**或**项目内的 media UUID,两者都行。可以多次传。

**看一眼再往下走。** 风格对不对、构图对不对,在这里判定 —— 这一步免费。

### ③ 出片(每块一次,1 积分)

**永远通过 `veo-gen`,不要裸调 `gflow video`:**

```bash
VEO_GEN_LOG=<run>/veo-gen-attempts.log \
"$SKILL_DIR/scripts/veo-gen" --final <run>/clips/block03.mp4 -- \
  i2v --initial-frame <run>/keyframes/block03.png \
      --model veo-lite --duration 8 --aspect 9:16 \
      --out-dir <run>/clips --project <project_id> \
      "<Block 3 的 MOTION + 音效描述>"
```

`veo-gen` 自带:`GFLOW_CLI_UI_MODE=classic`、白名单式重试(只重试明确的提交前
瞬时错误)、`generate_captured` 信用取证、指数退避、`--final` 重命名。
它最后一行打印产物的最终路径。

**为什么值得多关键帧这一步:** 首帧就是你确认过的那张图,t=0 时刻风格漂移物理上
不可能;而且付费前多了一道零成本的闸门。相比之下"把风格参考图挂到视频生成上"
是语义软约束,模型可以不听 —— 老 Higgsfield 流程里"渲成写实"的失败一次就是
30–90 积分。

**道具一致性的做法:** 不要把道具塞进视频侧的参考图(veo-lite 上限 3 张)。
把道具作为 `--ref` 烘进**免费的关键帧**里 —— 图像侧上限 10 张,而且免费,
等于绕开了视频侧的参考图预算。

---

## 模型 / 时长 / 参考图上限矩阵

**视频**

| 模型 | 最长 | r2v 参考图上限 | 备注 |
|---|---|---|---|
| `veo-lite` | 8s | 3 | **i2v 默认且推荐**,显式传,别省略 |
| `veo-fast` | 8s | 3 | |
| `veo-quality` | 8s | **0(不支持 r2v)** | |
| `veo-lite-lp` | 8s | 3 | 低优先级队列 |
| `omni-flash` | **10s** | 7 | **i2v 下会静默丢弃首帧**(issue #125),只用于 t2v/r2v |

- `--duration` 只接受 `4 / 6 / 8`(i2v);`10` 是 omni-flash 独有。
- `--aspect` 只接受 `9:16` / `16:9`。**没有 1:1**。
- 省略 `--model` = 用 Flow UI 当前默认,那是个移动靶 → 永远显式传。

**图像**

| 别名 | 是什么 | i2i 参考图上限 |
|---|---|---|
| `nano-pro` | Nano Banana Pro | 10 |
| `nano2` | Nano Banana 2(默认) | 10 |
| `image4` / `imagen4` | Imagen 4 | 3 |

生成时**没有分辨率参数**;要更高清只能事后
`gflow image upscale <media_id> --scale 2k|4k --project <id>`(4k 需 Ultra;
`upscale` 不支持 `--json`)。

---

## 提速与并发

- **关键帧可以批量提交:** `gflow image batch <manifest.tsv> --model nano-pro`
  一次最多 5 条,共享一个 Flow 项目,自带提交抖动。TSV 每行
  `prompt\tcount\taspect_ratio\tmodel`。比逐条 `i2i` 快不少。
  (注意 `batch` 走的是 t2i 语义,要挂参考图仍需逐条 `i2i`。)
- **同一个 profile 不能并发。** 第二个调用立刻 `ProfileLockedError`(exit 11),
  不排队。本机只有一个 profile → **全流程严格串行**。
- **提交之间要留间隔 —— 这条会咬人。** Flow 的反爬会对密集连续提交发难:
  批量项之间 sleep **≥20 秒**。实测用 5 秒跑 9 张关键帧,第 4 张就吃到
  `RecaptchaError`,连带两张栽在网络抖动上,9 张只出了 6 张。
  `veo-gen` 的退避只覆盖单条内部的重试,**管不了条与条之间的节奏** ——
  批量脚本必须自己 sleep。
- **图像失败就退避重试。** 图像免费,没有理由不重试;`RecaptchaError` 和
  网络抖动都是瞬时的,隔 45 秒重来一次通常就过。视频则相反 —— 先按信用安全
  规则判断扣没扣分。
- 6 块的真实墙钟约 20 分钟(1min 风格键 + 3min 关键帧 + 12min 视频 + 2min 旁白 +
  1min 装配)。开跑前如实告诉用户,别说"几分钟"。

---

## 信用安全规则

**走 CLI 时这条判据直接可用**(这是选 CLI 的首要理由):

- gflow 的 stderr 里出现 `generate_captured` = 请求已被后端接受、模型已经跑过
  → **可能已扣积分 → 绝不自动重试**,停下报告。
- 没出现 = 提交前失败(HTTP 503 / UI 抖动 / 浏览器会话断)→ 模型没跑,
  **不扣积分,重试安全**。

`veo-gen` 已经实现了这条,连同白名单式重试:

```
TRANSIENT = WireFormatError | UnexpectedError | TransportTimeoutError |
            TransportError | WafRejectionError | FlowAgentUiError |
            FlowAppError | RateLimitError | NetworkError |
            BrowserSessionClosedError | BrowserEngineUnavailableError
```

这份名单要和 gflow 自己的 `errors.is_retryable` **保持一致**。实测踩过:
`FlowAppError`(exit 31)被 gflow 标为 retryable,但白名单里漏了它,于是一次
瞬时的 Flow 应用层抖动被当成终端错误直接放弃 —— 明明 `submitted=false`、
一分钱没扣。升级 gflow 后值得重新核对一遍这份名单。

**未知或空的错误类一律不重试** —— 避免在内容策略/参数错误上反复空烧。
认证类失败只兜一次(赌 SSO 静默重铸 session),第二次仍失败就必须人工重登。

成功判据是 **gflow 自身的退出码 0**,权威;`--json` 的结构化日志行里也带
`status` 键,只解析 JSON 会被日志行污染。

### 产物没取回来时:`recover-media.py`

**根因(实测,三次失败堆栈完全一致):**

```
APIRequestContext.get: Client network socket disconnected
before secure TLS connection was established
  → GET .../media.getMediaUrlRedirect?name=<media_id>
```

**是到 labs.google 的 TLS 握手被掐断,不是 gflow 的逻辑 bug。** gflow 不重试
这个错,直接抛成裸 `UnexpectedError` —— 一次网络抖动 = 一个积分打水漂。

同一条网络问题的其它面孔(在到 Google 链路不稳的环境里会反复出现):

| 现象 | 底层 |
|---|---|
| 下载崩溃、`local_path: null` | TLS socket disconnected |
| `gflow auth login` 报「Could not verify」但其实登录成功了 | ConnectError |
| `FlowAppError`(31)「Flow web app crashed before the editor rendered」 | 页面资源没加载完 |
| `vox` 拉 HF 模型无限期挂住 | 同一条链路(所以 `narrate.py` 强制 `HF_HUB_OFFLINE=1`)|

**真正的修法是重试那一发 GET** —— 它免费、幂等(只是换一个签名 URL 再取一遍
已经生成好的文件),没有任何理由不重试。`recover-media.py` 默认重试 6 次、
指数退避,这才是它存在的意义;「事后补救」只是副作用。

gflow 自己没有「下载已有 media」的命令:

- `gflow data media <id>` 只给元数据,没有地址
- `gflow scene create` 要 workflowId,而本地 `assets` 表那一列**是空的**
- `--har` 也救不了 —— 崩溃发生在**发起下载请求之前**,HAR 里只有静态资源
  (实测:248 条记录,零条视频请求;每次还白写 46MB。别开)

但下载本身是个确定性 URL(gflow 源码 `api/routes.py:49`):

```
https://labs.google/fx/api/trpc/media.getMediaUrlRedirect?name=<media_id>
```

它 302 到签名的 GCS 地址。用同一个 profile 的浏览器上下文发这个请求就能拿回来:

```bash
# 自动找出所有「成功但没落盘」的视频并取回
uv run --script "$SKILL_DIR/scripts/recover-media.py" --out <run>/clips --auto

# 或按 media_id 点名取,顺便命名归位
uv run --script "$SKILL_DIR/scripts/recover-media.py" --out <run>/clips \
    <media_id> --as block02.mp4
```

**出片循环应当自动调用它**:veo-gen 报「生成成功但没取回」时,
从 `veo-gen-attempts.log` 最后一行取 `media=<id>`(那一行 `submitted=true`),
**立即**恢复 —— veo-gen 已经退出,profile 是空闲的。
这样这个 bug 的代价从「1 积分打水漂」降到「多花几十秒」。

> 曾经误判:第一次内联恢复失败于 `ERR_CONNECTION_CLOSED`,我归咎于 profile
> 占用并改成「跑完再批量恢复」。**那是错的** —— 那次也是同一个网络抖动,只不过
> 打在了 `page.goto` 上。现在的实现干脆不做 `goto`(持久化上下文自带 cookie,
> `ctx.request` 直接可用),少一次会被打断的请求。

实测效果:5 次付费尝试原本只拿到 2 条 clip(50% 损耗),恢复后 5 条全在手,
**损耗率 0%**。

前置:恢复时不能有其它 gflow 进程占着 profile。太老的 media 会 404(链接过期)。

### 常见错误类的处置

| 错误 / exit | 处置 |
|---|---|
| **生成成功但产物没取回来** | 日志里有 `MEDIA_GENERATION_STATUS_SUCCESSFUL`,随后 `phase=video_generation` 抛裸 `Error`(exit 1)。**额度已扣,片子在 Flow 上是好的**。本机实测约 1/3 概率。→ **用 `scripts/recover-media.py` 取回,不要重跑**(见下) |
| `FlowAppError`(31) | Flow 应用层瞬时抖动,**gflow 标为 retryable**。提交前失败不扣分,直接重试 |
| `UiSelectorDriftError`(23) | 提交前,不扣分。先 `uv tool upgrade gflow-cli` |
| `FlowAgentUiError`(25) | 账号被灰度到 agentic UI。`veo-gen` 已强制 classic;仍报就重试(cohort 约 12h 翻转) |
| `ProfileLockedError`(11) | 有残留进程。`pgrep -f profile_greentrainpodcast` 后清掉 —— **用 `kill`(SIGTERM)不要 `kill -9`**。SIGKILL 会让 Chrome 来不及收尾,profile 被标记成 `exit_type: Crashed`,之后每次启动都弹 Restore pages? 气泡,而那个气泡会**盖住 Flow 的输入框**, 反过来制造 `UiSelectorDriftError`。真被 -9 过就关掉 Chrome、把 profile 的 `Default/Preferences` 里 `profile.exit_type` 改回 `Normal`(preflight 会检测这一项)。锁文件残留时按锁里记的 pid 判活再删 |
| `AuthExpired` | `gflow auth login --browser chrome`,登录后等 5 秒再 Cmd+Q 整个 Chrome |
| 内容策略 | **改提示词,不要重试**。若发生在提交后,积分已扣 |
| `MEDIA_GENERATION_STATUS_FAILED` | 提交后失败 → 已扣分。检查提示词/首帧,手动决定是否重跑 |

---

## Veo 与 Higgsfield 引擎的行为差异(迁移时最容易翻车的地方)

| | seedance/gemini_omni(Higgsfield) | Veo 3.1(gflow) |
|---|---|---|
| 提示词内切镜 `Shot 1 … Cut to shot 2` | 执行 | **不执行** —— 别写,写了也是一镜 |
| 假一镜(单一连续运镜 + 首尾运动模糊) | 有效 | **同样有效**,继续用 |
| 原生音效 | seedance 有 | **有,而且关不掉** —— 见下 |
| 可辨识政要面孔 | gemini_omni 能渲 | **更严格,未系统实测** |
| 审核边界 | 有实测地图(见 backend-higgsfield.md) | **完全未测,必须靠真实运行重建** |

**原生音是硬门禁,不是风格建议。** Veo 会自发在片内生成人声(人群嘈杂、旁白腔)。
ducking 只能把竞争人声压低,消不掉它,而且你付完钱才发现。所以:

- 每条视频提示词末尾必带:`No speech, no dialogue, no singing, no voiceover.`
- 万一还是混进人声:`assemble.py --bed-gain 0` 把原生音整条静音。

---

## 一次完整运行的顺序

```
0. uv run --script scripts/preflight.py --probe-auth      # GO/NO-GO
1. 写脚本(见 SKILL.md 的文案公式,每块 14–18 词)→ blocks.json
2. uv run --script scripts/narrate.py --blocks blocks.json --run <run> --voice <音色>
   → 每块的真实秒数与 bucket。有块超长会 exit 3,改文案重跑。
3. gflow image t2i  → 风格键(免费),记下 local_path 与 project_id
4. gflow image i2i  → 每块关键帧(免费,逐张过目)
5. veo-gen -- i2v   → 每块出片(1 积分/条,串行,每条约 2 分钟)
                      clip 路径回填进 manifest.json
6. uv run --script scripts/assemble.py --manifest <run>/manifest.json
7. 交付 final.mp4 + final.srt + 脚本全文 + Sources
```

中途死了直接重跑:每个阶段都是幂等的(产物比输入新就跳过),`--force` 强制重做。
**这不是加分项 —— Flow 会话会在几十小时空闲后过期,20 分钟的串行流程有真实概率
死在第 4 块。**

---

## 附:MCP 路线(可选)

已注册 `gflow` MCP server 时可用。适合一次性快速出图;**不建议用它跑完整流水线**
(理由见开头的对照表)。

```
gflow_generate_image(prompt, model="nano-pro", aspect, count, seed,
                     reference_images=[路径或 UUID], profile, project,
                     project_name, instructions, ui_mode)

gflow_generate_video(prompt, mode="t2v"|"i2v"|"r2v", aspect,
                     initial_frame, end_frame, reference_images,
                     model, duration, count, profile, project, project_name)
```

两个都同步阻塞到生成完成,返回
`{status, task_id, flow_project_id, flow_media_id, flow_workflow_id, files:[本地路径], params}`。
没有查询工具,`task_id` 只是给日志看的。

用 MCP 时必须注意的三件事:

1. 注册的 `env` 里要有 `GFLOW_CLI_UI_MODE=classic` —— `gflow_generate_video`
   **没有 `ui_mode` 参数**,agentic-UI 灰度 bug 只能在那里治。
2. MCP 客户端工具超时要 ≥300 秒,否则**每条 clip 都会在扣完积分之后超时失败**。
3. 令牌桶限流(容量 8 / 20 秒补 1)。撞到 `rate_limited` 就退回 CLI。

**MCP 失败时的信用判据**(因为看不到 `generate_captured`):
`gflow data list videos --limit 3 --json` 交叉核对 —— 有对应行 = 已扣分,
没有 = 提交前失败。**任何存疑的情况,直接改用 `veo-gen` 重跑那一块。**

注意:`gflow data list videos --json` 输出的是 **JSONL(每行一个对象)**,不是
JSON 数组 —— 整体 `json.load()` 会抛 `Extra data`。要逐行解析。
判断一条视频有没有真正落盘,看那行的 `local_path` 是不是 `null`。
