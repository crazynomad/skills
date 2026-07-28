# 旁白(C4)

gflow 一点 TTS 能力都没有 —— Veo 的原生音只存在于片内,既不能外供也不能导出。
所以旁白必须由 skill 自己补上。

**默认:本地 vox(Qwen3-TTS on MLX)。想要更好的纪录片男声时切 ElevenLabs。**

---

## 时长纪律:为什么旁白必须先做

这条流水线是**音频驱动**的:先出旁白 → 量真实秒数 → 再决定每块视频生成几秒。

反过来(先出片再配音)就会退回固定窗口的老毛病:短的音频要么居中放(晚开口,
听着不同步)要么补静音,长的要么被提速(听着赶)要么装不下。**先量后生成,
这两个问题都不存在。**

`scripts/narrate.py` 就是这个顺序的实现。它做四件事:合成 → 响度归一 →
`ffprobe` 量归一后的文件 → 选桶。

**量的必须是归一化之后的文件。** loudnorm 会把时长改动几十毫秒,
"先量原始 wav → 选桶 → 再归一"会让选桶依据失效。

---

## 桶位:{4, 6, 8},没有 10

`gflow video i2v --duration` 只接受 4/6/8。10 秒是 omni-flash 独有,而
omni-flash 在 i2v 下会静默丢弃首帧(gflow issue #125),所以走关键帧路线时
10 秒不可用。

```
bucket = 最小的 b ∈ {4,6,8} 满足 b ≥ 旁白秒数 + 0.25
```

那 0.25 秒是尾部呼吸,防止相邻两块的旁白撞在一起。

**装不下(旁白 > 7.75s)→ `narrate.py` exit 3,必须改写文案。** 不要试图靠
装配阶段的提速救 —— 提速上限是 1.12×,再快纪录片男声就听得出来。

### vox 的时长不可复现 —— 写文案要留余量

**同一句话跑两次,时长能差 1.5 秒以上**(实测:一句 13 词的行在三次运行里分别是
7.20s / 8.64s / 5.76s)。所以:

- **目标写到 ≤6.5 秒,不要卡在 7.75 秒的天花板上。** 卡着写的块今天过、明天可能
  就超,而超了就要重写重配。
- 句号很贵:纪录片音色在每个句号处停约 0.7 秒。**一个逗号连起来的长句比两个短句
  快得多** —— 同样词数,单句流畅版能比断句版短 1-2 秒。
- 一块超长时,先看看是不是能把句号改成逗号,再考虑删词。

配套的实现细节:`narrate.py` 的幂等判据是**每一块文案的 SHA**,不是 `blocks.json`
的 mtime。用 mtime 的话,改任何一句都会让全部块重新合成 —— 而时长是随机的,于是
每块的桶位重新掷骰子,改一处引发连锁超长,变成打地鼠(这个坑实测踩过)。

### 选桶要往上偏

每条 clip 无论 4 秒还是 8 秒**都是 1 积分**。所以:

- 一块只需要 4 秒 → 考虑和相邻块**合并**。切点越密越贵(积分按条算)也越碎。
- 宁可写满 8 秒,也别写出一堆 4 秒的碎块。
- `narrate.py` 选到 4 秒时会主动提示这一点。

对应的文案公式:**每块 14–18 词,目标 ≤7.5 秒**。
(老 Higgsfield 流程是 20–24 词 / 10 秒窗口 —— 迁移时这是必须自觉执行的
创作层改动,不是管道细节。)

---

## 路线 A:vox(默认,免费,离线)

```bash
uv run --script "$SKILL_DIR/scripts/narrate.py" \
    --blocks blocks.json --run <run> --voice vivian --model large
```

`blocks.json`:
```json
{"aspect": "9:16",
 "blocks": [{"n": 1, "text": "…"}, {"n": 2, "text": "…"}]}
```

产物:`<run>/vo/blockNN.wav`(原始)、`blockNN.norm.wav`(归一,-16 LUFS/48k/立体声)、
`blockNN.srt`(词级 cue)、`<run>/manifest.json`。

### 已知性质与坑

| 事项 | 说明 |
|---|---|
| 逐条 `vox speak -n blockNN`,不用 `vox batch` | batch 没有 `--name`,块号与文件的对应要靠输出顺序猜 —— 猜错就是**静默的音画错位**,是最贵的一类 bug。用 `-n` 命名是确定性的 |
| 模型加载很慢 | 每次调用都要重载模型。想省这个开销,先在另一个终端跑 `vox serve`(常驻缓存) |
| 模型缓存 | `~/.cache/huggingface/hub/models--mlx-community--Qwen3-TTS-*`。`large`(1.7B)约 2.9G。**没缓存的规格会去下载,可能卡很久** —— 首次用某个规格前先单独跑一次确认 |
| 音色 | `vox voices` 列出;默认 `vivian`。纪录片旁白优先挑低沉、平稳的 |
| 语速 | `-s`(播放速率倍率),比 Higgsfield 的 `speech_rate` 粗糙。优先改文案而不是拧语速 |
| 输出格式 | `pcm_s16le / 24000 Hz / mono` —— 和 Veo 的 `aac / 48000 / stereo` 不一致,`assemble.py` 里两条腿都会先 `aformat` 对齐,这一步不能省(否则 `sidechaincompress` 报错或静默失常) |
| 字幕 | `--subtitle srt` 顺带产出 cue。`vox align` 还能做词级强制对齐,需要更精细的字幕时用 |

---

## 路线 B:ElevenLabs(音色更好,按量计费)

ElevenLabs 是 **MCP 工具**,`narrate.py` 调不到它(同 `SKILL.md` 里 D1 的道理:
脚本在 shell 里,MCP 工具在 agent 的工具命名空间里)。所以分两步:

```
① agent 直接调 ElevenLabs MCP 的 text-to-speech,每块一次,同一个 voice_id,
   把结果存成  <run>/vo/blockNN.wav
② uv run --script scripts/narrate.py --blocks blocks.json --run <run> --measure-only
```

`--measure-only` 跳过合成,只做响度归一 + 测量 + 选桶 + 写 manifest。
**两条 TTS 路线因此共用同一套确定性的时长算术** —— 这也是为什么这个开关值得存在。

同一条片子里**绝不能换音色**。换音色 = 换叙述者。

---

## 改了文案之后

重跑 `narrate.py` 即可。它是幂等的(产物比 `blocks.json` 新就跳过),而且会
**保留 manifest 里已回填的 clip 路径** —— 那些是已经花过积分的产物,
"改一句文案重配音"不该把它们冲掉。

只有被改动的那一块会重新合成;它的 bucket 若因此变了,那一块的 clip 需要重出,
其余不动。
