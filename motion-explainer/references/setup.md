# 一次性安装

跑一遍 `uv run --script "$SKILL_DIR/scripts/preflight.py"`,按输出的 NO-GO 项对照下面修。

---

## 1. gflow 登录(必须)

```bash
uv tool install gflow-cli          # 或 uv tool upgrade gflow-cli
gflow auth login --browser chrome  # macOS 必须 --browser chrome
```

登录完 **等 ≥5 秒,然后 Cmd+Q 退出整个 gflow 的 Chrome 实例** —— cookies 在浏览器
进程退出时才异步落盘,关窗口不等于退出。

`gflow auth status` 的 `cookies_present: True` **只查文件存在,不代表会话有效**。
真要确认就跑 `preflight.py --probe-auth`(它会做一次免费的图像生成来实测)。

**反过来也会骗人:`gflow auth login` 报失败不代表真失败。** 实测 2026-07-27:
登录流程末尾的自检撞了 `ConnectError`,打印
"Could not verify the Flow session — this is often a network problem",
但 cookies 其实已经落盘、会话完全可用。**别信它的自检,用免费图像实测**:

```bash
uv run --script "$SKILL_DIR/scripts/preflight.py" --probe-auth
```

会话是 ~24 小时滚动的:用它会续期,闲置会死。没有 refresh 命令,过期只能重登。

---

## 2. vox(旁白)

已装则跳过。`vox --version` 能出版本即可。

**必须先把要用的模型规格拉到本地缓存。** `narrate.py` 默认强制
`HF_HUB_OFFLINE=1`,因为实测:模型已缓存时离线跑一条只要约 1.8 秒,而不加这个
变量,HuggingFace 的联网检查会**无限期挂住** —— 十分钟不出一个字符,没有任何提示。

```bash
vox speak "warm up" -m large -o /tmp     # 拉 large(1.7B,约 2.9G)
```

可选:词级字幕需要一个单独的强制对齐模型。不装的话字幕退化成"整块一条 cue"
(对这个片种其实完全够用,整句字幕本来就是常规做法):

```bash
vox speak "warm up" -m large -o /tmp --subtitle srt   # 顺带拉 ForcedAligner
```

想省掉每次调用的模型加载开销:另开一个终端跑 `vox serve`。

---

## 3. ffmpeg 与字体

ffmpeg / ffprobe 必装(`brew install ffmpeg`)。

**字幕烧录不依赖 libass。** 本机的 ffmpeg 不含 libass/freetype/fontconfig,
`subtitles` 和 `drawtext` 滤镜都不存在,而 homebrew-core 当前的公式本身就不带 ——
`brew` 修不好。`assemble.py` 因此默认走 Pillow 渲 PNG + overlay,这是主路线。
脚本每次都探测,将来换了带 libass 的构建会自动升级。

字体(可选,但推荐 —— Anton 是这个片种的原味选择):

```bash
brew install --cask font-anton
```

不装就退到 Arial Black / Impact,观感接近但没那么"Vox"。

---

## 4. 软链进 skills

```bash
ln -s /Users/greentrain/Github/skills/motion-explainer \
      /Users/greentrain/.claude/skills/motion-explainer
```

---

## 可选:gflow MCP

默认流程**不需要** MCP —— 走 CLI 更强(能做信用取证、没有限流、不受客户端超时管、
还独占 `image batch` / `video chain` / `scene create` / `upscale`)。
注册它只是为了"临时想快出一张图"这类一次性场景。

```bash
claude mcp add gflow -s user -e GFLOW_CLI_UI_MODE=classic -- gflow mcp run
```

用它时有两个坑:

**坑一:`GFLOW_CLI_UI_MODE=classic` 不能省。** 本机账号被灰度到 Flow 的新版
agentic UI,视频生成在"新建 project"那步就 RuntimeError。CLI 可以用
`--ui-mode` 治,但 **`gflow_generate_video` 这个 MCP 工具没有 `ui_mode` 参数**
(图像工具有)—— 只能在注册的 `env` 里设。
(旧的 `GFLOW_CLI_PREFER_CLASSIC=1` 在 gflow 0.44 已废弃并打 DeprecationWarning。)

**坑二:MCP 工具超时要 ≥300 秒。** Veo 一次调用阻塞约 120 秒,默认超时会让
**每条 clip 都失败,而且是提交之后失败 —— 积分已经扣了**。在
`~/.claude/settings.json` 的 `env` 里设:

```jsonc
"env": { "MCP_TOOL_TIMEOUT": "600000", "MCP_TIMEOUT": "60000" }
```

(`GFLOW_CLI_TIMEOUT_SECONDS` 这个环境变量**不存在**,别去设它。)
`gflow mcp setup` 是个只会打印 "not yet implemented" 的空壳,别指望它。

---

## 可选:Higgsfield 后端

如果还想保留切回 Higgsfield 的能力,把它的 MCP 也注册上,然后读
`references/backend-higgsfield.md`。用那个后端时 `narrate.py` 和 `assemble.py`
都不需要 —— TTS、装配、烧字幕都在它服务端做。

---

## 可选:ElevenLabs 旁白

装了 ElevenLabs MCP 就能用更好的纪录片男声。用法见 `references/narration.md`
的路线 B(agent 调 MCP 生成 wav → `narrate.py --measure-only` 接手)。

---

## 验证

```bash
uv run --script "$SKILL_DIR/scripts/preflight.py" --probe-auth
```

全绿之后,建议先跑一条**单块真跑**(1 积分):风格键(免费)→ 1 张关键帧(免费,
看风格对不对)→ 1 条 i2v clip → 装配。这一条能把登录、UI_MODE、信用规则
全部验通,比直接开 6 块划算得多。
