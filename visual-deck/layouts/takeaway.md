# Layout: Takeaway

章节结语 — 右侧 800px 图 + 左侧"本章带走 · 一句话"+ 一个 takeaway 金句 + NEXT 块预告下一章。

## 何时用

- 每章结束的 takeaway 页(Ch1 / Ch2 / Ch3 / Ch4 / Ch5)
- 任何需要"金句 + 过渡到下一段"的页

## 不该用

- 章节中间的内容页(用 chapter-cover 是错的)
- 没有"下一章"概念的最后一页(用 hero-cover 或 thesis)
- takeaway 长度超过 3 行(说明没"带走一句话",是带走一段;改文案)

## 视觉预算(1920×1080)

```
padding 112 / 850 / 96 / 128   (右侧 850 让位 800 竖图)
usable width  = 942
usable height = 872

top row:                       40px
mono-sub label + gap:           75px  (27px 标签 + 48px gap)
takeaway (×3 lines):           345px  (96 × 1.2 × 3)
subtext (×1 line):              52px  (37 × 1.4)
gap to NEXT block:              53px
NEXT (top border + label + text): 100px  (5+37+16+24+16+40)
bottom row:                     21px
────────────────────────────
total ≈ 686 px ✅ (fits 872)
```

## JSX 模板

```tsx
import sideImage from './assets/takeaway-bg.png';

const Ch1Takeaway: Page = () => (
  <div style={{
    width: '100%', height: '100%',
    background: `
      linear-gradient(to right, #0A0A0A 0%, #0A0A0A 55%, rgba(10,10,10,0.4) 75%, rgba(10,10,10,0) 100%),
      url(${sideImage}) right center / 800px 1080px no-repeat,
      #0A0A0A
    `,
    color: '#F5F2EB',
    fontFamily: '"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif',
    padding: '112px 850px 96px 128px',
    display: 'flex', flexDirection: 'column', boxSizing: 'border-box',
  }}>
    <TopRow left="CH1 · TAKEAWAY" leftColor="#76C7C0" right="06 / 34" rightColor="#6B6B6B" />

    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <p style={{ fontSize: 27, letterSpacing: 8, color: '#8A8A8A', margin: '0 0 48px 0' }}>
        本章带走 · 一句话
      </p>
      <h2 style={{ fontSize: 96, fontWeight: 700, lineHeight: 1.2, margin: 0, color: '#F5F2EB' }}>
        史上最佳财报<br />
        <Accent>×</Accent> 最大客户造反<br />
        <Accent>=</Accent> 一个需要被研究的悖论
      </h2>
      <p style={{ fontSize: 37, color: '#8A8A8A', fontStyle: 'italic', marginTop: 64 }}>
        下面不急着给答案。先立尺子。
      </p>
    </div>

    <div style={{ marginTop: 53, paddingTop: 37, borderTop: '5px solid #F5F2EB' }}>
      <p style={{ fontSize: 24, letterSpacing: 8, color: '#76C7C0', margin: 0 }}>
        NEXT → CH2 坐标系 + 被告发言
      </p>
      <p style={{ fontSize: 40, color: '#F5F2EB', marginTop: 16, fontStyle: 'italic' }}>
        用什么尺子量？被研究对象自己怎么说？
      </p>
    </div>

    <BottomRow left="Ch1 · 结语" right="→ Ch2 · Coordinates + Defense" />
  </div>
);
```

## 关键参数说明

| 部分 | 数值 | 为什么 |
|---|---|---|
| Takeaway `fontSize: 96` | 介于 hero(160)和 title(85)之间 | "金句"需要重量但比 hero 弱 |
| Takeaway lines | ≤3 | 超过 3 行就是"段落"不是"金句",必须改文案 |
| Subtext `fontStyle: italic` | 与 takeaway 区分 | 主+副分层;不用斜体会显得是 takeaway 的延续 |
| NEXT `borderTop: 5px solid text` | 强分隔 | 这是真正的"段落终止"线;比 1px 细线更"档案" |
| NEXT label color: accent | 强调"前进方向" | 比 takeaway 本身轻一些,但比正文重 |

## 变体: subtext-strong(全片最重的那一页)

ep10 Ch3 takeaway 是"全片最重"的页,文案分量更高。差别:

- `subtext` 改成 `subtext-strong`: `fontSize: 45`, `color: '#F5F2EB'`(主文本色而非 muted),仍 italic
- Takeaway 字号可以放到 120(虽超 hero 的 160 但仍合理)
- Top label 加 `· 全片最重 ⋆` 后缀

参考 ep10 slide19 的实现。

## 变体: 带 proof grid(数据 takeaway)

ep10 Ch4 takeaway 在 takeaway 下方加了 3 个"行为证据"卡片(10% / 80% / 数十万片)。

```tsx
// 在 takeaway 下方 + NEXT 上方插入:
<div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 27, marginTop: 27 }}>
  <ProofCell n="10%" t="OpenAI 给 Cerebras 的认股权证" />
  <ProofCell n="80%" t="Google AI 算力来自自研 TPU" />
  <ProofCell n="数十万片" t="Meta MTIA 已在生产环境" />
</div>

// 其中 ProofCell 是 inline 组件:
const ProofCell = ({ n, t }: { n: React.ReactNode; t: React.ReactNode }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
    <p style={{ fontSize: 43, fontWeight: 700, color: '#76C7C0', margin: 0 }}>{n}</p>
    <p style={{ fontSize: 21, color: '#8A8A8A', margin: 0, lineHeight: 1.4 }}>{t}</p>
  </div>
);
```

⚠️ 加 proof grid 后 subtext 必须去掉,否则视觉预算超 872px。

## 常见错误

- ❌ Takeaway 不带 accent(全白字):金句失去焦点,变成"普通断行"
- ❌ NEXT 块写超过 1 句:它是 teaser,不是 summary,1 句结束
- ❌ subtext 用 accent 颜色:会和 takeaway 内的 accent 冲突,留给真正的金句
- ❌ takeaway 用 4 行换行:**不许缩字号,改文案**

## 实战参考

ep10 slides 6(Ch1) / 11(Ch2)/ 19(Ch3 全片最重)/ 24(Ch4 带 proof grid)/ 28(Ch5)
