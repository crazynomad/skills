# 装配(C5 + C6)

gflow 既不能混外部音轨也不能烧字幕(`gflow scene create` 只是服务端拼视频)。
这两块由 `scripts/assemble.py` 用本地 ffmpeg 补上。

```bash
uv run --script "$SKILL_DIR/scripts/assemble.py" --manifest <run>/manifest.json
```

产物:`<run>/final.mp4`(烧好字幕、旁白盖在压低的原生音之上)+ `<run>/final.srt`
(旁挂,给 YouTube 用)。

---

## manifest.json

`narrate.py` 写出来,出片阶段回填 `clip`,`assemble.py` 消费。**这是各阶段之间
唯一的接口**,手改也可以。

```json
{
  "aspect": "9:16", "width": 720, "height": 1280, "fps": 24,
  "voice": "vivian", "tail_pad": 0.25,
  "blocks": [
    {
      "n": 1,
      "text": "Humans throw away enough food each day to feed two billion people.",
      "narration": "run/vo/block01.norm.wav",
      "narration_sec": 5.52,
      "srt": null,
      "cues": [{"start": 0.0, "end": 5.52, "text": "Humans throw away…"}],
      "bucket": 6,
      "clip": "run/clips/block01.mp4"
    }
  ]
}
```

`clip` 为 null 的块会让 `assemble.py` 直接报错退出 —— 免得拼出一条缺块的片子。

---

## 两遍走,以及为什么

**Pass 1:逐块归一化** → `<run>/norm/blockNN.mp4`,每块一次独立的 ffmpeg 调用。
**Pass 2:concat demuxer + `-c copy`** 把它们拼起来。

不用单个 N 输入的 `filter_complex` 一次拼完,理由有三:任意一条 Veo clip 的坏时基
会毒化整张图;内存随 N 增长;第 5 块失败要全量重来。

**`-c copy` 只在所有块的流参数完全一致时才安全。** 不一致时 concat demuxer
**不报错** —— 它会产生逐块累积的音画漂移,一条 6 块的片子到最后旁白能差出几帧。
所以 Pass 2 之前有一道强制的 `ffprobe` 签名闸门,比对
`width/height/SAR/pix_fmt/r_frame_rate/codec/profile/time_base` 与
`音频 codec/sample_rate/channels/layout`,任何一项不同就硬失败(exit 4)。

Pass 1 里保证一致性的关键几项:

```
scale=W:H:force_original_aspect_ratio=decrease, pad=W:H:…, setsar=1
fps=FPS, settb=1/15360          + 输出 -video_track_timescale 15360
-c:v libx264 -pix_fmt yuv420p -profile:v high -level 4.0 -g 2·FPS -sc_threshold 0
-c:a aac -ar 48000 -ac 2
```

`settb` 和 `-video_track_timescale` 都钉成 15360:Veo 的 clip 时基各式各样
(实测见过 1/15360 和 1/12800),不钉死就会出现"每块漂几毫秒、6 块之后旁白晚一帧"
这个经典 bug。

---

## 音频:旁白盖过被压低的原生音

Veo 的 clip 自带原生音效(风声、纸响、drone)。它有价值,但不能盖过旁白。做法:

```
原生音床 → volume=0.30 → sidechaincompress(以旁白为侧链) → amix
旁白     → adelay=120ms → apad → atrim=0:D ┘
```

**两条腿都必须先 `aformat=fltp:48000:stereo` + `aresample`。** vox 出的是
24kHz 单声道,Veo 出的是 48kHz 立体声 —— 不统一,`sidechaincompress` 要么报错
要么静默失常。这不是可选的优化。

其他几个不能省的细节:

| 参数 | 为什么 |
|---|---|
| `amix=…:normalize=0` | 默认的 normalize 会把两路各减半,旁白直接变小声 |
| `volume=0.30` 预衰减 | 这个构建没有 limiter,靠预衰减防削顶 |
| `adelay=120\|120` | 旁白从 t=0 开口会让第一个音素贴着切点被削掉 |
| `apad` + `atrim=0:D` + `-t D` | `apad` 不加界会无限跑下去;两处都设是有意的双保险 |

**实测的 ducking 深度约 6 dB**,旁白比压低后的音床高约 22 dB —— 纪录片混音的
健康区间。想调:`--duck-threshold`。

**Veo 混进人声时** → `--bed-gain 0`,把原生音整条静音。ducking 压得低竞争人声,
消不掉它。

---

## 时长调和

`C` = clip 秒数,`N` = 旁白秒数,`pad` = 0.25。优先级:**什么都不做 > 给旁白提速 >
冻结尾帧 > 失败。**

| 情况 | 做法 | D |
|---|---|---|
| `C ≥ N+pad` | 画面为准,旁白补静音 | `C` |
| 需要的提速 ≤ 1.12× | `atempo`,画面不动 | `C` |
| 缺口 ≤ 0.8s | `tpad=stop_mode=clone` 冻结尾帧 | `N+pad` |
| 都不行 | **exit 3**,打印所需词数 | — |

**冻结排在提速后面是有原因的:** 每条 clip 都被写成在运动模糊里结束(假一镜),
克隆那一帧会把"一镜到底"变成"卡住了"。轻微提速几乎听不出来,视觉停滞很明显。
1.12× 这个上限是听感边界 —— 再快,纪录片男声就明显赶了。

提速会同时改变字幕 cue 的时间:`cue / tempo + 0.12`。这两处偏移忘了改就是
字幕整体飘。

---

## 字幕:三层探测,本机落在 tier-2

```
tier 1  ffmpeg 有 subtitles 滤镜(libass) → subtitles=…:force_style=…
tier 2  没有 libass,用 Pillow            → 每条 cue 渲成整帧透明 PNG + overlay
tier 3  两者都没有                        → 软字幕 + 告警
```

**本机 ffmpeg 不含 libass / freetype / fontconfig**,`subtitles` 和 `drawtext`
滤镜都不存在,而且 homebrew-core 当前的 ffmpeg 公式本身就不带 —— `brew` 修不好。
所以 **tier-2 是主路线,不是降级方案**。脚本每次都探测,将来 ffmpeg 换了自动升 tier-1。

tier-2 的做法:Pillow 把每条 cue 渲成**整帧** RGBA PNG(不是只画文字块再去 ffmpeg
里算位置 —— 位置算错是最烦人的一类 bug,整帧让 overlay 永远是 `x=0:y=0`),
`stroke_width` 描边替代 libass 的 `Outline`,字号按画面宽度自适应并逐步缩小直到
3 行内放得下,底部留 11% 安全区。

**按块烧,时间戳是块内 0 基的** —— 因为每块是独立归一化后才拼接的,所以烧录
路径完全没有全局偏移算术。合并成一条全局 `final.srt` 只是给 YouTube 的旁挂文件,
纯文本操作,不碰视频。这消掉了整个设计里最容易出 bug 的一环。

字体:优先 Anton(`brew install --cask font-anton`),否则退到 Arial Black /
Impact。`--font` 可指定。`--no-upper` 关掉自动大写。

---

## 幂等与断点续跑

**这是强制项,不是加分项。** 单 profile 串行,6 块约 20 分钟,Flow 会话有真实
概率死在中途。

每块的归一化产物比它的输入(clip / 旁白 / cue PNG)新就跳过 —— 实测重跑一次
0.24 秒。`--force` 强制重做。

---

## 故障对照

| 症状 | 原因 | 处置 |
|---|---|---|
| exit 4,打印两块的签名差异 | 归一化后流参数不一致 | 看差在哪一项;通常是某块跳过了归一化(用了旧产物)→ `--force` |
| exit 3 | 某块旁白装不下 clip | 改短文案重配音,或把那块的 clip 升到更大的桶重出 |
| 实际时长与预期差 >0.25s | 有块的时基/帧率没被统一 | 检查告警指向的块 |
| 旁白听不清 | 原生音太吵 | 调低 `--bed-gain`,或直接 0 |
| 原生音里有人说话 | Veo 自发生成了人声 | `--bed-gain 0`;下次在提示词里加硬门禁 |
| 字幕糊 / 位置怪 | 字体或安全区 | `--font` 换字体;竖屏和横屏的安全区不同,已按比例算 |
| 字幕整体偏移 | 提速后 cue 没跟着改 | 这是脚本内部逻辑,报 bug |
