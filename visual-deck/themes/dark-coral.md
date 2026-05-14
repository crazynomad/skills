---
name: Dark Coral
description: 绿皮火车人文/商业故事章节主题——暖色调,情感、洞察、温度感。
---

# Dark Coral

人文叙事 / 商业故事 / 洞察分享类章节的默认主题。暖色 coral 表达"温度、共情、人物",与冷静 gold 副点缀互补。从 visual-deck 0.x 的 dark-coral.css 移植,适配 open-slide 1920×1080 画布。

**与 dark-teal 的唯一差别**: `accent` 由冷色 teal `#76C7C0` 换成暖色 coral `#FF6B47`,其他全部保持一致。这是一对**镜像主题**——切换不破坏既有 layout/typography 决策,只改情绪基调。

## Palette

| Role     | Value     | Notes                                                |
| -------- | --------- | ---------------------------------------------------- |
| bg       | `#0A0A0A` | 底色 void black                                      |
| text     | `#F5F2EB` | 正文 warm off-white                                  |
| accent   | `#FF6B47` | 主点缀 warm coral——情感强调,人物 / 故事的高亮       |
| accent2  | `#D4A574` | 副点缀 warm gold                                     |
| muted    | `#8A8A8A` | 次要文字                                             |
| dim      | `#6B6B6B` | 最弱文字                                             |
| faint    | `#5A5A5A` | 更弱                                                 |
| cool     | `#76C7C0` | 应急冷色(罕用,可对照 dark-teal 的 hot 表达"反例") |

## Typography

与 dark-teal **完全一致**——字体栈、字号档位、letter-spacing 同。同一份 layout 切换主题不该改字号。

- Display + Body 字体: `"Microsoft YaHei", "微软雅黑", Helvetica, Arial, sans-serif`
- Weight: bold 700, normal 400, light 300

| 用途      | 像素 |
|---|---:|
| Hero title | 160 |
| Section heading | 85 |
| Page heading | 60 |
| Body | 32 |
| Caption/label | 24 |
| Source | 21 |

## Layout

与 dark-teal 完全一致(padding / 图位 / letter-spacing 都同)。

## Fixed components

把 `dark-teal.md` 里的组件**全部复制**,只把 `Accent` 里的颜色 `#76C7C0` 改成 `#FF6B47`、把 `TopRow` 默认 `rightColor` 改同款即可。

### Accent(暖色版)

```tsx
const Accent = ({ children }: { children: React.ReactNode }) => (
  <span style={{ color: '#FF6B47' }}>{children}</span>
);
```

### TopRow(同 dark-teal,只换 rightColor 默认值)

```tsx
const TopRow = ({ left, right, leftColor = '#6B6B6B', rightColor = '#FF6B47' }: {
  left: React.ReactNode; right: React.ReactNode;
  leftColor?: string; rightColor?: string;
}) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <p style={{ fontSize: 24, letterSpacing: 8, fontWeight: 300, color: leftColor, margin: 0 }}>{left}</p>
    <p style={{ fontSize: 24, letterSpacing: 5, fontWeight: 300, color: rightColor, margin: 0 }}>{right}</p>
  </div>
);
```

`Title` / `BottomRow` 直接复用 dark-teal 的版本——它们不带 accent。

## Motion

同 dark-teal: **静态**为主,需要时只允许 `fadeIn` 0.4s。

## Aesthetic

夜晚电台、播客封套、纸质杂志专栏的暖光。**有温度但不煽情**。Coral 是火光,不是霓虹——不要把它当"亮色"用,它是 ember(灰烬里的余温),所以 deck 里出现频率应该**比 dark-teal 的 teal 更少**——一页 1-2 处足矣,过多 coral 反而失去情绪强度。

## When to pick this theme

- 人物故事、行业洞察、文化解读、产品发布(有 narrative arc)
- 与观众情感建立连接的章节
- 商业故事("OpenAI 是怎么炼成的"、"程序员的中年危机")

如果是**研究简报 / 技术架构 / 算力分析**,换用 `dark-teal`——冷色更匹配"被审视"的姿态。
