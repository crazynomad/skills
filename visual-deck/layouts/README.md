# layouts/ — 绿皮火车 deck 版式词汇

可粘贴的 JSX 版式片段。从 visual-deck 0.x 的 HTML layouts 转换到 open-slide 1.0 的 React/JSX 形态。

## 4 个核心版式(v1.0 ship)

| 文件 | 用途 | 何时用 |
|---|---|---|
| [hero-cover.md](hero-cover.md) | 全幅背景 + 标题 + 副标题 | 封面、章节边界、收尾 |
| [chapter-cover.md](chapter-cover.md) | 800px 竖图 + 大章号 + 双栏 + echo | 章节扉页 |
| [takeaway.md](takeaway.md) | 800px 右图 + 金句 + NEXT 块 | 每章结语"本章带走" |
| [thesis.md](thesis.md) | 居中大字 + 副标题 | 全片论点、收尾金句 |

## 选哪个的决策树

```
问 1: 是封面 / 章节边界 / 收尾?
  是 → hero-cover
  否 → 继续

问 2: 是章节起始页(承接上一章 + 预告本章)?
  是 → chapter-cover
  否 → 继续

问 3: 是每章结束的金句(takeaway 一句话)?
  是 → takeaway(带 NEXT 预告)
  否 → 继续

问 4: 是全片中心论点 / 收尾反问 / 单页独占的金句?
  是 → thesis(居中)
  否 → 你需要的可能是「内容页」,不在 v1.0 4 个核心版式里——
        直接写 React,参考 ep10 的 TOC / Meta Finding / Three Cards 等 bespoke 版式
```

## v1.0 之外的版式(项目特化,不打包到 skill)

在 ep10 deck 里实战使用过、但**没有抽象为通用 layout** 的:

- **TOC grid**(slide02): 6 章节卡片横排,核心章高亮。用了 `<TocCard />` × 6 显式实例化
- **Meta finding cake**(slide18): 5 行表格,L5/L4 上升 teal、L3/L2 下降 gold、L1 中性。用 `<CakeRow />` × 5
- **3 stat cards**(slide33): 大数字 + label + desc 三列。用 `<StatCard />` × 3

这些是**项目特化的设计**,在 visual-deck v1.0 阶段当作"参考实现"而非"通用 layout"。如果未来发现 EP11/12 也需要类似版式,再考虑抽象上来。

源代码参考: `~/Github/greentrain-studio/main/episodes/ep10-ai-ppt/open-slide-deck/slides/ep10-nvidia-moat/index.tsx`

## 复用纪律(对 agent 的提醒)

`slide-authoring` 硬规则里有一条:
> 不许用 `array.map` 渲染重复的视觉元素;每个卡片/行/格子写成显式 `<Component />` 实例。

这条规则在 layouts/ 里也适用——不要把 chapter-cover 的双栏写成 `cols.map(...)`,要写成 `<Column ... />` × 2。否则 inspector 改一个就改了所有。
