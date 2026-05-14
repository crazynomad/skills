# 占位符语法 (Placeholder Naming)

> Slides API 的 `replaceAllText` 是**全 deck 扫描 + 精确匹配**。占位符规则是这套 skill 的合同——违反就一定出 bug,而且 bug 很隐蔽(替换跨页)。

## 文本占位符

### 语法

```
{{p<页码>-<key>}}
```

- 双花括号 `{{...}}`,内容**全 ASCII**,kebab-case
- `<页码>` 是十进制数(1, 2, 10, 27)
- `<key>` 是该页内的标识,小写字母 + 数字 + 短横线

### 例子

| 字段 | 占位符 |
|---|---|
| 第 1 页主标题 | `{{p1-title}}` |
| 第 1 页副标题 | `{{p1-subtitle}}` |
| 第 3 页第二条 bullet | `{{p3-bullet-2}}` |
| 第 7 页 KPI 数字 A | `{{p7-stat-a-value}}` |
| 第 7 页 KPI 标签 A | `{{p7-stat-a-label}}` |

### 三条铁律

1. **页码不能省**——`{{title}}` 没编号会被 N 页同时替换,几乎一定出错
2. **key 不许有中文/空格/标点**——Slides 网页编辑器偶尔会把"{{中文}}"拆 token,匹配不到
3. **大小写敏感**——`{{p1-Title}}` 和 `{{p1-title}}` 是两个不同占位符,`matchCase: true`

## 图片占位符

### 语法

```
{{p<页码>-img-<key>}}
```

注意中间多一个 `-img-` 区分,这样 `validate_plan.py` 能从语法上知道这是图片槽位。

### 用法

在母板里**画一个矩形(rectangle)**,矩形里**只写**这一个占位符字符串,不要别的内容(包括空格、标点)。`inject.py` 会用 `replaceAllShapesWithImage` 把整个矩形替换成图。

| 场景 | 占位符 | 矩形尺寸建议 |
|---|---|---|
| HF 全幅 hero 背景 | `{{p1-img-hero}}` | 720pt × 405pt(整页) |
| R34 右侧竖图 | `{{p4-img-side}}` | 304pt × 405pt |
| 三栏并列里第二张图 | `{{p9-img-2}}` | 240pt × 240pt 等 |

### 一条铁律

矩形里**只有占位符,没有其他内容**。`replaceAllShapesWithImage` 用 `containsText.text` 整字符串匹配——矩形里多一个空格、多一行回车,匹配都会失败。

## 备注(speaker notes)占位符

### 语法

```
{{p<页码>-notes}}
```

### 用法

在母板的**每一页 speaker notes 区域**(View → Show speaker notes)里粘一行 `{{pN-notes}}`。`inject.py` 会通过 `replaceAllText` 把它替换——`replaceAllText` 的扫描范围**包含 notes 页**,所以不需要特殊参数。

如果一页不需要 notes,可以**在母板里不放占位符**——`replaceAllText` 找不到匹配会静默跳过,不报错。

## content-plan.json 映射规则

```json
{
  "slides": [
    {
      "page": 1,
      "text": {
        "title": "重塑荣联汽车数智化",   // -> {{p1-title}}
        "subtitle": "2026 Q2 战略评审"   // -> {{p1-subtitle}}
      },
      "image": {
        "hero": "images/bg-01-scrimmed.png"  // -> {{p1-img-hero}}
      },
      "notes": "口播补充..."              // -> {{p1-notes}}
    }
  ]
}
```

JSON 里的 key 是"裸"key(不带 `pN-` 前缀,不带 `img-`),`inject.py` 自动拼好完整占位符。

## 命名建议(给设计模板的人)

| 场景 | 建议 key |
|---|---|
| 主标题 | `title` |
| 副标题 | `subtitle` |
| eyebrow / 上方小标签 | `eyebrow` |
| 主段落 / lede | `lede` |
| bullet 条目 | `bullet-1` / `bullet-2` / `bullet-3` |
| 数据数字 | `stat-1-value` / `stat-1-label` |
| 时间轴节点 | `step-1-time` / `step-1-title` / `step-1-body` |
| 来源/出处 | `source` |
| 章节序号 | `section-no` |
| Hero 背景 | `img-hero` |
| 主图(R34/L34) | `img-side` |
| 并列图 | `img-1` / `img-2` / `img-3` |

跨页**保持同名**——不同页都叫 `title`,自动通过 `pN-` 前缀区分,模板维护更容易。
