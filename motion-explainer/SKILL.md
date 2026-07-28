---
name: motion-explainer
description: >
  端到端做一条带旁白、带字幕、已剪好的解说短片(motion-graphics explainer):
  选题/调研 → 事实核查过的脚本 → 锁定的风格键 → 逐块关键帧与动画 → 纪录片旁白
  → 一条成片 MP4。后端可插拔:默认走 gflow(Google Flow / Veo 3.1 / Nano Banana
  Pro,烧订阅额度而非计费 API),也支持 Higgsfield MCP。两种画风:Vox 式
  Mixed Media 编辑部拼贴,以及电影感纸模纪录片(做旧报纸微缩景观、遮眼条剪影、
  活字印刷道具)。当用户要"做个解说视频""motion graphics 解说""动画解说"
  "数据视频""Vox 风格的片子""纸模/报纸拼贴纪录片""用 Flow 做条视频"
  "跑一遍视频流水线",或者只说"做个关于 X 的视频"甚至没给题目(本 skill 会自己
  找热点)时使用。也用于地缘政治/金钱/权力题材的无人出镜旁白短片。
version: 1.0.0
---

# Motion Explainer(后端可插拔)

把一个题目 —— 或者什么都不给 —— 变成一条剪好的解说短片。

**默认后端 gflow。开工前读 `references/backend-gflow.md`。**

---

## 这条流水线的心智模型

一条片子被拆成 **N 个 block**。每块 = 一句旁白 + 一张关键帧 + 一条 clip。
三者的顺序是**音频驱动**的:

```
先出旁白 → 量真实秒数 → 决定这块视频生成几秒 → 出关键帧(免费) → 出片(1 积分)
```

反过来(先出片再配音)就会退回固定窗口的老毛病:短音频晚开口听着不同步,
长音频被提速听着赶。

**gflow 的经济学决定了一切策略:图像免费,视频 1 积分/条。**
所以把风格判断、构图判断、道具一致性统统压到免费的图像阶段解决,
视频阶段只负责"让这张已经确认过的图动起来"。

---

## 能力契约(创作层只依赖这 7 个名字)

| # | 能力 | gflow(默认,走 CLI) | Higgsfield(MCP) |
|---|---|---|---|
| C1 | 风格键 | `gflow image t2i --model nano-pro` · **免费** | `resolve_explainer_preset` · 免费 |
| C2 | 关键帧 | `gflow image i2i --ref <风格键>` · **免费** | **没有这个能力** |
| C3 | 出片 | `scripts/veo-gen -- i2v --initial-frame …` · **1 积分** | `generate_video` · 30–90 积分 |
| C4 | 旁白 | **后端没有** → `scripts/narrate.py`(vox)/ ElevenLabs MCP | `generate_audio` |
| C5 | 装配 | **后端没有** → `scripts/assemble.py` | `explainer_video` |
| C6 | 字幕 | **后端没有** → `assemble.py` 内 Pillow overlay | `subtitles:{font}` |
| C7 | 失败分类 | `generate_captured` 信用取证(veo-gen 内建) | job status / preset_recommendation |

接缝就在这张表里,**没有代码适配层**。三个脚本都不碰后端:`narrate.py` 只管
TTS、`assemble.py` 只管 ffmpeg、`veo-gen` 本身就是 CLI 包装器。
代码只用在三处确定性场景:ffmpeg 滤镜图、时长算术、已实战验证的重试逻辑。

**gflow 默认走 CLI 而不是 MCP**,首要理由是 **MCP 判断不了失败有没有扣积分** ——
`generate_captured` 只在 CLI 的 stderr 里。次要理由:CLI 没有令牌桶限流、
不受 MCP 客户端超时管、还独占 `image batch` / `video chain` / `scene create` /
`upscale` / `--dry-run`。MCP 仍可用于一次性快速出图,见 `backend-gflow.md` 文末。

后端选择:默认 gflow。只有 Higgsfield 注册了 → 读
`references/backend-higgsfield.md`,那时 C4/C5/C6 三个脚本都不需要。

---

## 运行方式

这个 skill 是**全权委托**型:选题、脚本、音色、素材、装配都自己定。

- 用户给了题目/角度/时长/音色 → 照办。没给的按下面的默认值自己定。
- **在第一次付费生成之前**,发一条计划消息:题目、角度、块数、音色、
  预估积分、**以及真实墙钟**(6 块约 20 分钟,串行)。发完**直接继续,不等审批**,
  除非用户明确要求先商量。
- 绝不因为一个有默认值的问题中途停下。**交付散片而非成片 MP4 = 失败。**

## 默认值

| 项 | 默认 | 什么时候改 |
|---|---|---|
| 后端 | gflow,**走 CLI**(`gflow image` + `scripts/veo-gen`) | 只注册了 Higgsfield;或临时只想出一张图 → 可用 gflow MCP |
| 画风 | Mixed Media 拼贴 | 题材是地缘政治/金钱/权力,或 brief 说"电影感" → 纸模 |
| 画幅 | 9:16 竖屏 | 用户说 YouTube/横屏 → 16:9 |
| 引擎 | `veo-lite` + `i2v` | 需要 10 秒或 >3 张参考图 → `omni-flash` + `r2v` |
| 块数 | 1 分钟 ≈ 8 块(每块 ~6-8 秒) | 用户给了长度 |
| 时长桶 | 4/6/8 秒,由旁白实测决定,**偏向 8** | — |
| 旁白 | 本地 vox,`vivian`,英文 | 要更好的男声 → ElevenLabs |
| 字幕 | 开,Anton(退 Arial Black) | 用户说不要 |
| 出镜 | 无人出镜 | 用户要主持人/吉祥物 |

---

## 故事引擎(banger 与明信片的区别)

一串好看但互不相干的画面 = 博物馆幻灯片。真正立得住的片子有这些:

- **贯穿物件。** 一个实体隐喻走完**每一块**并不断升级(横穿所有场景的燃烧引信、
  被打气逼近针尖的气球)。观众全程握着它,结尾兑现它。**写任何一块之前先定这个物件。**
- **问题钩子,最后才答。** 把问题印在道具上("WHO PAYS?"),旁白扣住答案直到收尾。
- **假一镜。** 每条 clip 写成一次连续运镜,首尾都在运动模糊里(俯冲/甩镜/耀斑/坠落)。
  块与块之间的硬切于是读作一镜到底 —— 并行生成,不需要帧对齐。
- **每约 3 秒一个冲击**(砸/盖章/冲击波/啪),每块至少一次速度斜坡。
  极端微距与全景交替,尺度反差拉满(巨脸 → 蚂蚁大的人 → 庞然道具)。
- **一个记忆点镜头。** 全片被记住的那一下(人群排成有意义的剪影;摇臂升起才看见的揭示)。

**注意:Veo 不执行提示词内的多镜切换**(`Shot 1 … Cut to shot 2`)。
假一镜仍然有效,继续用;多镜语法从老提示词库里删掉了。

---

## 文案公式

N 块,标 `Block 1 … Block N`,每块**14–18 词,目标 ≤7.5 秒**。
纯口语文本:没有舞台提示、没有括注,数字拼成单词("seventy percent"、
"twenty twenty-four")。

> 这个词数是从 i2v 的 8 秒上限倒推的。老 Higgsfield 流程是 20–24 词 / 10 秒窗口 ——
> 迁移时这是必须自觉执行的创作层改动,不是管道细节。

结构:

- **Block 1 冷开场。** 最反直觉的事实或问题,平铺直叙。不打招呼,不说"本期视频"。
- **Block 2 利害。** 为什么这事怪,或者为什么与观众有关。
- **中间块 证据。** 一块一个想法,每块锚在一个具体的数字/日期/地点/对比上。递进。
- **Block N−1 转折。** 反直觉的揭示,"但问题在于"。
- **Block N 收束 + 回扣。** 落下答案,最后一句重新定义开场那个事实。

语气:好奇、精确、略带一点冷幽默。短陈述句。**叙述者在解释,从不在煽动。**

每条 clip 的提示词末尾必带 `No speech, no dialogue, no singing, no voiceover.` ——
Veo 会自发生成人声,这是硬门禁不是风格建议(混进人声只能整条静音原生音,
而那时积分已经花了)。

---

## 流程

| 阶段 | 做什么 | 成本 |
|---|---|---|
| 0 preflight | `uv run --script "$SKILL_DIR/scripts/preflight.py" --probe-auth` | 免费 |
| T 选题 | 用户给了就用;没给就搜热点自己挑 | 免费 |
| R 调研 | 查证事实、数字、人名,留 Sources 清单 | 免费 |
| 2 脚本 | N 块旁白,上面的公式 → `blocks.json` | 免费 |
| 3 旁白 | `narrate.py` → 真实秒数 + 选桶 + `manifest.json` | 免费 |
| 4 风格键 | `gflow image t2i --model nano-pro`,记下 `local_path` + `project_id` | **免费** |
| 5 关键帧 | `gflow image i2i --ref <风格键>`,每块一次,**逐张过目**,跑偏就免费重来 | **免费** |
| 6 出片 | `veo-gen -- i2v --initial-frame <关键帧>`,回填 `clip` 到 manifest | **1 积分/条** |
| 7 装配 | `assemble.py` → final.mp4 + final.srt | 免费 |

具体调用见 `references/backend-gflow.md`。画风提示词见
`references/style-mixed-media.md` / `references/style-paper-diorama.md`。

```bash
SKILL_DIR=<本 SKILL.md 所在目录>；SCRIPTS="$SKILL_DIR/scripts"

uv run --script "$SCRIPTS/preflight.py" --probe-auth
uv run --script "$SCRIPTS/narrate.py" --blocks blocks.json --run <run> --voice vivian

gflow image t2i "<STYLE KEY>" --model nano-pro --aspect 9:16 \
  --out <run>/style --project-name "<片名>" --ui-mode classic --json
gflow image i2i "<Block N SCENE>" --ref <run>/style/<key>.png \
  --model nano-pro --aspect 9:16 --out <run>/keyframes \
  --project <project_id> --ui-mode classic --json
VEO_GEN_LOG=<run>/veo-gen-attempts.log "$SCRIPTS/veo-gen" \
  --final <run>/clips/block01.mp4 -- \
  i2v --initial-frame <run>/keyframes/block01.png \
      --model veo-lite --duration 8 --aspect 9:16 \
      --out-dir <run>/clips --project <project_id> "<Block 1 MOTION>"
# …clip 路径回填进 manifest.json…

uv run --script "$SCRIPTS/assemble.py" --manifest <run>/manifest.json
```

完整参数与陷阱见 `references/backend-gflow.md`。**出片永远通过 `veo-gen`,
不要裸调 `gflow video`** —— 那个包装器带着信用取证和白名单重试。

**每个阶段都是幂等的**(产物比输入新就跳过),中途死了直接重跑。
这不是加分项:单 profile 串行、20 分钟流程、Flow 会话会过期。

### 阶段 T — 选题

没给题目就找当下热的:搜 2–3 个角度(`trending topics this week <当前年月>`、
`most searched questions this week`,加一个用户关心的垂类)。

好题目的形状:核心是一个 **why/how 问句**、有**反直觉的数字或反转**、
**视觉潜力**强(地图、图表、物件、档案影像)、受众面广。
"为什么 X 突然到处都是"、"X 这么贵的真正原因"、"X 如何悄悄改变了 Y"。

避开:正在发生的悲剧与灾难、没有数据角度的纯明星八卦、任何找不到两个独立信源的东西。

自己挑最强的那个,在计划消息里说明(附一个备选供用户替换)。

### 阶段 R — 调研

**绝不凭记忆写稿。** 搜题目、抓 2–3 个最好的信源,收集:开场那个数字、
3–5 个具体事实/数字/日期、反直觉的转折、让画面具体起来的人/事/地。
每个数字**用第二个信源交叉验证**。留一份 Sources 清单放进最终交付。
不编引语、不编数字 —— **一句模糊的真话胜过一句具体的假话。**

---

## 交付

最终消息里给:成片、一句话说清题目与角度、脚本全文(方便复用)、Sources 清单。
然后**提议但不擅自执行** `youtube-seo`(如果片子要发 YouTube)。

---

## 常见错误

| 症状 | 原因 | 处置 |
|---|---|---|
| 视频生成在"新建 project"步 RuntimeError | 账号被灰度到 agentic UI | `veo-gen` 已强制 `GFLOW_CLI_UI_MODE=classic`;裸调 `gflow video` 才会撞上 |
| `UiSelectorDriftError` / exit 23 | Flow 改了 UI | 提交前失败,不扣分。`uv tool upgrade gflow-cli` |
| `narrate.py` 卡住不动 | vox 在等 HuggingFace 联网检查 | 已默认 `HF_HUB_OFFLINE=1`;模型没缓存就先 `vox speak "warm up" -m large -o /tmp` |
| clip 风格跑偏 | 关键帧那一步没过目就出片了 | 关键帧是**免费**的闸门,一定要看。跑偏就重出关键帧,别重出视频 |
| 视频 job failed 且没有错误文字 | 审核 | 见 `backend-gflow.md` 的信用安全规则。**先确认积分扣没扣再决定要不要重试** |
| 报「生成成功但没取回来」 | gflow 0.44 高频 bug,约 1/3 概率 | **别重跑**(积分已扣、片子是好的)→ `scripts/recover-media.py --auto` 取回 |
| `ProfileLockedError` / exit 11 | 同一个 profile 并发了,或有残留进程 | 本机只有一个 profile,全流程必须串行;`pgrep -f profile_greentrainpodcast` 清掉残留 |
| `narrate.py` exit 3 | 某块旁白超过 7.75 秒 | 改短那块文案重跑。别指望装配阶段救 |
| (用 MCP 时)每条视频调用都超时 | MCP 客户端工具超时 <300s | 见 `setup.md`。**注意是提交后失败,积分已扣**。这也是默认不用 MCP 的原因之一 |
| (用 MCP 时)返回 `rate_limited` | 令牌桶(容量 8,20s 补 1) | 退回 CLI |
| `assemble.py` exit 4 | 归一化后各块流参数不一致 | 看它打印的差异项;通常 `--force` 重做那块 |
| 原生音里有人在说话 | Veo 自发生成了人声 | `assemble.py --bed-gain 0`;下次提示词里加硬门禁 |
| 重跑 narrate 后 clip 没了 | (已修)会保留旧 manifest 里的 clip | 若仍发生,手工回填 |
| 用户要单独的素材 | — | 原始 clip 本来就没有旁白(旁白只存在于装配结果),本地抽帧抽轨即可得干净素材 |

---

## 文件清单

| 文件 | 用途 | 谁改 |
|---|---|---|
| `SKILL.md` | 故事引擎 + 文案公式 + 流程 + 能力契约。唯一必读 | — |
| `references/backend-gflow.md` | **默认后端。开工前读** | — |
| `references/backend-higgsfield.md` | 老后端;只在它注册了才读 | — |
| `references/style-mixed-media.md` | 拼贴画风的提示词库 | — |
| `references/style-paper-diorama.md` | 纸模画风的提示词库 + 道具工作流 | — |
| `references/narration.md` | TTS 两条路线、桶位规则、时长纪律 | — |
| `references/assembly.md` | manifest schema、ffmpeg 契约、字幕分层、故障对照 | — |
| `references/setup.md` | 一次性安装(gflow 登录、vox 模型预热、字体;MCP 是可选段) | 用户 |
| `scripts/preflight.py` | 只读能力探针,GO/NO-GO | — |
| `scripts/narrate.py` | 旁白 → 归一 → 测量 → 选桶 → manifest | — |
| `scripts/assemble.py` | manifest → final.mp4 + final.srt | — |
| `scripts/recover-media.py` | 把「已扣积分但没下载」的产物从 Flow 取回本地 | — |
| `scripts/veo-gen` | gflow CLI 兜底,带信用取证。**与 flow-media 的副本需同步** | — |
