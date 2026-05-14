# 方案 Deck 生成:多 Skill 组合工作流

`visual-deck` v1.0 只负责「把已经想清楚的内容做成视觉化 deck」。一份真正能说服客户的方案,**前面还缺两段:叙事骨架 + 素材生产**。这份文档描述从零到交付的完整链路,以及每一段该调哪个 skill。

## 全景链路

```
┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌─────────────┐
│ 1. 叙事骨架  │ → │ 2. 内容编排  │ → │ 3. 素材生产   │ → │ 4. 渲染 deck  │ → │ 5. 审计反馈  │
│ ppt-classify│   │ visual-deck │   │ nano-banana  │   │ open-slide   │   │ ppt-narr-rv │
│ ppt-research│   │ (layout 决策)│   │ pro / svg    │   │ pnpm dev     │   │ /手动自查    │
└─────────────┘   └─────────────┘   └──────────────┘   └──────────────┘   └─────────────┘
    WHY              WHAT              VISUAL            HOW                QA
```

每一段都可以独立跑,但跳过前面某段就要承担对应的"跳过代价"。

---

## 1. 叙事骨架(WHY) · `/ppt-classify` + `/ppt-research-setup`

**目的**:在打开任何编辑器之前,先把「为什么要讲这个方案、讲给谁、讲完他们该怎么动」想透。

**做什么**:
- `/ppt-classify`:判断 PPT 类型(Pitch / Research / Teaching / Narrative),决定立论框架
- `/ppt-research-setup`(如果是 Research 类):三段论框架(反共识悖论 / 结构分解 / 调查路径)+ 六问具体性诊断
- `/ppt-narrative-review`(可选):评审 storyline 结构、节奏、视觉锚点

**产出**:`thesis-setup.md`(立论文档)包含:
- 核心论点(1 句话)
- 章节边界(每章一句话定位)
- 每章预期页数和"会带走什么"

**跳过代价**:Deck 做完才发现故事线不通,整体返工。

---

## 2. 内容编排(WHAT) · `visual-deck` layout 决策树

**目的**:把立论文档的每个论点映射到具体的版式,产出 slide JSX。

**做什么**:
- 按 deck 章节拆页,**每页只讲一件事**
- 对照 `layouts/README.md` 的决策树选版式:
  - 封面 / 章节边界 / 收尾 → `hero-cover.md`
  - 章节起始(承上启下) → `chapter-cover.md`
  - 每章 takeaway 金句 → `takeaway.md`
  - 全片中心论点 / 收尾反问 → `thesis.md`
  - 其他特殊形态(TOC grid / KPI cards / 表格) → 参考 ep10 实战,写 inline component
- 在 `slides/<deck-id>/index.tsx` 里写 React 组件,每页一个 Page
- 顶部 declare `design: DesignSystem`,从 `themes/<theme>.md` 复制(默认 dark-teal)
- 用 open-slide 的 dev server(`pnpm dev`)即时预览,HMR < 1s

**产出**:`slides/<deck-id>/index.tsx` + 标记好的 `<ImagePlaceholder>` 或暂存 prompt 标记

**跳过代价**:陷入"一张图塞 8 条要点"的信息密度失控,或前后三页都是同一个版式的节奏单调。

---

## 3. 素材生产(VISUAL) · `/nano-banana-pro` + `/svg-logo-designer`

**目的**:按 image-prompts 批量生产背景图、icon、logo。

**做什么**:

| 素材类型 | 用哪个 skill | 关键约束 |
|---|---|---|
| HF 背景图(封面/章节)| `/nano-banana-pro` | V2 四段式 prompt,安全区百分比写死,色彩 token + hex 双写 |
| 800px 竖图(chapter-cover / takeaway 右图) | `/nano-banana-pro` | 3:4 或 1:1 比例,注意单侧留 void |
| 客户/合作方 logo | `/svg-logo-designer` 或 直接拿客户素材 | — |
| icon / 抽象图元 | `/svg-logo-designer`(pictorial 变体)| — |

**prompt 规范**:见 `references/image-prompts-v2.md`。**不支持 21:9**,见 `references/nano-banana-ratios.md`。

**产出**:`slides/<deck-id>/assets/*.png`

**跳过代价**:用库存图 / 随便生成会让 deck 失去视觉统一性,客户一眼就能看出"拼凑感"。

---

## 4. 渲染 deck(HOW) · open-slide dev server

**目的**:本地实时预览,出 demo URL 或静态站点。

**做什么**:

首次创建项目:
```bash
cd <project-dir>
npx @open-slide/cli init <deck-name> --use-pnpm --locale zh-CN --no-git
cd <deck-name>
# 把 visual-deck/themes/dark-teal.md 的内容复制 → 项目的 themes/dark-teal.md
# 把 visual-deck/themes/dark-teal.demo.tsx 复制 → 项目的 themes/dark-teal.demo.tsx
# 把图片素材放进 slides/<deck-id>/assets/
pnpm dev   # 默认 http://localhost:5173
```

迭代:
```bash
# 编辑 slides/<deck-id>/index.tsx
# 浏览器 HMR < 1s 自动刷新
```

交付:
```bash
pnpm build              # 出 dist/ 静态站点
# 部署 Vercel / Cloudflare Pages / Netlify
# 或 pnpm exec open-slide export-pdf  (需要 open-slide 1.x+ 支持)
```

**v1.0 的输出限制**:**不出 `.pptx` 文件**。绝大多数演讲/分享场景用静态 URL 或 PDF 已足够。

**未来路径**:如果需要 .pptx 输出,会贡献到 open-slide 上游作为新的 export 选项(HTML→pptxgenjs),不在 visual-deck 内维护。见 `references/pptx-export-roadmap.md`(如有)。

**产出**:可点开的 dev 预览 URL,或部署后的静态 deck URL。

---

## 5. 审计反馈(QA) · `/ppt-narrative-review` 思路

**目的**:交付前自查,过滤"没有叙事目的"的页。

**做什么**:
- 跑 `/ppt-narrative-review` 让 agent 评一遍 storyline 结构(可选)
- 手动逐页过(参考 ep10 经验):
  - 这张图在为哪个论点服务?说不清 → 换图或删页
  - 这条 bullet 是否只是"看起来专业"的空话(Unlock the power of...)? 是 → 删
  - 前后三页是不是同一版式? 是 → 考虑换 layout 或切镜像
  - 每张 slide 打开速读 5 秒,是否能记住**一个具体的东西**?
- 用 open-slide 的 **inspector**:浏览器点元素 → 加 `@slide-comment` 批注 → 跑 `/apply-comments` 让 agent 改

**跳过代价**:交付给客户后才发现有"漂亮但没内容"的页,口头汇报会卡壳。

---

## 速查表:哪段该调哪个 skill

| 阶段 | Skill | 触发时机 |
|---|---|---|
| 1. 叙事骨架 | `/ppt-classify` → `/ppt-research-setup`(或 narrative-setup)| 客户方案启动、还没一行 JSX 时 |
| 2. 内容编排 | `visual-deck`(layouts/ + themes/)| 有了立论,开始拆页 |
| 3. 素材生产 | `/nano-banana-pro` / `/svg-logo-designer` | JSX 骨架写完、image prompts 出来后 |
| 4. 渲染 deck | open-slide `pnpm dev` / `pnpm build` | 图齐了、内容填了 |
| 5. 审计反馈 | `/ppt-narrative-review` / inspector `@slide-comment` | 交付前 |

---

## 最小可行组合

赶时间时允许跳步,但要**自知跳了什么**:

- **最快(1-2h)**:直接 `visual-deck` 起 JSX,故事靠经验脑补,素材用已有图 → 适合内部快速分享
- **标准(半天)**:ppt-classify → visual-deck → nano-banana 批量跑图 → 手动自查 → 适合对外方案
- **完整(1-2 天)**:全链路,含 narrative-review 评审 storyline → 适合大客户正式提案、高风险场景

默认走「标准」流程。

---

## 跨集复用(themes 的真正价值)

visual-deck v1.0 的 `themes/dark-teal.md` + `dark-coral.md` 是**跨集复用的设计资产**。每集新 deck 只需:

1. 复制 `themes/<theme>.md` 内容到新项目的 `themes/`(同时复制 `.demo.tsx`)
2. 在 slide 顶部 declare `meta: { theme: 'dark-teal' }`
3. 从 layouts/ 复制粘贴需要的版式

**不要**每集重新调色 / 重新选字体 / 重新定 padding——这些是绿皮火车的"频道视觉身份",一致性比新鲜感更重要。
