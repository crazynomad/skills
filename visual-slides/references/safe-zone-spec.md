# 安全区契约 (Safe Zone Spec — Slides 版)

> **第一原则**:前景文字只能排在图的天然安全区里。装不下 → `{{pN-notes}}`,**不许缩字号**。

这份契约和 `visual-deck/references/safe-zone-spec.md` 用同一套百分比,但落在 Slides 上有两处差别——见末尾 **Slides 适配**。

## Slides 16:9 页面尺寸

Slides 默认 16:9 页面在 API 里是 EMU 单位:

| 单位 | 宽 | 高 |
|---|---|---|
| EMU | 9,144,000 | 5,143,500 |
| inch | 10.0 | 5.625 |
| pt | 720 | 405 |
| px @ 96dpi | 960 | 540 |

**所有"百分比"按 720×405 pt 算,和 visual-deck 完全一致**——只是 Slides 不渲染 HTML,所以你在母板里靠"眼睛 + 标尺"摆位,不靠 CSS。

## 三种标准 layout 的安全区

### HF (Hero-Fill, 全幅背景)

用于封面、章节页、封底、大金句。

- **背景图占位**:一个 720pt × 405pt 的形状(rectangle),里面写 `{{pN-img-hero}}`
- **暗罩**:已经烘进 PNG 里(`scrim_bake.py`,alpha 0.55~0.62),Slides 不再叠
- **天然安全区**:top 15% / bottom 15% 是 void,放大标题 / label / source
- **文字规则**:hero 标题 ≤ 60pt,副标题 ≤ 16pt,label ≤ 9pt;文字密度不超过画面 30%

### R34 (Right 3:4, 右侧竖图 + 左侧文字)

主力内容页。

- **图像形状**:右侧 304pt × 405pt(3:4),里面写 `{{pN-img-side}}`
- **文字安全区**:左侧 padding 48pt,右边界 **不越过 380pt**(给图留 16pt 气口)
- **图像柔化**:出图时 prompt 里写"left edge fades to void 40pt"——Slides 不能做 CSS 渐变,**必须烘进 PNG**
- **文字容量**:eyebrow 9pt + 标题 32pt(≤2 行)+ lede 14pt(≤2 行)+ 3~4 条 bullet(12pt)

### L34 (Left 3:4, 左侧竖图 + 右侧文字)

R34 镜像。

- 图像形状放左侧 (left:0, 0~304pt)
- 文字区 left padding 改为 320pt
- 图像渐变方向反转(prompt 里写"right edge fades to void")

## Slides 适配(与 visual-deck 的差别)

### 1. 没有 overflow 自动检测

`html2pptx.js` 能跑 Playwright 测 scrollHeight,Slides API **不能**。所以:

- 母板设计时**预留 20% 余量**(把 lipsum 文本填到形状里看是否撑爆)
- 用 `inject.py --dry-run` 看请求量是否合理,但**真出 deck 后必须人工翻一遍**
- 长文本溢出会被 Slides 自动隐藏(超出形状部分不显示)——比 PPTX 报错更隐蔽

### 2. 字体回退要演练

- Slides 默认字体是 Arial / 思源黑体。母板用什么字体,占位符替换后字体**继承形状原样式**
- **中文母板必须先设好中文字体**(思源黑体 / 阿里巴巴普惠体),不然 Arial 渲染中文会回退到不可预测的系统字
- 母板填好假数据预览过一次再投入生产

### 3. 暗罩烘焙更刚需

Slides 不渲染 CSS gradient,**也不支持形状半透明叠层**(技术上支持,但 API 操作繁琐到不实用)。所以:

- 所有 HF/R34/L34 背景图**必须先跑 `scrim_bake.py`**
- 母板里的图像占位形状不要再叠半透明矩形——浪费,且影响 replaceAllShapesWithImage

## 溢出走 notes 的正确姿势

母板的每页 speaker notes 区域里写一个占位符:

```
{{p3-notes}}
```

content-plan.json 里:

```json
{
  "page": 3,
  "text": { "title": "...", ... },
  "notes": "【口播 · 第 3 页】\n— 这条信息画面太挤,放口播\n— 补充数据 / 背景故事 / 引用链接"
}
```

`inject.py` 会把它替换成完整 notes 文本。观众看画面、讲者看 notes、读者下 PDF 时画面 + notes 都有。

## 反例(绝不要做)

- ❌ 把字号从 12pt 压到 9pt 硬塞——观众看不清,违反第一原则
- ❌ HF 暗罩调到 80%+ 盖住整张图——图就白生成了
- ❌ R34 图像主体上压文字——除非图特意留了 void 区
- ❌ 一页 >5 个 bullet——拆页或进 notes
- ❌ 母板里给占位符做花字效果(粗体 + 阴影 + 字间距)——替换后样式保留,中英文混排会撞墙
