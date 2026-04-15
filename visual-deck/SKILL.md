---
name: visual-deck
description: Generate "image + text" style visual PPT decks (evangelism / internal sharing / client-facing) using an HTML→PPTX pipeline with safe-zone typography, Nano Banana backgrounds, and overflow-to-notes discipline. Use when the user wants a visually dense, cinematic slide deck where layout is image-driven rather than text-driven. NOT for pure data reports or text-heavy documents.
version: 0.2.0
---

# visual-deck — 视觉版 PPT 生成

## 何时触发

**适用**：
- 布道版 / 对外方案 / 内部分享类 PPT，版式优先、内容随图走
- 需要背景图 + 前景文字的「图+文」统一风格
- 单页信息密度高，但视觉需要干净

**不适用**：
- 纯数据报表、纯文字文档 → 用 docx/xlsx
- 临时一次性 PPT，不值得搭 pipeline → 直接用 pptx skill
- 客户方不接受 cinematic 风格 → 本 skill 的图像语言不匹配

## 三条硬约束（不可妥协）

这三条是踩过坑换来的，违反任何一条直接退回：

### 1. 文字只进安全区，溢出走 notes

- 每张 slide 都有天然的图像安全区（暗色区/留白区），前景文字**只能排在里面**
- 正文装不下时：**不许缩字号**，不许退回"全屏蒙版压字"。把溢出内容灌进 `slide.addNotes()`
- 具体安全区%见 `references/safe-zone-spec.md`

### 2. Image prompt 必须 V2 四段式

- `描述 / Composition / Style / Do not include` 四段齐全
- 安全区百分比写死在 Composition 段（"top 15% / bottom 15% fade to void"）
- 色彩用 token + hex 双写（"warm coral, hex #FF6B47"）
- 模板和示例见 `references/image-prompts-v2.md`

### 3. Nano Banana 比例有限

- 支持：16:9 / 4:3 / 1:1 / 3:4 / 9:16
- **不支持 21:9** — 需要超宽时走变通（拼接 / 裁切 / HF 铺底 + 暗罩）
- 细则见 `references/nano-banana-ratios.md`

## 四段 Pipeline

```
slides/*.html  ──► html2pptx.js ──► 基础 pptx
       ↑
 images/*.png ──(CSS background)── 背景图由 HTML 直接引用
                 │
      notes-map.js ──► 溢出文案灌 speaker notes
                 │
              build.js ──► 最终 pptx
```

**文件角色**：

| 文件 | 作用 | 是否改 |
|---|---|---|
| `pipeline/html2pptx.js` | HTML→PPTX 渲染器，处理定位/文字/图片/shape/placeholder/overflow 检测 | **不改** |
| `templates/build.js` | 主构建脚本：遍历 slides/ + 注入 notes + 写 pptx | 改元信息（title/author/文件名） |
| `templates/themes/*.css` | **主题 token** — `dark-coral.css`（默认）/ `dark-teal.css` | **换主题只改这里** |
| `templates/layouts/*.html` | 版式骨架库（见下方决策树） | 复制后填内容 |
| `templates/notes-map.js` | 溢出文案映射 `{ slideNum: "notes..." }` | 按需填 |
| `templates/package.json` | 依赖声明（playwright / pptxgenjs / sharp） | 不改 |

## 版式决策树（选 layout 时走这个）

```
问 1：这页是章节边界 / 封面 / 封底吗？
  是 → slide-cover.html (HF)
  否 → 继续

问 2：这页只有一句金句（≤40 字），别的都稀释它？
  是 → slide-quote.html
  否 → 继续

问 3：这页是"数字说话"（KPI / 成绩单 / 市场数据）？
  是 → 只有一个核心数字？
        是 → slide-quote.html（把数字放大成金句）
        否（3~4 个并列数字）→ slide-stats.html
  否 → 继续

问 4：这页是"按时间/阶段讲流程"？
  是 → slide-timeline.html（3~5 个节点）
  否 → 继续

问 5：这页是"对比/并列"？
  是 → 几项？
        2 项 → slide-2col.html（before/after, A/B）
        3 项 → slide-3col.html（三段论）
        4+ → 拆页或 stats
  否 → 继续（下面是默认主力）

问 6：有一个核心视觉隐喻 + 2~4 条要点？
  是 → 前后页已连续 r34 两次？
        是 → slide-l34.html（换方向打破节奏）
        否 → slide-r34.html（默认）
  否 → 停下来想想这页要讲什么，版式够不够（不够再扩）

每次选完问自己：
  - 前后三页是否都是同一个版式？→ 考虑切镜像或换 layout
  - quote 页是否超过 3 页？→ 金句稀释了，降级成 r34
```

**版式目录**（8 个）：

| Layout | 用途 | 关键信号 |
|---|---|---|
| `slide-cover.html` | HF 全幅，封面/章节/封底 | 有背景图 + 大标题 |
| `slide-quote.html` | 居中金句 | 一句话，≤40 字 |
| `slide-stats.html` | 2×2 数字格子 | 3~4 个并列 KPI |
| `slide-timeline.html` | 水平时间轴 | 3~5 阶段/节点 |
| `slide-2col.html` | 双栏对比 | 二元对比（A/B） |
| `slide-3col.html` | 三栏并列 | 三段论 / 三种 X |
| `slide-r34.html` | 右图 + 左文（主力） | 一个论点 + 2~4 bullet |
| `slide-l34.html` | 左图 + 右文（镜像） | 同 r34，但换方向 |

每个 layout 文件顶部有 `USE WHEN` / `DO NOT USE WHEN` 注释，选不定就打开文件看。

## 扩展约束（给未来的自己）

**新增 layout / theme 前必须回答**：

1. 现有版式为什么不够？举一个具体 slide 说不通的场景。
2. 新版式的 USE WHEN / DO NOT USE WHEN 分别是什么？
3. 这条决策树改动后，是否让"选择更容易"而不是"更纠结"？

如果这三题任何一题答不清，**这个版式就不该加**。扁平地堆 layout 会让 Claude 面对 skill 时选择困难，信息结构 ≫ 选项数量。

**新增 theme 同理**：说清"为什么现有 dark-coral / dark-teal 不够"再加。

## 标准执行流程

1. **明确主题与页数** — 先问用户：主题色系（默认暗色 CORAL）、页数、是否需要封面/目录/封底
2. **生成 HTML slides** — 基于 `templates/slide.html` 骨架，每页先写 HTML，**在浏览器/devtools 里检查 overflow**（`html2pptx.js` 也会兜底检测并报错）
3. **生成 image prompts** — 按 V2 四段式格式，输出到 `image-prompts.md`，用户拿去 Nano Banana 批量跑
4. **收齐图片** — 用户把生成的图放进 `images/slideNN.png`
5. **填 notes-map.js** — 溢出内容、口播补偿都进这里
6. **跑 build** — `node build.js`，产出 `.pptx`

## 关键陷阱（Claude 自己最容易犯的）

- ❌ 想着"字装不下就缩小到 10pt" —— 违反约束 1，必须 notes
- ❌ "这个图要 21:9 超宽" —— Nano Banana 不支持，要么 16:9 HF 裁掉两侧，要么拼图
- ❌ Image prompt 漏了 "Do not include" 段 —— 会生成文字/logo/水印污染
- ❌ HTML body 尺寸写错（非 `720pt × 405pt` for 16:9） —— `html2pptx.js` 会抛 dimension mismatch 错误
- ❌ 在 `build.js` 里硬编码页数 —— 用 `fs.readdirSync('slides/')` 动态枚举
- ❌ **inline `<span>` 上写 `margin`** —— `html2pptx.js` 拒绝（PPTX 无 inline box model）。需要间距用 `padding-left` 或把 span 改成 inline-block
- ❌ **在 div 上用 `linear-gradient` 背景** —— `html2pptx.js` 只接受 solid color 或 `url(...)` 图片。需要渐变效果：要么 solid color 近似，要么把渐变做进背景图，要么用 `body` 背景（body 支持 url，div 不支持渐变）

## 主题系统

所有色彩/字体/字号/padding 都在 `templates/themes/*.css` 里作为 CSS 变量。每个 slide HTML 顶部 `<link rel="stylesheet" href="../themes/<theme>.css">` 引用，内部 `<style>` 只用 `var(--xxx)`，**不许写死 hex**。

**可选主题**：
- `dark-coral.css`（默认） — 暖色，偏情感/洞察/人文调性
- `dark-teal.css` — 冷色，偏技术/架构/理性调性

**切主题**：改所有 slide HTML 里 `<link>` 的路径即可（或者全 deck 同一主题就用项目级 sed/find 一键替换）。

**换主题**：只改 `theme.css` 一个文件，所有 slide 跟着变。theme.css 末尾注释了暗色 TEAL / 浅色 NAVY 两套示例变量。

**核心 token**：
- `--bg / --fg / --muted / --dim / --faint` — 底/正文/次/最弱/footer
- `--accent / --accent-2` — 主/副点缀色
- `--font-sans`、`--fs-hero/title/subtitle/lede/body/label/source` — 字体字号
- `--pad-slide / --pad-r34 / --pad-l34` — 三种 layout 的 padding
- `--scrim-base / --scrim-left / --scrim-heavy` — 暗罩透明度档位

## 快速开始

看 `examples/minimal/` —— 2 页可跑的最小例子。复制整个目录到新项目，`npm install` 后 `node build.js` 就有 pptx。
