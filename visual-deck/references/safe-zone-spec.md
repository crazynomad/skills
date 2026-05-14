# 安全区契约 (Safe Zone Spec)

> **第一原则**:前景文字只能排在图的天然安全区里。装不下 → **改文案、拆页、或溢出走 speaker notes**。**不许缩字号**。

这套契约是 visual-deck 0.x 时代踩过的坑积累出来的——`overflow: hidden` 会让超出 1080px 的内容**完全消失**,投影看不见,导出 PDF 也丢。每个版式定下来的 padding / max-width / font-size 都是"装得下"的硬上限。

适用于 open-slide 的 **1920 × 1080 px** 画布。所有数值已从 visual-deck 0.x 的 720pt 系统按 **2.667x** 映射到当前像素。

## Canvas

| 单位 | 宽 | 高 |
|---|---:|---:|
| px | 1920 | 1080 |
| inch | 20 | 11.25 |
| pt | 1440 | 810 |

→ open-slide 框架内部把 1920×1080 缩放显示到任何 viewport,设计时**就当作真的有 1920×1080 像素**。

## 三种主版式的安全区

### HF (Hero-Fill, 16:9 全幅背景)

用于封面、章节边界、收尾、独占金句页。**对应 layout: `hero-cover.md` / `thesis.md`**

- **背景图**:1920 × 1080 全幅铺满
- **scrim 暗罩**:CSS `linear-gradient(rgba(10,10,10,0.55), rgba(10,10,10,0.55))` 叠加(替代 v0.x 的 PNG scrim 烘焙)
  - 稀疏文字页:`0.45 - 0.55`
  - 中等密度页:`0.60 - 0.65`
  - 密集网格页:`0.70 - 0.75`
- **天然安全区**:图像的 top 15% / bottom 15% 应该是 void(近黑或低对比),放置大标题、label、source 不会被图像主体压住
- **文字规则**:hero 标题 ≤ 200px、副标题 ≤ 50px、label ≤ 28px;文字密度不超过画面 30%

### Right Image 3:4(右侧竖图 + 左侧文字)

用于内容页,适合有一个核心视觉隐喻的论点页。**对应 layout: `takeaway.md`**

- **图像区**:右侧 800 × 1080 px(3:4 比例)
- **文字安全区**:左侧 padding 128px,右边界 **不越过 1015px**(给图留 55px 气口)
- **图像柔化**:通过 CSS `linear-gradient(to right, bg 0%, bg 55%, ..., rgba(10,10,10,0) 100%)` 把图像左缘渐隐到底色,不需要在出图时让 prompt 处理
- **文字容量**:eyebrow(24px)+ 标题(85px,≤2 行)+ lede(37px,≤2 行)+ 3~4 条 bullet(32px)

### Left Image 3:4(左侧竖图 + 右侧文字)

R34 镜像版本。**对应 layout: `chapter-cover.md`**

- 图像区放在左侧 0–800px
- 文字 padding-left: 850px(留 50px 气口)
- gradient 方向反转: `linear-gradient(to left, ...)`

## 如何判断"装不下"

v0.x 时代有 `tools/check-overflow.js` 跑 Playwright 测 scrollHeight。**v1.0 (open-slide) 没有自动检测**——必须人工算。

**算法**(在动手写 JSX 之前):

```
usable height = 1080 - top padding - bottom padding
              = 1080 - 112 - 96 = 872  (HF 默认)
              = 1080 - 112 - 96 = 872  (R34 也是)

每个块占用 height = font_size × line_height × lines
两块之间加 gap 32-64px

逐块累加,total ≤ usable
```

**每个 layout 文件顶部的"视觉预算"段落已经把这道题做过了**——你只要确认你写的内容**没有超出该 layout 文档给的行数限制**就行。

举例:`takeaway.md` 规定 takeaway 文字 ≤ 3 行。你写 4 行?即使加 `overflow: hidden` 也不行——第 4 行会被砍掉,投影上看不见。**改文案,拆成两页或缩文本**。

## 文字溢出处理的正确姿势

在 open-slide 1.0 里,speaker notes **直接写在 React 组件里**(不再是 `notes-map.js`):

```tsx
const Ch1Takeaway: Page = () => (
  <div style={{ ... }}>
    {/* visible content */}
    <h2>史上最佳财报 × 最大客户造反 = 一个需要被研究的悖论</h2>

    {/* speaker notes (open-slide 自动从这个特殊 element 抽出) */}
    <aside data-speaker-note>
      口播补充:18% 这个数字放在第一句开口。后面两条是上下文,不要每条都展开,留 15 秒收。
    </aside>
  </div>
);
```

(注:open-slide 1.x 的 speaker notes API 仍在演化,具体语法见框架最新文档。)

观众看画面、讲者看 notes、导出 PDF 时画面 + notes 都有。三赢。

## 反例(绝不要做)

- ❌ **把字号从 12pt 压到 9pt 硬塞** — 违反第一原则,观众看不清
- ❌ **把 HF scrim 调到 0.85+ 盖住整张图** — 图就白生成了,等于纯色底
- ❌ **在 R34 的图像主体上压文字** — 除非图特意留了中心 void 区
- ❌ **同一页放 >5 个 bullet** — 拆页或进 notes
- ❌ **用 `overflow: hidden / scroll / auto` 隐藏超出** — 画面会消失,等于没有那段内容
- ❌ **用 `transform: scale(0.8)` 缩小元素塞进去** — 缩放后字号低于 28px 不可读

## v0.x → v1.0 单位换算表(供老 deck 迁移参考)

| 0.x (pt) | 1.0 (px) | 用途 |
|---:|---:|---|
| 60pt | 160 | Hero 大标题 |
| 32pt | 85 | Section heading |
| 16pt | 43 | Subtitle / lede |
| 14pt | 37 | Body lede |
| 12pt | 32 | Body |
| 9pt | 24 | Label / caption |
| 8pt | 21 | Source |
| 42pt | 112 | padding 顶部 |
| 48pt | 128 | padding 左右 |
| 36pt | 96 | padding 底部 |
| 304pt | 800 | 竖图宽 |
| 320pt | 850 | r34/l34 单侧 padding |
| 720pt | 1920 | 画面宽 |
| 405pt | 1080 | 画面高 |

公式:`px = round(pt × 2.667)`,等价于 `px = round(pt × 1920 / 720)`。
