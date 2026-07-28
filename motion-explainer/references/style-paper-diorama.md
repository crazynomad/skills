# 风格:纸模纪录片(Paper Diorama)

电影感做旧棕褐报纸微缩景观、黑色遮眼条剪影人物、单一焦橙点缀、活字印刷道具文字、
钨丝灯光、移轴微距。

用在:brief 说"电影感 / 有戏剧性 / 调查感 / 像那个 AI 泡沫的片子",或者题材是
地缘政治、金钱、权力。

---

## 与 Mixed Media 的关键差异:这个风格**带文字**

Mixed Media 禁止片内出现任何文字。这个风格反过来 —— **活字印刷标签是它的签名**。

规则:每场**一个**标签,1–2 个词或一个数字(`EXPIRED`、`1,000`、`AUGUST`、
`WHO BLINKS?`),永远描述成"撕边焦橙纸元素上的做旧活字印刷",并且在否定词里
明确圈定:

```
No text anywhere except "<LABEL>". No gibberish letters, no captions,
no watermark, no photorealism, no live-action.
```

为什么这条例外成立而 Mixed Media 那边不成立:单个短标签 + 已确认过的关键帧
把出错面收窄到了可控范围。**标签越长越容易糊,超过两个词就别试。**

实测(2026-07-27,nano-pro):`WHO PAYS?` `THE BILL` 这类 1–2 词标签渲染得
非常干净,连票根的齿孔都对。**这条规则在 gflow 侧同样成立**,不只是 Higgsfield。

### 陷阱:模型会把 diorama 理解成「桌上的展示盒」

`diorama` 这个词本身带歧义 —— 它既可以是"你身处其中的微缩世界",也可以是
"陈列柜里的模型"。nano-pro 有相当概率选后者:实测 9 张关键帧里有 **4 张**
自己长出了木盒边框/托盘/桌面,读起来像"桌上摆着一个模型",而另外 5 张是
"镜头就在纸世界里面"。**混在一起、再配上 FPV 运镜,跳跃感很明显。**

每条关键帧提示词都加上这段(和 STYLE tokens 一样固定):

```
The camera is INSIDE this paper world at eye level with the figures —
the scene fills the entire frame edge to edge. No wooden box, no tray,
no display case, no table surface, no frame or border around the scene,
no shot of a model sitting in a container.
```

这类问题只在**把 9 张摆在一起看**的时候才暴露 —— 单张单张看,每一张都挺好。
所以出片前务必拼一张联络表(`ffmpeg xstack`)整体过一遍。

### 陷阱:场景里出现「天然带字的物件」时,围栏会失效

`No text anywhere except "<LABEL>"` 挡得住凭空冒字,**挡不住模型去填一个本来
就该有字的东西**。实测:写"一张手风琴折叠的**发票**",模型老老实实印上了
`INVOICE` / `Date:` / `Description` / `Qty`,其中一行糊成了 `TOTAL FLYER₹S.50`。

会触发这个的物件:发票、账单、报纸头版、路牌、票据、表格、合同、屏幕。

**两个办法,都要用:**

1. **换个不带字义的名词。** "invoice" → "paper ribbon" / "paper strip"。
   词本身携带的语义比 negative 更有力。
2. **显式声明它是空白的**,别指望 negative 兜底:
   ```
   The paper ribbon is COMPLETELY BLANK — plain unprinted cream paper,
   no ruled lines, no form fields, no columns, no headings, no numbers
   of any kind. …and that band is the only printed thing in the frame.
   ```

注意做旧报纸墙面上的乱码字**是这个画风的构成部分**,不用管它 —— 要治的是
「本该承载信息的物件上出现了糊字」,那个才出戏。

这也是关键帧闸门的价值:这类瑕疵在**免费**阶段发现,重出零成本;直接出片就是
1 积分打水漂。

---

## STYLE KEY 提示词(整片一次,免费)

`gflow image t2i "<下面这段>" --model nano-pro --aspect <9:16|16:9> --ui-mode classic --json`:

```
Cinematic vintage paper diorama style swatch, documentary collage aesthetic:
a miniature three-dimensional landscape built entirely from aged sepia
newspaper sheets and cardboard, torn edges, layered paper canyon walls of old
newsprint, monochrome archival photo cutouts of anonymous suited figures
standing among the paper structures with black censor bars over their eyes,
one dominant burnt-orange paper prop as the single color accent against the
sepia world, distressed letterpress print texture, warm tungsten documentary
lighting with deep shadows, macro tilt-shift lens look with shallow depth of
field, film grain and dust. Handcrafted physical paper materials only — no
letters, no words, no numbers, no logos. Non-photorealistic scene content,
no live-action people, stylized paper craft world.
```

## STYLE tokens

```
cinematic vintage paper diorama, aged sepia newsprint world, monochrome
halftone print, monochrome archival cutout figures with black censor bars
over their eyes, single burnt-orange accent, distressed letterpress,
warm tungsten light, macro tilt-shift shallow depth of field, film grain,
handcrafted stop-motion paper feel, non-photorealistic, no live-action
```

---

## 可复用道具:烘进关键帧,别挂在视频上

要让同一个物件在不同 block 之间不变形,就得给它一张固定的参考图。

**做法(gflow 版,与 Higgsfield 版不同):**

```bash
# ① 造道具(免费,每个一次)
gflow image i2i "Single reusable prop asset, centered on a plain warm off-white \
paper background. {道具描述}. {STYLE tokens}. Nothing else in frame. \
No letters, no words, no numbers." \
  --ref <风格键>.png --model nano-pro --aspect 1:1 \
  --out <run>/props --project <project_id> --ui-mode classic --json

# ② 用道具 —— 烘进那一块的关键帧里,不是挂到视频上
gflow image i2i "… the {道具A} from the reference image sits in the foreground …" \
  --ref <风格键>.png --ref <道具A>.png --ref <道具B>.png \
  --model nano-pro --aspect 9:16 --out <run>/keyframes \
  --project <project_id> --ui-mode classic --json
  #  ↑ 图像侧参考图上限 10 张,而且免费

# ③ 出片
"$SKILL_DIR/scripts/veo-gen" --final <run>/clips/blockNN.mp4 -- \
  i2v --initial-frame <run>/keyframes/blockNN.png --model veo-lite --duration 8 …
```

**为什么不把道具直接给视频:** `veo-lite` 的 `r2v` 参考图上限只有 **3 张**,
风格键就占掉一张,剩两张不够用。而图像侧上限 10 张、还免费 —— 把一致性问题
在免费阶段解决完,视频阶段只需要一张已经包含了所有道具的首帧。这是 Higgsfield
后端做不到的。

老 skill 里那四个道具的 job id 是 **Higgsfield 的**,对 gflow 毫无意义,
已移到 `backend-higgsfield.md`。gflow 侧的道具要重新造一遍,存本地路径 +
`flow_media_id`。

---

## 假一镜的分块提示词形状

每条 clip = 一次连续运镜;每个边界都藏在运动模糊里,于是硬切读作一镜到底。

**关键帧**(定住构图与风格):
```
{STYLE tokens}. {这一刻的画面:谁在哪、什么道具、光从哪来}.
One burnt-orange {道具} carries the distressed letterpress word "{LABEL}".
Single still frame. No text anywhere except "{LABEL}". No gibberish letters,
no captions, no watermark, no photorealism, no live-action.
```

**视频**(只描述怎么动):
```
{STYLE tokens} — ONE continuous high-energy FPV camera move with aggressive
speed ramps, no cuts.
The shot: [从上一块的运动模糊里冒出来] … [每约 3 秒一个冲击:砸 / 盖章 /
冲击波 / 啪] … [以完全运动模糊的 <俯冲/甩镜/坠落/耀斑> 结束].
SOUND: [3–5 个具体的画面内音效事件].
No speech, no dialogue, no singing, no voiceover.
No text anywhere except "{LABEL}". No gibberish letters, no captions,
no watermark, no photorealism, no live-action.
```

范例("WHO BLINKS?" 的开场块,已按 Veo 重写 —— **删掉了原版里的多镜切换语法**):
```
… ONE continuous high-energy FPV camera move with aggressive speed ramps.
The shot: from black, EXTREME slow-motion macro of a halftone-printed human
eye on newsprint as a thick black censor bar SLAMS down over it like a
guillotine, paper dust exploding on impact. Violent speed-ramp pull-back
reveals a giant newspaper front-page portrait; a gust RIPS the page away to a
second portrait, ripped away again to a third, each rip faster than the last.
The camera then DIVES at full speed into a tearing gap in a giant aged treaty
document as a burnt-orange stamp punches the letterpress word "EXPIRED"
across it; the lens plunges through the torn fibers into swirling paper dust,
ending mid-dive fully motion-blurred.
SOUND: guillotine slam with dust whump, three accelerating page rips, one
massive stamp punch, rushing paper wind.
No speech, no dialogue, no singing, no voiceover.
No text anywhere except "EXPIRED". …
```

---

## 审核:Veo 的边界是**未知的**

老 skill 里那份审核地图(政客真名必挂、面部特写要换引擎、mushroom cloud 触发
nsfw)全部是从 **seedance / gemini_omni 实测**来的,已移到 `backend-higgsfield.md`。

**不要把它当成 Veo 的地图。** Veo 的内容策略边界在本流程里**完全没有实测过**,
必须用真实运行一条条重建。目前只能给出这些有根据的推断:

- 眼部黑色遮盖条**本来就是这个风格的构成元素**,顺带把肖像相似度问题化解掉了 ——
  继续用,不管哪个引擎。
- 中景 / 全身的匿名西装人物是安全的写法;面部特写风险最高。
- 遇到 `content-policy` 类错误:**改提示词,不要重试**(重试不会变,而且如果
  错误发生在提交后,积分已经扣了 —— 判据见 `backend-gflow.md` 的信用安全规则)。
- 每次踩到新的审核边界,**把它写回这个小节**。这份地图的价值等于它的实测密度。

---

## 音乐

gflow 侧没有可用的独立音乐模型。两个选择:

1. 靠 Veo 的原生音效床(通常够用) —— 但要小心它自发生成人声,
   见 `backend-gflow.md` 的硬门禁。
2. 外部生成(Suno/Udio)后本地混。一份贴合这个风格的 brief:
   约 46 BPM 心跳脉冲,超低频 drone + 低音大提琴,几乎没有高频,
   8 秒一次的呼吸式起伏,开场就响,在全片 80% 处单次高潮,随后快速衰减到静音。
