# gws CLI Cheatsheet

> 仅记录 `visual-slides` skill 实际依赖的 gws 命令。完整文档见 [googleworkspace/cli](https://github.com/googleworkspace/cli)。

## 安装

```bash
# 方式 A:下载预编译 binary(推荐)
# https://github.com/googleworkspace/cli/releases
# 解压后把 gws 放进 $PATH

# 方式 B:npm
npm install -g @googleworkspace/cli

# 验证
gws --version
```

## 认证(只做一次)

```bash
# 启动 OAuth 流程
gws auth login

# 列出已登录账号
gws auth list

# 切换账号
gws auth use <email>
```

OAuth 范围需要包含 `drive` + `slides`。如果第一次跑某个命令报 403,基本是 scope 不够,重新 `gws auth login` 时勾全。

## 探查命令

```bash
# 列出 slides API 的所有方法
gws slides --help

# 看某个具体方法的参数 schema
gws schema slides.presentations.batchUpdate
gws schema drive.files.copy
gws schema drive.files.create
gws schema drive.permissions.create
```

`gws schema` 是排错神器——任何字段拼错,先用它看官方 schema。

## skill 实际跑的四种命令

`inject.py` 自动执行这些,平时不用手敲。列在这里供 debug 时手动验证。

### 1. 复制模板 deck

```bash
gws drive files copy \
  --params '{"fileId":"<TEMPLATE_DECK_ID>"}' \
  --json '{"name":"<新文件名>"}'
```

返回:`{"id":"<新 deck ID>", ...}`

### 2. 上传图片到 Drive

```bash
gws drive files create \
  --json '{"name":"bg-01-scrimmed.png","parents":["<FOLDER_ID>"]}' \
  --upload ./images/bg-01-scrimmed.png
```

返回:`{"id":"<图片 file ID>", ...}`

### 3. 把图片设为"任何人可读"

```bash
gws drive permissions create \
  --params '{"fileId":"<图片 file ID>"}' \
  --json '{"role":"reader","type":"anyone"}'
```

⚠️ **这一步会让图片在 Drive 上公开可读**。私密内容请放专用文件夹隔离。inject.py 不会自动撤销权限。

### 4. 应用 batchUpdate

```bash
gws slides presentations batchUpdate \
  --params '{"presentationId":"<新 deck ID>"}' \
  --json '{"requests":[...]}'
```

或从文件读 body(`@` 前缀):

```bash
gws slides presentations batchUpdate \
  --params '{"presentationId":"<新 deck ID>"}' \
  --json @requests.json
```

## 常见错误

| 报错 | 原因 | 对策 |
|---|---|---|
| `403 insufficientScopes` | 登录时没勾 drive/slides | 重跑 `gws auth login` |
| `404 File not found` | templateDeckId 错(粘了 URL 而非 ID) | 取 URL 里 `/d/<ID>/edit` 的 ID 段 |
| `400 INVALID_ARGUMENT: imageUrl` | 图片不是公开可读 | 检查 step 3 是否漏跑 |
| `replaceAllText` 报 0 次替换 | 占位符不匹配 | 用 `gws slides presentations get` 拉 deck 内容,grep 占位符 |
| 替换跨页 | 占位符没编号 | 改成 `{{pN-key}}` 形式 |

## debug 用的"读模板"命令

```bash
# 拉整个 deck 的内容树(很大,grep 用)
gws slides presentations get \
  --params '{"presentationId":"<DECK_ID>"}' \
  | jq '.. | .text? // empty | select(. | test("{{"))'
```

这条管线会把 deck 里所有"含 `{{`"的文本拽出来——可以一眼看清楚模板里到底有哪些占位符,是否拼写错误。

## 版本

skill 在 gws v1.x 上开发。如果未来 gws 改语法(`--json` → `--body` 之类),改 `inject.py` 里的 `gws_call()` 一处即可。
