# Template Spec — 如何在 Slides UI 里手工做母板

> 这是路线 B 的**唯一手工资产**。模板一旦做好,后续可以多套数据复用;但模板做歪了,inject.py 救不回来。

## 一次性准备

1. 打开 [Google Slides](https://slides.google.com/),**新建空白演示文稿**(不要用任何 Google 自带模板)
2. 在 `File → Page setup` 里确认 16:9 比例(默认已是)
3. 设置默认中文字体:
   - `Insert → Text box` 画个文本框,选中,把字体换成 **思源黑体 / 阿里巴巴普惠体 / Noto Sans CJK SC** 等中文可用字体
   - 删掉文本框——后续手工新建的文本框会继承这个字体
4. 把 deck 移到一个**专用 Drive 文件夹**,文件夹里再建一个 `images/` 子文件夹(给 inject.py 上传图用)

记下两个 ID:
- **模板 deck ID**:打开 deck,URL 里 `/d/<这一段>/edit`
- **images 文件夹 ID**:打开文件夹,URL 里 `/folders/<这一段>`

## 每页的标准做法

### 1. 先放图片占位形状
- `Insert → Shape → Rectangle` 画一个矩形,大小按 layout(HF=720×405pt,R34 右半=304×405pt)
- 双击进入编辑,**只输入** `{{p<N>-img-<key>}}` 一个字符串
- 把矩形填充设置为浅灰(让占位符在编辑时可见),边框设为无
- 这是图片"槽位"——`replaceAllShapesWithImage` 会把整个矩形替换成上传的图

### 2. 再放文字占位形状
- `Insert → Text box`,画一个文本框,大小按安全区
- 在文本框里输入 `{{p<N>-<key>}}` 一行一个
- **重要**:文本框只放占位符,不要叠加 placeholder 的样式(粗体/字号/颜色由 inject 后的值决定不了——继承母板原文本框样式,所以**母板里的文本框样式就是最终样式**)

### 3. speaker notes
- `View → Show speaker notes`,在底下区域粘一行 `{{p<N>-notes}}`(可选,不需要这页就不放)

### 4. 重复以上 N 页

## 一份最小可用母板的检查清单

每页问自己:
- [ ] 占位符全 ASCII,大小写一致,页码正确?
- [ ] 图片占位是一个**纯净矩形**,矩形里**只有**占位符字符串?
- [ ] 文字占位的文本框尺寸 = 安全区(不会被占位符撑大)?
- [ ] 文字样式(字体/字号/颜色/对齐)是最终想要的样式?
- [ ] 中文样式过了**预览测试**(把 `{{p1-title}}` 改成"重塑荣联汽车数智化"看一眼,字体回退正常?字号撑爆?)

## 测试模板的两种方法

### A. 手工填一遍(强烈推荐做一次)
- 复制母板一份(`File → Make a copy`),手工把所有 `{{}}` 换成测试文本
- 看是否所有形状/文本框都能装下、字体回退正常
- 通过后,把测试副本删了,继续用原母板做生产

### B. inject.py --dry-run + --output-json
- 写一份 content-plan.json
- `python inject.py plan.json --dry-run --output-json /tmp/req.json`
- 看 `/tmp/req.json` 的请求结构是否对——但**它不告诉你母板长得怎样**,只能证明占位符语法没错

## 三个最容易踩的坑

### 1. 用了 Google 自带模板
Google 自带模板(如 "Simple Dark")自带 `placeholder` 类型的 layout(`TITLE` / `BODY` 这种)。这些 placeholder **会和 `{{}}` 占位符冲突**——Slides 编辑器有时会把占位符文本"折叠"成 placeholder 的提示文本,replaceAllText 找不到。

**对策**:坚持 `Blank → 自己摆所有元素`。

### 2. 占位符被自动断行
文本框尺寸太小时,Slides 会把 `{{p1-title}}` 折成 `{{p1-` + `title}}` 两行——`replaceAllText` 找不到带 `\n` 的匹配。

**对策**:文本框水平方向**留 30% 余量**,或者干脆把占位符前缀缩短(但本规范坚持 `pN-key` 不缩)。

### 3. 占位符里多了不可见字符
从 Slack/Word 粘贴时偶尔带 zero-width space。预览时一切正常,replaceAllText 怎么都匹配不上。

**对策**:占位符**手敲**,不要复制粘贴。如果疑似中招,用 `validate_plan.py`(它会查 plan 里的 key,但**不会查母板里的占位符**——这是 skill 的一个已知盲区,v0.2 可能加 deck audit 命令)。

## 把母板的版本号写进 content-plan.json

```json
{
  "title": "Q2 Review",
  "templateDeckId": "1aBc...",
  "templateVersion": "v1.2",       // 自己维护版本号
  "outputDeckTitle": "Q2 Review",
  ...
}
```

`inject.py` 暂时不读 templateVersion,但人工 review 时能立刻看出"这份内容是按哪版模板写的"。模板版式调整后旧 plan 不一定还能跑通,版本号是预警信号。
