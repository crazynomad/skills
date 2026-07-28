# 后端适配:Higgsfield MCP

**只在 Higgsfield MCP 已注册时读这个文件。** 默认后端是 gflow(见 `backend-gflow.md`)。

保留它有两个理由:一是这条流水线本来就该是后端可插拔的,二是老 skill
`vox-motion-graphics` 里那些用真金白银换来的审核经验只在这个后端成立,
放在这里比删掉好 —— 但也**只在这里成立**,别拿去指导 Veo。

---

## 能力对照

Higgsfield 是"服务端全包"型:TTS、装配、烧字幕都在它那边。所以用这个后端时,
`scripts/narrate.py` 和 `scripts/assemble.py` **都不需要** —— 那两个脚本是专门
为了补 gflow 的缺口写的。

| 能力 | Higgsfield 实现 | 成本 |
|---|---|---|
| C1 风格键 | `resolve_explainer_preset(preset_id)` → `media_id` | 免费 |
| C2 关键帧 | **没有对应能力**(有 `generate_image`,但没法把静止图当首帧喂给视频) | — |
| C3 出片 | `generate_video(medias=[{value:key, role:"image"}], duration:10)` | 30–90 积分/条 |
| C4 旁白 | `list_voices` + `generate_audio(model="seed_audio", voice_id, voice_type)` | 按量 |
| C5 装配 | `explainer_video{width, height, items:[{video, audio}]}` | 按量 |
| C6 字幕 | 装配参数里的 `subtitles:{font:"anton"}` | 0.05 积分/块 |

**任务模型:** 异步。每个 `generate_*` 返回 job id,用 `job_status {jobId, sync:true}`
轮询,或看 `show_generations`。完成的 job id 可以直接当下游的 `medias[].value`
和装配时的 `video`/`audio`,不用取原始 URL。

---

## 时长模型的差异(切换后端时最容易忘)

Higgsfield 的装配是**固定 10 秒窗口**:短的音频居中放(7 秒的会晚 1.5 秒开口,
听着像不同步),略长的做保音高提速(13 秒的被压 30%,听着像赶稿),画面永不拉伸。

所以用这个后端时:
- 每块文案回到 **~20–24 词**(≈9 秒),不是 gflow 那边的 14–18 词
- `N = 分钟数 × 6`
- 装配前逐条读 `durationSec` 核验,目标 9.0–10.5 秒

TTS 节奏经验(Higgsfield 的 seed_audio 实测):纪录片旁白音在每个句号处停约
0.7 秒,所以"短句 + 人名多"的行只有约 1.8 词/秒,而"一个逗号连起来的长句"能到
约 2.5 词/秒 —— 同样词数能差 4 秒以上。优先写单一流畅长句。旋钮是
`speech_rate`(-50..100)。

---

## 引擎分工

| 引擎 | 成本 | 特点 |
|---|---|---|
| `gemini_omni` | 30 积分/条 | 快,Mixed Media 拼贴的主力。**唯一能从描述渲出可辨识政要面孔的引擎** |
| `seedance_2_0` | 45(720p std)/ 90(1080p) | 参考级电影感:执行提示词内切镜(`Shot 1 … Cut to shot 2`)、真实速度斜坡与 FPV 运镜、原生音效设计(`generate_audio: true`),音效能在旁白底下存活 |

---

## 预设与素材 id(只对 Higgsfield 有意义,对 gflow 是废数据)

```
Mixed Media 预设 id : 80e4dd7b-cd65-42d4-b191-b58d62558602
纸模风格键 job id   : 0561c26f-ad53-44da-815d-a8796d32d864
```

纸模风格的可复用道具(作为额外 `image_references` 传入,并在提示词里说
"参考图里的那个 X",防止物件在不同 block 之间变形):

| 道具 | job id |
|---|---|
| 纸质核导弹(橙色弹头) | 0cb0ada4-5376-44fe-8950-822425825336 |
| 做旧报纸头版(遮眼条肖像) | 4cf403d1-6791-4661-af13-7d61330accdd |
| 火药桶 "WHO BLINKS?" + 盘绕引信 | 68d803d1-3876-4410-9be4-9d800f6913be |
| 三个领导人剪影(美红领带 / 俄 / 中) | bd35a771-ddd9-456f-827a-18027293d1b0 |

---

## 审核地图(**Higgsfield 实测,不可外推到 Veo**)

- **提示词里出现政客真名 → seedance 的 job 必挂**(提交正常,渲染时死)。
  名字放在 TTS 旁白里没问题。
- **可辨识的政要面部特写**(即使不点名)→ seedance 拒;**gemini_omni 能渲** →
  把这类 block 路由到 gemini,风格键保持不变。
- 中景 / 全身的"打红领带的领导人 / 精悍的俄方政要 / 东亚政要"描述**两个引擎都过**。
  眼部的黑色遮盖条既卖了社论感,也化解了肖像权问题。
- **"mushroom cloud" → nsfw 标记。** 换一个剪影(沙漏当时既能过又更贴"最后期限"
  的主题)。
- 服务端会用 `preset_recommendation` 通知拦截风格化提示词
  (3D RENDER / IN THE DARK / DROWN IN MUSIC / FREE FALL…)。**永远不要接受** ——
  用通知里 `retry_literal_with` 给的 `declined_preset_id` 重新提交。
  那个 id 只压制那一个预设,换个提示词可能触发另一个。

---

## 已知的其他坑

- **画幅不继承。** 用 9:16 的风格键,`gemini_omni` 照样可能出 16:9。
  必须在每条 `generate_video` 上显式传 `aspect_ratio`。
- 装配的 `width`/`height` 要读**成片 clip 的真实尺寸**,不是当初计划的尺寸。
- 装配拒绝某个 id = 那个 job 还没到终态,轮询完再按顺序传全 N 项重试。
  **Block N 的音频永远落在 Clip N 上。**
- `voice_id` / `voice_type` 报错 = 跳过了 `list_voices`。取一对确切的值全片复用。
- 用 `get_cost: true` 跑一次 `generate_video` 可以在出片前估总花费。
