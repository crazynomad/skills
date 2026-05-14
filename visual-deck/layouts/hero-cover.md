# Layout: Hero-Cover (HF · Hero-Fill)

全幅背景图 + 大标题 + 副标题。绿皮火车 deck 里**封面、章节边界、收尾**都用这个。

## 何时用

- Deck 第一页(封面)
- Deck 最后一页(留给观众的金句 / "Case Closed" 类)
- 单页 thesis 陈述(全片中心论点)
- 没有需要"对比"、"逐条说"、"流程"的页

## 不该用

- 内容页(每页至少 3+ 条要点)→ 用 takeaway 或自建多栏 layout
- 章节扉页(需要章节号 + 两栏说明)→ 用 chapter-cover
- 纯数字 KPI 页 → 用 stats-grid

## 视觉预算(1920×1080)

```
padding 112 / 128 / 96 / 128
usable height = 1080 - 112 - 96 = 872

top label row:         24px × 1 line + 16px gap   = 40px
prelude / eyebrow:     37px × 1 line + 26px gap   = 63px
hero title (×2 lines): 160 × 1.15 × 2             = 368px
subtitle (×1 line):    43px × 1 + 26px top gap    = 69px
bottom row:            21px × 1 line              = 21px
─────────────────────────────────────────────────
total estimate:                                     561 px ✅ (fits 872)

剩余 ~310px 是为图像气口、不期而至的中文换行预留
```

## JSX 模板(粘贴到 `slides/<id>/index.tsx`)

需要先在 slide 顶部 import 一张背景图:
```tsx
import bgImage from './assets/cover.png';
```

主题已经定义了 `TopRow` / `BottomRow` / `Title` / `Accent`(从 `themes/<theme>.md` 复制),下面 layout 就直接调用:

```tsx
const Cover: Page = () => (
  <div style={{
    width: '100%', height: '100%',
    background: `linear-gradient(rgba(10,10,10,0.55), rgba(10,10,10,0.55)), url(${bgImage}) center/cover no-repeat, #0A0A0A`,
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
      <p style={{ fontSize: 43, color: '#D4A574', lineHeight: 1.4, margin: '26px 0 0 0' }}>
        一份在 史上最佳财报 与 最大客户集体造反 之间 写的研究简报
      </p>
    </div>

    <BottomRow left="FY26 Q4 · AGENTIC INFLECTION" right="" />
  </div>
);
```

## 关键参数说明

| 部分 | 数值 | 为什么 |
|---|---|---|
| Scrim opacity | `rgba(10,10,10,0.55)` | 0.55 是稀疏文字页档位;密集页加到 0.62-0.7 |
| Hero `fontSize` | 160 | 主题 type-scale 推荐;不超 200,否则中文换行后撑爆 |
| Hero `lineHeight` | 1.15 | 中文紧间距;英文可放到 1.05 |
| Prelude `letterSpacing` | 5px | 拉开做"档案感";中文 prelude 也用,但中文字之间会显得太散,务必只用英文 prelude |
| Subtitle `color: accent2` | gold (`#D4A574`) | 副点缀色,而非 accent——不抢主标题风头 |

## 常见错误

- ❌ 标题撑到 3 行:1920×1080 的 hero 应该≤2 行。如果中文 3 行说明文案太长,**改文案,不改字号**
- ❌ 用 emoji 替代 accent 颜色:emoji 在 1920×1080 渲染会有边缘锯齿,在投影/视频里更糟糕
- ❌ scrim 调到 0.8 盖住整张图:图就白生成了,等于纯色底
- ❌ 不放 prelude 直接上 hero:hero 上面留白会显得头重脚轻,加一行 37px 的灰色英文 prelude 是最便宜的"档案感"补救

## 实战参考

- ep10 slide01(Cover)、slide32(Thesis)、slide34(Case Closed)
- 项目路径:`~/Github/greentrain-studio/main/episodes/ep10-ai-ppt/open-slide-deck/slides/ep10-nvidia-moat/index.tsx`
