---
name: visual-deck
description: Generate "image + text" style visual decks on the open-slide React framework with 绿皮火车's design system — dark-teal / dark-coral themes, four core layouts (hero-cover / chapter-cover / takeaway / thesis), Nano Banana background imagery, and safe-zone typography discipline. Use when the user wants a visually dense, cinematic slide deck where layout is image-driven rather than text-driven and is comfortable shipping a static URL or PDF. NOT for legacy .pptx file output — that path was removed in v1.0; future PPTX export is planned as an open-slide upstream contribution.
version: 1.0.0
---

# visual-deck — 视觉版 deck 设计系统

绿皮火车频道的 deck 设计语言。基于 [open-slide](https://github.com/1weiho/open-slide) React 框架,提供:**两套频道主题** + **四个核心版式词汇** + **Nano Banana 背景图规范** + **安全区/溢出/V2 prompt 编辑纪律**。

v1.0 是大版本切换:旧版的 HTML→PPTX 渲染管线(pptxgenjs / scrim-bake / 8 layouts / check-overflow)已**全部移除**。如果你要找 PPTX 输出能力,见 SKILL.md 末尾的 [PPTX Roadmap](#pptx-roadmap)。

## 何时触发

**适用**:
- 布道版 / 对外方案 / 内部分享 / YouTube 视频用 deck,**最终交付物可以是 URL 或 PDF**
- 单页信息密度高,版式需要干净一致
- 需要重复复用绿皮火车的视觉身份(dark-teal 技术系 / dark-coral 人文系)
- agent 主导的迭代式 deck(`pnpm dev` HMR + 浏览器 inspector + `/apply-comments`)

**不适用**:
- **必须**交付 `.pptx` 文件让客户在 PowerPoint 里编辑 → 暂时回退到 `pptx` skill,或等 PPTX 上游 export
- 纯数据报表 / 纯文字文档 → 用 docx/xlsx skill
- 一次性临时 deck(不值得 setup open-slide 项目) → 直接用 pptx skill

## 三条硬约束(从 visual-deck 0.x 继承)

这三条是踩过坑换来的,违反任何一条直接退回。

### 1. 文字只进安全区,溢出走 speaker notes

- 每张 slide 都有天然的安全区(暗色区 / 留白区),前景文字**只能排在里面**
- 正文装不下时:**不许缩字号**,不许退回"全屏蒙版压字"。把溢出内容塞进 speaker notes(写在 `<aside data-speaker-note>` 里),或拆页
- 详见 `references/safe-zone-spec.md`(已按 1920×1080 像素校准)

### 2. Image prompt 必须 V2 四段式

- 描述 / Composition / Style / Do not include 四段齐全
- 安全区百分比写死在 Composition 段
- 色彩用 token + hex 双写
- 详见 `references/image-prompts-v2.md`

### 3. Nano Banana 比例有限

- 支持 16:9 / 4:3 / 1:1 / 3:4 / 9:16
- **不支持 21:9** — 见 `references/nano-banana-ratios.md` 的三种变通

## 完整 Pipeline(v1.0)

```
立论文档(/ppt-classify + /ppt-research-setup)
       │
       ▼
image-prompts.md(V2 四段式)
       │
       ▼ (Nano Banana / agent 跑)
slides/<deck-id>/assets/*.png
       │
       ▼ (CSS scrim,不再烘焙 PNG)
slides/<deck-id>/index.tsx
       │     │
       │     └── 顶部 design: DesignSystem(从 themes/dark-teal.md 复制)
       │     └── layout helper(从 layouts/*.md 复制)
       │     └── 每个 Page 组件实现一页
       │
       ▼
open-slide pnpm dev → HMR < 1s 实时预览
       │
       ├── inspector 点元素加 @slide-comment
       ├── /apply-comments agent 改 JSX
       └── 反复迭代
       │
       ▼
pnpm build → dist/ 静态站点
   或 export PDF
   或 部署 Vercel
```

## 文件角色

| 文件/目录 | 作用 | 是否改 |
|---|---|---|
| `references/open-slide-bootstrap.md` | **必读** · 从零跑 open-slide 项目的速成 | 不改 |
| `references/safe-zone-spec.md` | **必读** · 安全区 + 1920×1080 单位换算 | 不改 |
| `references/image-prompts-v2.md` | **必读** · V2 四段式 prompt 规范 | 不改 |
| `references/nano-banana-ratios.md` | 出图比例约束 + 21:9 变通 | 不改 |
| `references/workflow-multi-skill.md` | 5 阶段全链路工作流(WHY/WHAT/VISUAL/HOW/QA) | 不改 |
| `themes/dark-teal.md` + `dark-teal.demo.tsx` | 技术章节默认主题(冷色),paste-ready | 用户用 |
| `themes/dark-coral.md` + `dark-coral.demo.tsx` | 人文章节主题(暖色) | 用户用 |
| `layouts/hero-cover.md` | 全幅背景 layout 模板 | 用户用 |
| `layouts/chapter-cover.md` | 章节扉页(800px 竖图 + 双栏) | 用户用 |
| `layouts/takeaway.md` | 每章结语(800px 右图 + 金句 + NEXT) | 用户用 |
| `layouts/thesis.md` | 居中陈述(全片论点 / 收尾) | 用户用 |
| `layouts/README.md` | layout 决策树 + 项目特化版式索引 | 不改 |

## 版式决策树(选 layout 时走这个)

```
问 1:这页是封面 / 章节边界 / 收尾吗?
  是 → hero-cover(全幅背景 + 大标题)
  否 → 继续

问 2:这页是章节起始(承接上一章 + 预告本章)?
  是 → chapter-cover(800px 竖图 + 大章号 + 双栏 + echo)
  否 → 继续

问 3:这页是每章结束的金句(takeaway 一句话)?
  是 → takeaway(800px 右图 + 金句 + NEXT 块)
  否 → 继续

问 4:这页是全片中心论点 / 收尾反问 / 单页独占的金句?
  是 → thesis(居中大字 + 副标题)
  否 → 不在 4 个核心版式里,写 inline 组件——
       参考 ep10 的 TOC grid / Meta finding / Three stat cards(都是项目特化)
       源码:~/Github/greentrain-studio/main/episodes/ep10-ai-ppt/open-slide-deck/slides/ep10-nvidia-moat/index.tsx
```

更多选择细节看 `layouts/README.md`。

## 主题决策

| 调性 | 选哪个 | 例子 |
|---|---|---|
| 技术 / 研究 / 算力 / 架构 | `dark-teal` | EP10 NVIDIA 护城河 |
| 人文 / 商业故事 / 产品发布 / 文化解读 | `dark-coral` | 早期 EP01-08 偏暖调的内容 |

两套主题是**镜像设计**:Typography / Layout / padding 完全一致,**只差 accent 颜色**。这意味着同一个 layout 可以在两个主题里无缝复用。

## 标准执行流程

1. **立论先行** — `/ppt-classify` + `/ppt-research-setup`(详见 `references/workflow-multi-skill.md`)
2. **scaffold open-slide 项目** — `npx @open-slide/cli@latest init` + 复制 visual-deck 主题(详见 `references/open-slide-bootstrap.md`)
3. **拆页 + 选 layout** — 按上方决策树走,每页一个 Page 组件
4. **生成 image prompts** — V2 四段式,输出到 `image-prompts.md`,用户/agent 跑 Nano Banana
5. **写 JSX** — 从 `themes/<theme>.md` 复制 helper components,从 `layouts/*.md` 复制版式模板,改成你的内容
6. **dev server 预览** — `pnpm dev`,改 JSX 实时刷新
7. **inspector 协作** — 浏览器点元素加 `@slide-comment` 批注,跑 `/apply-comments` 让 agent 改
8. **交付** — `pnpm build` 出静态站点,或 export PDF

## 关键陷阱(agent 最容易犯的)

**版式相关**:
- ❌ 用 4 个核心 layout 装不下的内容时去 hack layout(改 padding / 缩字号) → **写 inline 组件**,参考 ep10 实战
- ❌ TOC / KPI 卡片用 `array.map` 渲染 → 违反 slide-authoring 硬规则。**显式 `<Card />` × N 实例化**,inspector 才能编辑单个
- ❌ Chapter cover 双栏长度悬殊 → 改成单栏或拆页

**主题相关**:
- ❌ 一份 deck 里混用 dark-teal 和 dark-coral 章节 → 频道身份混乱。如果章节调性不同,拆成不同 deck
- ❌ 把 `Accent` 当装饰用(每页 5+ 处) → accent 是强调点,过度使用失去强调意义。一页 1-2 处,thesis 页最多 2 处

**Nano Banana / 图片相关**:
- ❌ 需要 21:9 时强行让 Nano Banana 出 → 不支持,见 ratios.md 的变通
- ❌ 用 base64 data URL 嵌图 → open-slide 用 ES module import,从 `./assets/` 引用
- ❌ scrim 调到 0.85+ 盖住整张图 → 图就白生成了

**open-slide 框架相关**:
- ❌ 加 npm 依赖 → framework 禁止,只能用 react + 标准 web API
- ❌ 在 `slides/<id>/` 里建 sibling `.tsx` 文件 → 禁止,helper 组件必须 inline 在同一个 index.tsx
- ❌ 改 package.json / open-slide.config.ts → 禁止
- ❌ 用 `overflow: hidden/scroll` 隐藏溢出 → canvas 不滚动,溢出 = 内容消失。**改文案或拆页**

## 与 open-slide 框架自带 skill 的关系

open-slide 框架本身自带 5 个 agent skill:`/create-slide` / `/slide-authoring` / `/apply-comments` / `/create-theme` / `/current-slide`。

**visual-deck 与它们不冲突,而是分层**:

| 层 | 谁负责 |
|---|---|
| **通用规则**(1920×1080 canvas、type scale 范围、anti-patterns) | open-slide 的 `/slide-authoring` |
| **绿皮火车特化**(dark-teal/coral 主题、4 个 layout、V2 prompt、Nano Banana 比例) | visual-deck(本 skill) |
| **流程编排**(scaffold / dev server / inspector 工作流) | open-slide 的 `/create-slide` + `/apply-comments` |
| **PPT 立论**(分类、研究框架、storyline 评审) | `/ppt-classify` / `/ppt-research-setup` / `/ppt-narrative-review` |

**做新 deck 时的建议路径**:
1. 先 `/ppt-classify` 定 PPT 类型
2. 启动 open-slide 项目(`/create-slide` 或手动 scaffold)
3. 写 JSX 时,**读 visual-deck 的 layouts/<选定版式>.md + themes/<选定主题>.md**,从模板复制粘贴
4. inspector 反馈用 `/apply-comments`

## v0.x → v1.0 迁移指南

如果你有用 v0.x 做过的旧 deck:

1. **HTML 文件**:逐页转 JSX,参考 `layouts/` 里的对应版式
2. **CSS 变量**:从 `var(--accent)` 换成 `palette.accent`(hex 直写或用 `var(--osd-accent)`)
3. **背景图**:`background: url(../images/...)` → ES module import + CSS gradient(scrim 不再烘焙)
4. **notes-map.js**:废弃,改成每页 `<aside data-speaker-note>` 内联
5. **build.js**:废弃,改用 `pnpm dev` / `pnpm build`
6. **单位**:pt × 2.667 = px(safe-zone-spec.md 末尾有完整对照表)

参考实战:ep10 NVIDIA 护城河 deck 已完成 16 页迁移,源码可对照(`~/Github/greentrain-studio/main/episodes/ep10-ai-ppt/open-slide-deck/`)。

## PPTX Roadmap

v1.0 **不输出 .pptx 文件**。这是有意识的取舍——绿皮火车实际工作流(YouTube + 现场演讲)不需要 .pptx,只需要 deck 在浏览器里看得清。

**未来计划**:把 v0.x 时代的 HTML→pptxgenjs 管线封装成 **open-slide 的 export-pptx 命令**,贡献到 open-slide 上游。届时任何用 open-slide 的 deck(包括非绿皮火车用户)都能受益,而 visual-deck 自己不需要维护这套管线。

时间表未定,需要时再开工。

## 扩展约束(给未来的自己)

**新增 layout 之前必须回答**:
1. 现有 4 个版式为什么不够?举一个具体 slide 说不通的场景
2. 新版式的 USE WHEN / DO NOT USE WHEN 分别是什么?
3. 它真的可复用,还是只在一个 deck 出现过?(只用一次就别抽象,直接 inline 在 deck 里写)

**新增 theme 之前必须回答**:
1. dark-teal / dark-coral 为什么不够?
2. 新 theme 与现有两个的镜像关系是什么(palette 哪些不变,哪些变)
3. 这套主题的 "适用调性" 在频道里有几集会用?(一集就别加)

扁平堆叠 layout / theme 会让 agent 选不到对的——**信息结构 ≫ 选项数量**。

## 快速开始

```bash
# 1. scaffold
npx @open-slide/cli@latest init my-deck --use-pnpm --locale zh-CN --no-git
cd my-deck

# 2. 复制主题(从 visual-deck 仓库)
cp ~/Github/skills/visual-deck/themes/dark-teal.* themes/

# 3. 跑 dev
pnpm dev   # → http://localhost:5173

# 4. 写第一张 slide(参考 references/open-slide-bootstrap.md)
mkdir slides/<deck-id>
# ... 见 bootstrap 文档第 4 步
```

完整步骤见 `references/open-slide-bootstrap.md`。
