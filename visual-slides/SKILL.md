---
name: visual-slides
description: Generate "image + text" style visual decks directly in Google Slides via the gws CLI. Uses a hand-authored master template with {{placeholders}}, then injects content via slides.batchUpdate (replaceAllText + replaceAllShapesWithImage) and references Nano Banana backgrounds uploaded to Drive. Use when the deck must live in Google Slides (shareable link, comments, collaboration) AND the layout language matches the visual-deck design system. NOT for offline .pptx delivery — use visual-deck for that.
version: 0.1.0
---

# visual-slides — 视觉版 Google Slides 注入器

`visual-deck` 的"亲戚":同一套视觉设计语言(安全区、V2 image prompt、Nano Banana 暗罩),但输出目标从本地 `.pptx` 文件换成**线上 Google Slides 文档**。技术路线完全不同——不再走 HTML→PPTX,改走"人工模板 + `gws slides batchUpdate` 注入"。

## 何时触发

**适用**:
- 最终交付必须是 Google Slides URL(协作评论、版本历史、内嵌网页)
- 同一份模板要重复填不同数据(月报、客户方案的 N 个版本、Newsletter)
- 团队里至少有一个人愿意手工维护 Drive 上的母板 deck

**不适用**:
- 离线 PPT 文件交付 → 用 `visual-deck`
- 一次性、不复用的 deck → 用 `pptx` skill,模板维护成本不值
- 视觉精度要求极高(字距、阴影、复杂图形) → Slides API 表现力弱,选 `visual-deck`
- 母板没人维护 → 这个 skill 等于"没有图纸的注入器",拒做

## 三条硬约束(从 visual-deck 继承)

这三条不变,踩过的坑同样适用:

### 1. 文字只进安全区,溢出走 speaker notes
- 每张 slide 都有图像安全区(暗罩区/留白区),占位符**必须在安全区内**
- 装不下时:**不许缩字号**,把溢出灌进 `{{pN-notes}}`(对应该页演讲者备注)
- 安全区比例见 `references/safe-zone-spec.md`

### 2. Image prompt 必须 V2 四段式
- 描述 / Composition / Style / Do not include 四段齐全
- 安全区写死在 Composition 段
- 色彩 token + hex 双写
- 详见 `references/image-prompts-v2.md`

### 3. Nano Banana 比例有限
- 16:9 / 4:3 / 1:1 / 3:4 / 9:16,**不支持 21:9**
- Slides 默认页 16:9,绝大多数情况固定 16:9 出图就行
- 见 `references/nano-banana-ratios.md`

## 第四条硬约束(Slides 特有)

### 4. 占位符必须全 deck 唯一,图片必须 Drive 共享可读

- **`replaceAllText` 是全 deck 扫描**——两页都写 `{{title}}` 会被同时替换。占位符**必须**编号:`{{p1-title}}` / `{{p2-title}}`,见 `references/placeholder-naming.md`
- **`replaceAllShapesWithImage` 拉的是 image URL**——Slides 服务端去 fetch,所以图片在 Drive 里必须设置 `anyone with link can view`。inject.py 会自动加这个权限,完成后**不会撤销**。私密内容请用专用 Drive 文件夹隔离

## 完整 Pipeline

```
                  ┌─── 母板 Slides deck (Drive) ────┐
                  │ 含 {{pN-title}} / {{pN-img-X}}  │
                  └────────────┬────────────────────┘
                               │
                  content-plan.json ── 内容 + 模板 ID
                               │
   image-prompts.md            │
        │                      │
        ▼ (Nano Banana)        │
   images/*.png                │
        │                      │
        ▼ (scrim_bake.py)      │
   images/*-scrimmed.png       │
        │                      │
        ▼                      ▼
        └───────► inject.py ──────────► 线上 Slides deck
                     │
                     ├─ gws drive files copy (复制母板)
                     ├─ gws drive files create (上传图片 × N)
                     ├─ gws drive permissions create (公开可读)
                     └─ gws slides presentations batchUpdate
                            (replaceAllText + replaceAllShapesWithImage)
```

## 文件角色

| 文件 | 作用 | 是否改 |
|---|---|---|
| `scripts/inject.py` | 主编排器:复制模板→上传图→batchUpdate→输出 URL | **不改** |
| `scripts/scrim_bake.py` | Pillow 把 scrim 暗罩烘进 PNG(Slides 不渲染 gradient) | **不改** |
| `scripts/validate_plan.py` | 在 inject 前校验 content-plan.json 的占位符/路径 | **不改** |
| `references/template-spec.md` | **必读** · 如何在 Slides UI 里手工做母板 | 不改 |
| `references/placeholder-naming.md` | **必读** · `{{pN-...}}` 占位符语法 | 不改 |
| `references/safe-zone-spec.md` | 安全区%(同 visual-deck,加 Slides EMU 备注) | 不改 |
| `references/image-prompts-v2.md` | V2 prompt 四段式 | 不改 |
| `references/nano-banana-ratios.md` | 出图比例约束 | 不改 |
| `references/gws-cli-cheatsheet.md` | gws 安装/登录 + skill 实际调用的命令 | 不改 |
| `templates/content-plan.example.json` | content-plan 的标准 schema | 复制后填 |
| `examples/minimal/` | 2 页可跑的最小例子 | 参考 |

## 占位符约定(核心)

| 类型 | 写法 | 替换机制 |
|---|---|---|
| 文本 | `{{p1-title}}` / `{{p3-bullet-2}}` | `replaceAllText` |
| 图片 | 在形状里写 `{{p1-img-hero}}` | `replaceAllShapesWithImage`(整形状被替换成图) |
| 备注 | `{{p1-notes}}`(放在 speaker notes 区域) | `replaceAllText`(scope: NOTES) |

**为什么不用 objectId**? 因为 objectId 在复制模板时不稳定(Slides 会重新生成),而**文字匹配在复制后依然成立**——母板里写什么,副本里就还是什么。这是路线 B 的核心妙处。

## 标准执行流程

1. **首次:用户准备母板 deck**(只做一次)
   - 在 Drive 新建 Slides 文档,按 `references/template-spec.md` 设计版式
   - 每个文本占位符写 `{{pN-xxx}}`,图片占位符写一个形状(rectangle)内含 `{{pN-img-xxx}}`
   - 记下 deck ID(URL 里 `/d/<这段>/edit`)

2. **每次生成:填 content-plan.json**
   - 从 `templates/content-plan.example.json` 复制
   - 填 `templateDeckId` + `driveImageFolderId` + 每页的 text/image 映射

3. **生成 image prompts**(V2 四段式)
   - 输出到 `image-prompts.md`,交给用户跑 Nano Banana

4. **scrim 烘焙**
   - `python scrim_bake.py images/bg-01.png 0.55 images/bg-02.png 0.65 ...`

5. **lint plan**
   - `python validate_plan.py content-plan.json` — 检查占位符是否全 deck 唯一、图片路径是否存在

6. **干跑(推荐先做)**
   - `python inject.py content-plan.json --dry-run` — 打印 batchUpdate 请求 JSON,不真改 Drive

7. **真跑**
   - `python inject.py content-plan.json`
   - 输出最终 `https://docs.google.com/presentation/d/...` URL

## 关键陷阱(Claude 自己最容易犯的)

**占位符相关**:
- ❌ 全 deck 写 `{{title}}` —— `replaceAllText` 会把所有页同时替换。必须 `{{p1-title}}` / `{{p2-title}}`
- ❌ 占位符里带中文 —— `replaceAllText` 走 UTF-8 没问题,但中文 + 空格 + 标点很容易拼错。坚持 ASCII kebab-case
- ❌ 在母板里把占位符做了花字效果 —— 替换后样式保留,中文/数字会被强行套上原占位符的字体。占位符必须用 deck 默认正文样式

**图片相关**:
- ❌ 用 base64 data URL —— Slides API **不接受**
- ❌ 私人 Drive 文件直接拉 —— Slides 服务器 fetch 不到,replaceAllShapesWithImage 报 INVALID_ARGUMENT。inject.py 会自动改成 `anyone with link can view`,但要意识到这个安全副作用
- ❌ 图形状里写多行文字占位符 —— Slides 把整个形状看作占位,`{{p1-img-hero}}` 必须**独占一个形状**,周围不能有其他文字

**模板相关**:
- ❌ 用 Slides "新建空白演示文稿"的母板 —— 它自带 placeholder layout,跟我们的 `{{}}` 系统打架。建议直接 `新建 → 空白`,自己摆所有元素
- ❌ 模板改了字号/位置 → 立即触发 inject —— 模板改动后**先复制一次空跑**,确认占位符还能被找到再批量跑生产

**gws 相关**:
- ❌ 没装 gws / 没登录 —— inject.py 第一步会探测,但记得 `references/gws-cli-cheatsheet.md` 里有 `gws auth login` 步骤
- ❌ 把 `templateDeckId` 写成 URL 而不是 ID —— Drive 文件 ID 是 URL 里 `/d/<ID>/` 那一段,不是整个 URL

## 与 visual-deck 的关系

| | visual-deck | visual-slides |
|---|---|---|
| 输出 | 本地 `.pptx` | 线上 Google Slides URL |
| 渲染 | HTML→PPTX(pptxgenjs) | Slides API batchUpdate |
| 模板 | `templates/layouts/*.html`(代码资产) | Drive 上手工 deck(非代码资产) |
| 协作 | 文件传输 | 实时协作 / 评论 |
| 一次性 | ✅ 快 | ❌ 模板维护成本 |
| 重复填充 | ❌ 每次重新跑 build | ✅ 模板一份多用 |
| 视觉精度 | 高 | 中 |
| 复用的资产 | — | image-prompts-v2 / safe-zone / nano-banana-ratios / scrim-bake |

**选哪个的口诀**:**一次性、高精度、要离线文件 → visual-deck;要协作、可复用、要 URL → visual-slides**。两者共用同一套设计语言,所以从 visual-deck 出过的 deck 思路可以平移过来,反之亦然。

## 依赖

- **gws CLI** ≥ v1.0(从 [googleworkspace/cli releases](https://github.com/googleworkspace/cli/releases) 装)
- **gws 已 auth**(`gws auth login`)
- **Python 3.10+** + `Pillow`(scrim_bake.py)
- **Nano Banana** 出图通道(用户自己有)

## 快速开始

```bash
# 1. 装 gws + 登录(只做一次)
# 见 references/gws-cli-cheatsheet.md

# 2. 看最小例子
cd examples/minimal
cat README.md

# 3. 用最小例子跑一次
python ../../scripts/validate_plan.py content-plan.json
python ../../scripts/inject.py content-plan.json --dry-run    # 看请求
python ../../scripts/inject.py content-plan.json              # 真跑
```
