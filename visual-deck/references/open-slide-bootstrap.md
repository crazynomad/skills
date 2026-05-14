# Open-Slide Bootstrap

visual-deck v1.0 假设你在 [open-slide](https://github.com/1weiho/open-slide) 框架上工作。这份文档是"从零到第一张 slide"的速成。

## 前置依赖

- **Node.js 18+** + **pnpm**(`brew install pnpm` 或 `npm i -g pnpm`)
- 浏览器(任意现代)

## 第 1 步:scaffold 项目

```bash
cd <你的项目目录>
npx @open-slide/cli@latest init <deck-name> --use-pnpm --locale zh-CN --no-git
# 例: npx @open-slide/cli@latest init ep11-open-slide --use-pnpm --locale zh-CN --no-git
cd <deck-name>
```

`--no-git` 是因为你大概率在一个已有的 git 仓库里(比如 greentrain-studio 的某个 worktree),不想嵌套 init。

scaffold 完会有这个结构:

```
<deck-name>/
├── .agents/skills/        # open-slide 自带的 5 个 skill
├── .claude/skills/        # symlink → .agents/skills
├── slides/getting-started/  # framework 自带的 demo,可删可不删
├── themes/                # 你的主题放这里
├── open-slide.config.ts   # 别动
├── package.json           # 别动
├── AGENTS.md / CLAUDE.md  # 框架硬规则
└── ...
```

## 第 2 步:复制 visual-deck 主题

把 visual-deck 仓库里的 `themes/dark-teal.md` + `dark-teal.demo.tsx` 一对**整体复制**到当前项目的 `themes/` 目录:

```bash
cp ~/Github/skills/visual-deck/themes/dark-teal.md themes/
cp ~/Github/skills/visual-deck/themes/dark-teal.demo.tsx themes/
```

(或 `dark-coral.*` 如果用暖色主题)

## 第 3 步:启动 dev server

```bash
pnpm dev
# 默认 http://localhost:5173
```

打开浏览器,会看到 home page 列出所有 deck + 主题。点击 "主题 → Dark Teal" 能看到 demo 三页(主题预览)。

## 第 4 步:写第一张 slide

```bash
mkdir slides/<deck-id>
mkdir slides/<deck-id>/assets
```

创建 `slides/<deck-id>/index.tsx`:

```tsx
import type { DesignSystem, Page, SlideMeta } from '@open-slide/core';

export const design: DesignSystem = {
  // 从 themes/dark-teal.md 的 Palette / Typography 段落复制过来
  palette: { bg: '#0A0A0A', text: '#F5F2EB', accent: '#76C7C0' },
  fonts: {
    display: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
    body: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
  },
  typeScale: { hero: 160, body: 32 },
  radius: 0,
};

// 从 themes/dark-teal.md 的 Fixed components 复制:
const TopRow = ({ left, right }: { left: React.ReactNode; right: React.ReactNode }) => (
  // ... (粘贴自 theme markdown)
);
const Accent = ({ children }: { children: React.ReactNode }) => (
  <span style={{ color: '#76C7C0' }}>{children}</span>
);

// 从 layouts/hero-cover.md 复制 JSX 模板,改成你的内容:
const Cover: Page = () => (
  <div style={{ ... }}>
    <TopRow left="GREENTRAIN · EP11" right="2026-06-01" />
    <div style={{ marginTop: 'auto', marginBottom: 'auto' }}>
      <h1>你的标题<br />还能 <Accent>立得住</Accent> 吗?</h1>
    </div>
  </div>
);

export const meta: SlideMeta = { title: 'EP11 demo', theme: 'dark-teal' };
export default [Cover] satisfies Page[];
```

HMR < 1s,改 JSX 浏览器自动刷新。

## 第 5 步:加图

把 Nano Banana 跑出来的 PNG 放进 `slides/<deck-id>/assets/cover.png`,然后:

```tsx
import coverBg from './assets/cover.png';

const Cover: Page = () => (
  <div style={{
    background: `linear-gradient(rgba(10,10,10,0.55),rgba(10,10,10,0.55)), url(${coverBg}) center/cover, #0A0A0A`,
    // ... 其他 style
  }}>
    ...
  </div>
);
```

scrim 用 CSS gradient——**不再需要烘焙 PNG**(visual-deck 0.x 的 scrim-bake.js 已被 CSS 替代)。

## 第 6 步:出 deck

```bash
# 静态站点:
pnpm build
# → dist/ 目录,部署到 Vercel / Cloudflare Pages / Netlify

# Inspector + agent 协作改:
# 浏览器点 "检查" → 点元素 → 写批注 → 回到 Claude Code 跑 /apply-comments
```

## 常见问题

### Q: pnpm dev 启动慢/失败?
A: 第一次 `pnpm install` 拉 472 个包(约 22 秒);若卡住检查 npm registry。

### Q: 改了 themes/dark-teal.md 在浏览器里看不到效果?
A: themes/.md 是 agent 的参考文档,**不会被 framework runtime 直接读取**。要改主题,改 `themes/dark-teal.demo.tsx`(主题预览)和你的每个 slide 顶部的 `design` const(实际主题应用)。

### Q: 怎么导出 PDF?
A: open-slide v1.x 应该已有 `pnpm exec open-slide export-pdf`,具体看 framework 版本。

### Q: 我要 .pptx 怎么办?
A: v1.0 不支持。未来计划贡献到 open-slide 上游作为 export 选项(HTML→pptxgenjs)。当前替代方案:静态 URL 分享、PDF 导出、视频录屏。

### Q: open-slide 的 framework 自带 skill(`/create-slide` / `/slide-authoring`)和 visual-deck 有冲突吗?
A: 不冲突。
- 框架自带的 `/slide-authoring` 是**通用规则**(1920×1080 canvas、type scale、anti-patterns),visual-deck 不重复
- visual-deck 是**绿皮火车特化**:dark-teal/coral 主题、4 个 layout 词汇、V2 image prompt 规范、Nano Banana 比例。在框架的 generic 之上加 channel-specific 的 opinionated 选择
- 写 slide 时**两边都参考**:先看 visual-deck 的 layout 决策树,选定后看 slide-authoring 的硬规则确保不破契约
