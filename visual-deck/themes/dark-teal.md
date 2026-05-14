---
name: Dark Teal
description: 绿皮火车技术章节默认主题——冷色调,理性、克制、研究简报感。
---

# Dark Teal

技术章节 / 研究简报章节的默认主题。冷色 teal 表达"冷静、理性、客观",与暖色 gold 副点缀互补。从 visual-deck 0.x 的 dark-teal.css 移植,适配 open-slide 1920×1080 画布。

## Palette

| Role     | Value     | Notes                                             |
| -------- | --------- | ------------------------------------------------- |
| bg       | `#0A0A0A` | 底色 void black                                   |
| text     | `#F5F2EB` | 正文 warm off-white(暖白,避免冷蓝白显得医院感)  |
| accent   | `#76C7C0` | 主点缀 cool teal——技术理性的克制点缀             |
| accent2  | `#D4A574` | 副点缀 warm gold——保留温度,中和冷感              |
| muted    | `#8A8A8A` | 次要文字                                          |
| dim      | `#6B6B6B` | 最弱文字(label / source)                         |
| faint    | `#5A5A5A` | 更弱(footer / 装饰横线)                          |
| hot      | `#FF6B47` | 应急强调(`0 层` / `$26B` 等"全片最重"数字)。罕用 |

## Typography

- Display + Body 字体: `"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif`——单字体栈,中英文混排稳定
- Weight: bold 700, normal 400, light 300。**不要**用 500/600(微软雅黑没有这两档)
- Type-scale(从 visual-deck 0.x 720pt 系统按 2.667x 映射):

  | 用途      | 像素 | slide-authoring 区间 |
  |---|---:|---|
  | Hero title | 160 | 140–200 ✓ |
  | Section heading | 85 | 80–120 ✓ |
  | Page heading | 60 | 56–80 ✓ |
  | Body text | 32 | 32–44 ✓ |
  | Caption / label | 24 | 22–28 ✓ |
  | Source | 21 | (略低于 caption,用于 footer) |

## Layout

- Content padding: **112px(top) / 128px(L/R) / 96px(bottom)**——从 42pt/48pt/36pt 映射
- Alignment: 左对齐为主,封面/Thesis 类全屏页用居中
- 右侧/左侧竖图布局: 图占 800×1080px,内容区 padding 调整为 850px(为图让位)
- Letter-spacing: 大字 `-0.015em`(紧)、小标签 `0.05em–0.3em`(松,做"档案感")

## Fixed components

直接复制到使用本主题的 slide,verbatim。

### TopRow(顶部:左侧 label + 右侧 section-no)

```tsx
const TopRow = ({ left, right, leftColor = '#6B6B6B', rightColor = '#76C7C0' }: {
  left: React.ReactNode; right: React.ReactNode;
  leftColor?: string; rightColor?: string;
}) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <p style={{ fontSize: 24, letterSpacing: 8, fontWeight: 300, color: leftColor, margin: 0 }}>{left}</p>
    <p style={{ fontSize: 24, letterSpacing: 5, fontWeight: 300, color: rightColor, margin: 0 }}>{right}</p>
  </div>
);
```

### BottomRow(底部:双 label,绿皮火车每页固定)

```tsx
const BottomRow = ({ left, right }: { left: React.ReactNode; right: React.ReactNode }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
    <p style={{ fontSize: 21, color: '#6B6B6B', letterSpacing: 3, margin: 0 }}>{left}</p>
    <p style={{ fontSize: 21, color: '#6B6B6B', letterSpacing: 3, margin: 0 }}>{right}</p>
  </div>
);
```

### Title(hero 大标题,封面用)

```tsx
const Title = ({ children }: { children: React.ReactNode }) => (
  <h1 style={{ fontSize: 160, fontWeight: 700, lineHeight: 1.15, margin: 0, color: '#F5F2EB' }}>
    {children}
  </h1>
);
```

### Accent(强调短语)

```tsx
const Accent = ({ children }: { children: React.ReactNode }) => (
  <span style={{ color: '#76C7C0' }}>{children}</span>
);
```

## Motion

- **静态(static)**。这套主题主打"档案/研究简报"调性,不做动画。
- 如果你必须加,只允许 `fadeIn` 0.4s 进场,**不要**用 spring / 弹性 / 翻转。

```css
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
```

## Aesthetic

档案室美学——夜里翻研究简报的感觉。**克制、密度、冷静**。无 rounded corners、无 gradient(背景图除外)、无渐变阴影、无 emoji 装饰。所有"装饰"都来自:大段留白 + letter-spacing 拉开的英文小标签 + 一两处 accent 颜色。中文用粗黑(700)做主调,英文 label 用 light(300)拉开间距。**纸质感不是材质,是节奏**。

## Example usage

```tsx
const Cover: Page = () => (
  <div style={{
    width: '100%', height: '100%',
    background: 'linear-gradient(rgba(10,10,10,0.55),rgba(10,10,10,0.55)), url(./assets/bg.jpg) center/cover, #0A0A0A',
    color: '#F5F2EB',
    fontFamily: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
    padding: '112px 128px 96px 128px',
    display: 'flex', flexDirection: 'column', boxSizing: 'border-box',
  }}>
    <TopRow left="GREENTRAIN · EP10 · RESEARCH BRIEF" right="2026-04-20" />
    <div style={{ marginTop: 'auto', marginBottom: 'auto' }}>
      <p style={{ fontSize: 37, color: '#8A8A8A', letterSpacing: 5, margin: '0 0 26px 0' }}>
        AI INFRASTRUCTURE · MOAT ANALYSIS
      </p>
      <Title>
        NVIDIA 的护城河，<br />还 <Accent>立得住</Accent> 吗？
      </Title>
    </div>
    <BottomRow left="FY26 Q4 · AGENTIC INFLECTION" right="" />
  </div>
);
```

## When to pick this theme

- 技术解读、研究简报、行业分析(NVIDIA / 算力 / 架构)
- 需要"冷静、理性、可证伪"的感觉
- 章节较多,需要章节边界感(冷色 accent 让 Takeaway 页易识别)

如果调性是"温度、人文、商业故事",换用 `dark-coral`。
