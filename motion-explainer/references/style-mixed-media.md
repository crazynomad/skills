# 风格:Mixed Media 编辑部拼贴(默认)

平面、明亮、社论感。档案照剪影 + 平涂色块 + 半调网点 + 手绘圈注。
适合数据故事、"为什么 X"、竖屏短片。

每条提示词的目标都一样:**一张被做成动画的社论拼贴**,永远不是一个被拍下来的场景。

---

## 视觉词汇

每块挑两三样组合,选择依据是"这一块的旁白在讲什么",不是"哪个好看"。

- **档案剪影** —— 照片主体(人、建筑、物件)带粗糙白纸边被剪出来,在平涂背景上
  漂移或啪地落位。照片是拼贴里的**元素**,整帧永远不是实拍。
- **平涂色场** —— 大胆的社论底色:暖黄、米白纸、深藏青、珊瑚红。每块一个主色,
  整片共用一套点缀色。
- **纸与印刷质感** —— 颗粒、半调网点、报纸纹、撕边、胶带条、轻微投影,
  把"剪下来贴上去"的手感卖出去。
- **手绘标注** —— 马克笔圆圈自己画出来圈住某个剪影、下划线扫入、箭头连接元素、
  强调乱笔。(**只能是抽象笔触,不能是字母或单词。**)
- **抽象数据图形** —— 柱状图长起来、折线自己画上去、饼图分离,**不带标签、
  不带数字、不带坐标轴文字**,纯形状与运动。
- **地图** —— 平面风格化地图,路线动画、脉动的地点圆点、区域填色。
- **遮盖条与高光块** —— 实色色条滑过某个区域、聚光暗角把一个剪影孤立出来,
  其余压暗。
- **尺度对比** —— 一个物件复制成阵列、小剪影紧挨着巨大剪影、堆叠长高。

## 运动词汇

Vox 的运动是干脆而有意图的:快速 ease-out 入场、元素带轻微过冲滑入/弹入、
"你听好"节拍上的缓慢推镜、想法之间的甩镜或翻页、拼贴图层之间的视差漂移。
**永远有东西在动,但同一时刻只有一样东西是"响"的。**

---

## STYLE KEY 提示词(整片一次,免费)

`gflow image t2i "<下面这段>" --model nano-pro --aspect <9:16|16:9> --ui-mode classic --json`:

```
Editorial mixed-media collage style swatch, documentary motion-graphics
aesthetic: flat warm yellow and off-white paper background with halftone dot
texture, archival photo cutouts with rough white paper borders, torn paper
edges and tape strips, hand-drawn black marker circles and arrows, bold flat
color blocks in navy and coral, subtle paper grain and drop shadows.
Abstract composition only — no characters, no objects with faces, no
letters, no words, no numbers. Non-photorealistic, no live-action, no
realism, no 3D render.
```

## STYLE tokens(每块的关键帧和视频提示词都以它开头)

```
editorial mixed-media collage, archival photo cutouts with white paper
borders, flat bold color fields, halftone and paper grain textures,
hand-drawn marker annotations, snappy motion-graphics animation,
non-photorealistic, no live-action
```

---

## 分块提示词模板

**关键帧(图像,免费)** —— 只描述一张静止画面。这是风格与构图的判定点:

```
{STYLE tokens}. {SCENE:这一块旁白对应的拼贴构图 —— 哪些剪影、什么底色、
哪些标注/图表/地图,以及它们怎么摆}. Single still frame, no motion blur.
No letters, no words, no numbers, no captions, no watermark, no logo,
no photorealism, no live-action, no 3D render.
```

**视频(i2v,1 积分)** —— 首帧已经定了画面,所以只描述**怎么动**:

```
{STYLE tokens} — one continuous camera move, no cuts.
MOTION: {入场编排 + 镜头运动 + 镜头内什么在动}.
SOUND: {环境床 + 一两个纸张/whoosh/tick 音效}.
No speech, no dialogue, no singing, no voiceover.
No readable text, letters, words, numbers, captions, subtitles, watermark,
logo, photorealism, live-action footage, 3D render, lip-sync,
talking characters, color drift.
```

最后那两行是固定的,逐字复制。

### 两条最容易忘的规则

1. **片内不能出现任何可读文字。** AI 拼字必糊。排版感用抽象高光条、遮盖块、
   圈线和下划线来表达。真字幕由 `assemble.py` 在本地烧录。
2. **片内不能有人说话,也不能有人声。** 旁白是后期按块贴上去的。
   Veo 会自发生成人声(人群嘈杂、旁白腔),所以 `No speech…` 那行是**硬门禁**,
   不是风格建议 —— 混进人声只能 `assemble.py --bed-gain 0` 把原生音整条静音,
   而那时积分已经花了。

### 从 Higgsfield 迁过来时要删掉的东西

老提示词库里的 `Shot 1 … Cut to shot 2` 这类**提示词内切镜语法,Veo 不执行** ——
写了也只会得到一个镜头。假一镜(单一连续运镜、首尾都在运动模糊里)仍然有效,
继续用。

---

## 范例

旁白(Block 1):*"Every day humans throw away enough food to feed two billion
people."*

关键帧提示词:
```
editorial mixed-media collage, archival photo cutouts with white paper borders,
flat bold color fields, halftone and paper grain textures, hand-drawn marker
annotations, non-photorealistic, no live-action. A warm yellow paper background
with halftone texture. Photo cutouts of apples, bread loaves and a full dinner
plate arranged in a neat grid; a torn-paper bin shape at the bottom edge; a
thick black marker circle around the last remaining plate. Single still frame,
no motion blur. No letters, no words, no numbers, no captions, no watermark,
no logo, no photorealism, no live-action, no 3D render.
```

视频提示词(i2v,首帧 = 上面那张):
```
editorial mixed-media collage, halftone and paper grain textures, snappy
motion-graphics animation, non-photorealistic, no live-action — one continuous
camera move, no cuts.
MOTION: the grid cutouts flip over one by one and tumble downward off-frame
into the torn-paper bin; slow camera push-in as they fall; the marker circle
draws itself in one confident stroke at the end.
SOUND: soft paper rustles and quick whoosh ticks as cutouts flip and fall,
low minimal ambient pulse underneath.
No speech, no dialogue, no singing, no voiceover.
No readable text, letters, words, numbers, captions, subtitles, watermark,
logo, photorealism, live-action footage, 3D render, lip-sync, talking
characters, color drift.
```

---

## 脚本形状范例(6 块 ≈ 45 秒)

题目:"为什么食物浪费其实是供应链的故事"

```
Block 1  Humans throw away enough food each day to feed two billion people.
Block 2  We blame picky eaters. The biggest losses happen far earlier.
Block 3  In poorer countries crops rot on the farm, waiting for trucks.
Block 4  Rich countries flipped it: food dies in supermarkets, not fields.
Block 5  Here's the twist. Fixing trucks beats every household campaign.
Block 6  The fight isn't in your kitchen. It's in the boring machinery.
```

注意形状:冷开场统计 → 利害 → 两个证据节拍 → 转折 → 回扣第一块的收尾。
每行一个想法,**14–18 词**,数字拼写成单词,没有废话。
