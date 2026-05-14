# Layout: Chapter Cover

章节封面——左/右 800px 竖图 + 大章号 + 章节标题 + 双栏("本章问题"/"本章动作")+ "上章回音" echo block。绿皮火车 deck 每个章节边界用这个版式。

## 何时用

- Ch2 / Ch3 / Ch4 / Ch5 / Ch6 等章节起始页
- 任何需要"承接上一章 + 预告本章"的过渡页
- 章节较多(≥3)且需要明显的章节边界感时

## 不该用

- 整本 deck 只有 1-2 章(每章一个 cover 反而显得过度)
- 不需要章节标号(用 hero-cover 更直接)
- 短篇 deck(<10 页),每页都重要,不需要"扉页"消耗预算

## 视觉预算(1920×1080)

```
padding 112 / 850 / 96 / 128  (右侧 850px 让位给 800px 竖图)
usable width  = 1920 - 850 - 128 = 942
usable height = 1080 - 112 - 96  = 872

top row:                              24px × 1            = 40px
header (chNo + ch-title): max(192, 24+21+48×2) ≈ 192    = 192px
gap to split:                                              = 59px
split (col-label + rule + col-body × 2 lines):  ~150px   = 150px
gap to echo:                                               = 27px
echo block (label + text × 2 lines):           ~120px    = 120px
bottom row:                                                = 21px
─────────────────────────────────────────────────────────
total ≈ 609 px ✅ (fits 872, 留 263px 余量给气口)
```

## JSX 模板

```tsx
import sideImage from './assets/chapter-bg.png';

const ChapterCover: Page = () => (
  <div style={{
    width: '100%', height: '100%',
    background: `
      linear-gradient(to left, #0A0A0A 0%, #0A0A0A 55%, rgba(10,10,10,0.4) 75%, rgba(10,10,10,0) 100%),
      url(${sideImage}) left center / 800px 1080px no-repeat,
      #0A0A0A
    `,
    color: '#F5F2EB',
    fontFamily: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
    padding: '112px 128px 96px 850px',
    display: 'flex', flexDirection: 'column', boxSizing: 'border-box',
  }}>
    <TopRow left="章节封面 · SECTION COVER" leftColor="#8A8A8A" right="07 / 34" />

    <div style={{ display: 'flex', alignItems: 'baseline', gap: 75, marginTop: 37 }}>
      <p style={{ fontSize: 192, color: '#76C7C0', lineHeight: 0.85, fontWeight: 700, margin: 0 }}>
        02
      </p>
      <div style={{ flex: 1, paddingTop: 53 }}>
        <p style={{ fontSize: 24, letterSpacing: 8, color: '#8A8A8A', margin: 0 }}>
          章节 · CHAPTER
        </p>
        <p style={{ fontSize: 48, marginTop: 21, lineHeight: 1.1, fontWeight: 700, color: '#F5F2EB' }}>
          研究者的坐标系<br />+ Jensen 的四层防御
        </p>
      </div>
    </div>

    <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 75, marginTop: 59 }}>
      <div>
        <p style={{ fontSize: 24, letterSpacing: 8, color: '#8A8A8A', margin: 0 }}>本章问题</p>
        <div style={{ height: 2.7, background: '#5A5A5A', margin: '21px 0 32px' }} />
        <p style={{ fontSize: 29, lineHeight: 1.4, color: '#F5F2EB', fontWeight: 300, margin: 0 }}>
          用什么尺子量？<br />被研究对象自己怎么说？
        </p>
      </div>
      <div>
        <p style={{ fontSize: 24, letterSpacing: 8, color: '#8A8A8A', margin: 0 }}>本章两个动作</p>
        <div style={{ height: 2.7, background: '#5A5A5A', margin: '21px 0 32px' }} />
        <p style={{ fontSize: 29, lineHeight: 1.4, color: '#F5F2EB', fontWeight: 300, margin: 0 }}>
          先 立尺子 — 三坐标系<br />再 让被告发言 — Jensen 4 层原话
        </p>
      </div>
    </div>

    <div style={{ marginTop: 27, paddingTop: 21, borderTop: '2.7px solid #5A5A5A' }}>
      <p style={{ fontSize: 24, letterSpacing: 8, color: '#8A8A8A', margin: 0 }}>上章回音 · ECHO</p>
      <p style={{ fontSize: 30, color: '#D4A574', marginTop: 11, fontStyle: 'italic', lineHeight: 1.4 }}>
        "巅峰与背叛为何同步？" — 默认解错在哪里，这一章先不回答。
      </p>
    </div>

    <BottomRow left="Ch2.1 坐标系 · Ch2.2 Jensen 4 层防御" right="CHAPTER 02" />
  </div>
);
```

## 关键参数说明

| 部分 | 数值 | 为什么 |
|---|---|---|
| `padding-right: 850px` | 给 800px 竖图留 50px 气口 | 文字若贴近图边会失去呼吸感 |
| `gradient to left` | bg 在右、image 在左 | 用 CSS gradient 而不是 PNG 烘焙就能做的图像左缘渐隐 |
| 大章号 `fontSize: 192` | 视觉锚点 | 占据头部 60% 高度,让人一眼看到"第几章" |
| `lineHeight: 0.85` | 章号紧贴下文 | 默认 1.2 会显得章号飘在空中 |
| Split `gridTemplateColumns: '1fr 1fr'` | 等宽双栏 | 两个 col body 长度差异不超过 30% 时维持 1:1;否则改 2:1 |

## 镜像变体(L34 / R34)

把图放在右侧(主图在右,文字在左):
- `background` 里 `linear-gradient(to right, ...)` 反向
- `background: url(...) right center` 而非 `left center`
- `padding: '112px 850px 96px 128px'`(留左 128,留右 850)

## "全片核心"特殊章(Ch3)

当某章是"全片核心"时(ep10 的 Ch3),加 `⋆` 标记:

```tsx
// top row label 改成:
left="章节封面 · 全片核心 ⋆"

// 章号后面加星标:
<p style={{ fontSize: 192, ... }}>
  03<span style={{ color: '#D4A574', marginLeft: 16, fontSize: 96 }}>⋆</span>
</p>

// eyebrow 改成:
'章节 · CORE CHAPTER'
```

## 常见错误

- ❌ 双栏文字长度悬殊(一栏 1 句,一栏 4 句):改成单栏或拆页
- ❌ 章号超过 3 位(`100`):192px 会撑爆 800px 宽,改用 `fontSize: 128`
- ❌ 上章回音写超过 2 行:它是"回声",不是"总结",1-2 句精炼

## 实战参考

ep10 slides 7 / 12 / 20 / 25 / 29(5 个章节扉页都用同一个 helper component `<ChapterCover />`)
