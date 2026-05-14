# Layout: Thesis(居中陈述)

全幅背景 + 居中大字 thesis 陈述。绿皮火车 deck 里"全片核心论点 / 收尾金句 / 反问页"用这个。

## 何时用

- Deck 的核心 thesis 页(整本 deck 的一句话答案)
- 收尾的反问 / 留给观众的话
- 章节内的"金句独占一页"时刻(每个章节最多一个)
- 单一中心论点,**没有**对比/列表/数据需要展示

## 不该用

- 内容页(有 3+ 条要点)
- 章节扉页(用 chapter-cover)
- 短句宣言(用 hero-cover,thesis 比 hero 更"居中、神圣化")

## hero-cover vs thesis 的区别

| | hero-cover | thesis |
|---|---|---|
| 对齐 | 左对齐 | **居中** |
| 文字位置 | 弹性(top/bottom 留白) | **画面绝对中心** |
| 标题字号 | 160 | 160(可上探到 180) |
| 上下留白 | 信息平衡 | 大量留白突出独占感 |
| 副标题 | 在标题下,左对齐 | 在标题下方 128px,**居中** |
| 何时用 | 封面、章节边界 | 全片论点、收尾金句 |

## 视觉预算(1920×1080)

```
padding 112 / 128 / 96 / 128
usable height = 872

top row:                            40px
flex auto top space:               ~80px
thesis (×2 lines):                 384px  (160 × 1.2 × 2)
gap to subtitle:                   128px
subtitle (×2 lines):               105px  (35 × 1.5 × 2)
flex auto bottom space:            ~80px
bottom row:                         21px
────────────────────────────────
total ≈ 838 px ✅ (fits 872,只剩 34px 余量,精确控制)
```

⚠️ thesis 的视觉预算是 4 个 layout 里**最紧的**——因为"居中"意味着不能用 marginTop 调位置,而要用 flex justify-center 把整块推到中央。如果 thesis 超过 2 行,会从中心向上挤压,造成顶部 top row 被覆盖。

## JSX 模板

```tsx
import bgImage from './assets/thesis-bg.png';

const Thesis: Page = () => (
  <div style={{
    width: '100%', height: '100%',
    background: `linear-gradient(rgba(10,10,10,0.55), rgba(10,10,10,0.55)), url(${bgImage}) center/cover no-repeat, #0A0A0A`,
    color: '#F5F2EB',
    fontFamily: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
    padding: '112px 128px 96px 128px',
    display: 'flex', flexDirection: 'column', boxSizing: 'border-box',
  }}>
    <TopRow left="RESEARCH BRIEF · THESIS" leftColor="#76C7C0" right="32 / 34" rightColor="#6B6B6B" />

    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      textAlign: 'center',
    }}>
      <h1 style={{ fontSize: 160, fontWeight: 700, lineHeight: 1.2, margin: 0, maxWidth: 1650, color: '#F5F2EB' }}>
        巅峰 与 背叛 <Accent>同步</Accent>，<br />
        因为护城河 在 <Accent>换码头</Accent>。
      </h1>
      <p style={{ fontSize: 35, color: '#D4A574', letterSpacing: 5, marginTop: 128, fontStyle: 'italic', lineHeight: 1.5 }}>
        从 Ch1 的悖论 到 Ch6 的仪表盘，<br />
        34 页走到这里。
      </p>
    </div>

    <BottomRow left="The Thesis" right="CLOSE · 01/03" />
  </div>
);
```

## 关键参数说明

| 部分 | 数值 | 为什么 |
|---|---|---|
| Container `flex: 1` + `justifyContent: 'center'` | 把 thesis 推到画面绝对中央 | hero-cover 用 `marginTop: 'auto'`,thesis 用 flex center,因为后者要"居中"不是"弹性留白" |
| Thesis `maxWidth: 1650` | 防止超宽换行 | 1920 - 270 padding = 1650 |
| `textAlign: 'center'` | 文字居中 | thesis 必须居中,左对齐会破坏神圣感 |
| Subtitle `marginTop: 128` | 副标题与主 thesis 大距离 | 强呼吸,让 thesis 独自占据视觉中心 |
| Accent 出现 2 次 | 一句话里**最多 2 个 accent**,标定 thesis 的两个关键变量 | 超过 3 个就失去强调意义 |

## 变体: 反问页(Case Closed 收尾)

ep10 slide34 用类似版式,但有几处不同:

- Top 之下加一个 eyebrow 块 `研究者姿态 · THE VERDICT WE DON'T GIVE` + 一段说明
- thesis 部分换成大数字/时间(`2028–2029 见`),字号上探到 192px
- 加 italic subtext "到时候,我们 回来 检验。"

参考 ep10 slide34 实现。本质上是 thesis 的"开场白 + 大字 + 余韵"三段变体。

## 常见错误

- ❌ Thesis 超过 2 行:必须改文案,不要靠缩字号塞下
- ❌ Subtitle 字号过大(>50):会和 thesis 抢镜,subtitle 应该明显"低一档"
- ❌ Subtitle 不用 italic:看起来像 thesis 的延续,而不是注脚
- ❌ Accent 超过 2 次:thesis 一句话强调 2 个变量,3 个就是"什么都重要 = 什么都不重要"
- ❌ 加 footer 列表 / footnote / source:thesis 页应该绝对干净,引用放上一页

## 实战参考

ep10 slide32(Thesis: 巅峰与背叛同步)、slide34(Case Closed: 2028-2029 见)
