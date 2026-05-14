# Minimal Example

两页可跑的最小例子。把它当作 visual-slides 的入门教程,**按步骤跑一次**,每一步停下来看输出长什么样。

## 你需要先准备

1. **gws CLI 已装好 + auth login**(见 `../../references/gws-cli-cheatsheet.md`)
2. **Pillow 已装**(`pip install Pillow`)
3. **Drive 上有一个母板 deck**(见 `../../references/template-spec.md`)
   - 第 1 页:HF 版式,含 `{{p1-title}}` / `{{p1-subtitle}}` / `{{p1-img-hero}}` / speaker notes 区域有 `{{p1-notes}}`
   - 第 2 页:R34 版式,含 `{{p2-title}}` / `{{p2-bullet-1}}` / `{{p2-bullet-2}}` / `{{p2-bullet-3}}` / `{{p2-img-side}}`
4. **Drive 上一个文件夹**用于装上传的图

## 第 1 步:替换 ID

打开 `content-plan.json`,把:
- `REPLACE_WITH_YOUR_TEMPLATE_DECK_ID_ABC123` → 你的母板 deck ID
- `REPLACE_WITH_YOUR_IMAGES_FOLDER_ID_XYZ789` → 你的 images 文件夹 ID

ID 是 URL 里 `/d/<这段>/edit` 或 `/folders/<这段>` 那段。

## 第 2 步:跑 validate(看错误)

```bash
python ../../scripts/validate_plan.py content-plan.json
```

第一次跑应该报:
```
2 error(s) in content-plan.json:
  - p1 image missing: images/bg-01-cover-scrimmed.png
  - p2 image missing: images/bg-02-validation-scrimmed.png
```

这是预期的——还没生成图。继续。

## 第 3 步:生成图(Nano Banana)

把 `image-prompts.md` 里的两条 prompt 复制到 Nano Banana,跑出图,保存为:
- `images/bg-01-cover.png`(16:9)
- `images/bg-02-validation.png`(3:4)

如果手头没 Nano Banana,**临时用 Pillow 造两张占位 PNG 也能让 pipeline 跑通**:

```bash
mkdir -p images && python3 -c "
from PIL import Image
Image.new('RGB', (1920, 1080), (40, 40, 60)).save('images/bg-01-cover.png')
Image.new('RGB', (768, 1024), (40, 40, 60)).save('images/bg-02-validation.png')
"
```

## 第 4 步:烘 scrim

```bash
python ../../scripts/scrim_bake.py images/bg-01-cover.png 0.55 images/bg-02-validation.png 0.62
```

输出:
```
  baked bg-01-cover.png @ alpha=0.55 -> bg-01-cover-scrimmed.png
  baked bg-02-validation.png @ alpha=0.62 -> bg-02-validation-scrimmed.png
```

## 第 5 步:再跑 validate

```bash
python ../../scripts/validate_plan.py content-plan.json
```

应该 `ok: content-plan.json`。

## 第 6 步:dry-run

```bash
python ../../scripts/inject.py content-plan.json --dry-run
```

输出会列出:
- 会复制哪份模板
- 会上传哪些图
- 完整的 batchUpdate 请求 JSON(用假 fileId 填充图片 URL)

**这一步不调 gws,不动 Drive**。是确认占位符规则、检查请求结构的最后机会。

## 第 7 步:真跑

```bash
python ../../scripts/inject.py content-plan.json
```

输出最后一行是 `done: https://docs.google.com/presentation/d/.../edit`,点进去就是生成好的 deck。

## 跑完之后

- 检查每页占位符**全部都被替换**了——如果母板里有写 `{{...}}` 但 plan 里没对应内容,会保留原占位符在 deck 上(`replaceAllText` 找不到匹配会静默跳过)
- 检查图片是否正常显示——如果显示破图,八成是 step 3 漏跑或图片 ID 没正确公开
- 检查中文字体——母板默认字体不支持中文时,会显示豆腐块

## 把这个例子改成自己的

1. 复制整个 `examples/minimal/` 到项目目录
2. 改 `content-plan.json` 的页数 + 内容
3. 改 `image-prompts.md` 写自己的 prompt
4. 在 Drive 模板里加对应页(每加一页都按 `template-spec.md` 的 checklist 走)
5. 跑 validate → dry-run → real

每次只改 plan 不动模板,模板就是真正的"一次性投资"。
