# Skills for Non-Coder

[English](./README.md) | 中文

**所有人都用得到**的 Agent 技能合集，涵盖媒体处理、内容加工和文件管理。通过简单的 AI 指令即可完成复杂操作。

## 前置要求

- Python 3.10+ 环境
- `disk-cleaner`、`file-organizer`、`file-master` 仅限 macOS

## 安装

### 快速安装（推荐）

```bash
npx skills add crazynomad/skills
```

### 注册插件市场

在 Claude Code 中运行：

```bash
/plugin marketplace add crazynomad/skills
```

### 安装技能

**方式一：通过浏览界面**

1. 选择 **Browse and install plugins**
2. 选择 **noncoder-skills**
3. 选择要安装的插件
4. 选择 **Install now**

**方式二：直接安装**

```bash
# 安装指定插件
/plugin install media-skills@noncoder-skills
/plugin install file-skills@noncoder-skills
```

**方式三：告诉 Agent**

直接告诉 Claude Code：

> 请帮我安装 github.com/crazynomad/skills 中的 Skills

### 可用插件

| 插件 | 说明 | 包含技能 |
|------|------|----------|
| **media-skills** | 视频/播客下载、PDF 转换、标题生成 | [pdf-to-images](#pdf-to-images), [podcast-downloader](#podcast-downloader), [srt-title-generator](#srt-title-generator), [youtube-downloader](#youtube-downloader) |
| **file-skills** | macOS 磁盘清理、文件整理、文档智能 | [file-master](#file-master), [disk-cleaner](#disk-cleaner), [file-organizer](#file-organizer), [doc-mindmap](#doc-mindmap) |

更多详情请访问 **https://skills.sh/docs**。

## 可用技能

技能分为三大类：

### 文件管理（macOS）

#### file-master

Mac 文件管理大师 - 纯提示编排技能，将 disk-cleaner、file-organizer、doc-mindmap 串成 **「清 → 理 → 知」** 三阶段工作流，一次搞定 Mac 文件管理。

三个阶段：
| 阶段 | 名称 | 说明 |
|------|------|------|
| 阶段一 | 清 | 使用 disk-cleaner 清理磁盘 |
| 阶段二 | 理 | 使用 file-organizer 整理文件 |
| 阶段三 | 知 | 使用 doc-mindmap 分析文档 |

> 仅在用户需要多阶段组合操作时触发，单一任务请直接使用对应技能。

#### disk-cleaner

Mac 智能磁盘清理助手，基于 [Mole](https://github.com/tw93/Mole) 打造。支持三档清理策略、白名单保护、分类报告和成就页面。

```bash
# 检查环境
python disk-cleaner/scripts/mole_cleaner.py --check

# 预览可清理项目
python disk-cleaner/scripts/mole_cleaner.py --preview

# 带 HTML 报告的预览
python disk-cleaner/scripts/mole_cleaner.py --preview --html

# 选择档位清理（air/pro/max）
python disk-cleaner/scripts/mole_cleaner.py --clean --tier air --confirm
python disk-cleaner/scripts/mole_cleaner.py --clean --tier pro --confirm
python disk-cleaner/scripts/mole_cleaner.py --clean --tier max --confirm

# 管理白名单
python disk-cleaner/scripts/mole_cleaner.py --whitelist --show
python disk-cleaner/scripts/mole_cleaner.py --whitelist --preset office
```

**清理档位**：
| 档位 | 说明 |
|------|------|
| `air` | 保守 - 仅系统缓存 |
| `pro` | 均衡 - 缓存 + 日志 + 临时文件 |
| `max` | 激进 - 所有可清理项 |

**依赖**：[Mole](https://github.com/tw93/Mole)（`brew install tw93/tap/mole`）

#### file-organizer

Mac 智能文件整理助手，专注整理下载文件夹中的办公文档。支持手动模式（智能文件夹）和自动模式（按类型分类），与 disk-cleaner 白名单联动。

```bash
# 手动模式 - 创建智能文件夹
python file-organizer/scripts/file_organizer.py --manual

# 自动模式 - 按类别整理
python file-organizer/scripts/file_organizer.py --auto

# 预览不移动
python file-organizer/scripts/file_organizer.py --auto --dry-run

# 查看/整理截图
python file-organizer/scripts/file_organizer.py --screenshots

# 查找大文件（默认 >100MB）
python file-organizer/scripts/file_organizer.py --large-files
python file-organizer/scripts/file_organizer.py --large-files --min-size 500
```

**模式**：
| 模式 | 说明 |
|------|------|
| `--manual` | 创建智能文件夹供手动整理 |
| `--auto` | 按类别自动整理文件 |
| `--screenshots` | 查看和整理截图 |
| `--large-files` | 查找超过阈值的大文件 |

**依赖**：macOS，Python 3.8+

#### doc-mindmap

文档智能整理助手 - 批量转换办公文档为 Markdown，通过本地 Ollama 模型生成摘要，三维度软链接分类（主题/用途/客户），零额外磁盘占用。

```bash
# 预览文档 + 重复检测
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --preview

# 批量转换为 Markdown
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --convert --confirm

# 使用 Ollama 生成摘要
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --summarize

# 创建三维度软链接分类
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --organize

# 完整流程
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --convert --confirm --summarize --organize
```

**支持格式**：PDF、PPTX、DOCX、XLSX、XLS、CSV、HTML、EPUB、JSON、XML

**依赖**：
- [markitdown](https://github.com/microsoft/markitdown)：`pip install 'markitdown[all]'`
- [Ollama](https://ollama.com/)（可选，用于摘要）：`brew install ollama`

### 媒体处理

#### pdf-to-images

使用 ImageMagick 将 PDF 文件转换为高质量图片（PNG/JPG），适合提取幻灯片或生成预览图。

```bash
# 基础转换
python pdf-to-images/scripts/pdf_to_images.py "presentation.pdf"

# 指定输出目录
python pdf-to-images/scripts/pdf_to_images.py "document.pdf" -o ./output-images

# 高分辨率（300 DPI）
python pdf-to-images/scripts/pdf_to_images.py "document.pdf" -d 300

# JPEG 输出并设置质量
python pdf-to-images/scripts/pdf_to_images.py "document.pdf" -f jpg -q 90
```

**选项**：
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出目录 | 同目录加 `-slides` 后缀 |
| `-d, --dpi` | 分辨率 DPI | 150 |
| `-f, --format` | png、jpg、tiff | png |
| `-q, --quality` | JPEG 质量 1-100 | 85 |
| `-p, --prefix` | 输出文件名前缀 | slide |

**依赖**：[ImageMagick](https://imagemagick.org/)（`brew install imagemagick`）

#### podcast-downloader

高效下载 Apple Podcasts 播客节目。支持 iTunes API 快速查询，内置 RSS 回退机制和元数据提取。

```bash
# 下载单集
python podcast-downloader/scripts/download_podcast.py "https://podcasts.apple.com/cn/podcast/id1711052890?i=1000744375610"

# 下载最新 5 集
python podcast-downloader/scripts/download_podcast.py "https://podcasts.apple.com/cn/podcast/id1711052890" -n 5

# 指定输出目录
python podcast-downloader/scripts/download_podcast.py "PODCAST_URL" -n 10 -o ./podcasts
```

**选项**：
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `url` | Apple Podcast URL（必填） | - |
| `-n, --count` | 下载最新几集 | 全部（最多 200） |
| `-o, --output` | 输出目录 | 当前目录 |

**依赖**：`pip install requests feedparser`

#### srt-title-generator

分析 SRT 字幕文件，生成有吸引力的爆款视频标题。针对 YouTube、B 站、小红书等平台优化。

**工作流程**：读取 SRT 文件 > 提取文本 > 分析内容 > 生成平台专属标题

**输出格式**：为多个平台生成结构化标题：
| 平台 | 字数限制 |
|------|----------|
| YouTube | 最多 60 字符 |
| 小红书 | 最多 20 字符 |
| B 站 | 最多 80 字符 |
| 抖音 | 最多 55 字符 |

**依赖**：无（纯提示技能）

#### youtube-downloader

基于 `yt-dlp` 的强大视频下载工具，支持从 YouTube 及 1000+ 网站下载视频、播放列表、字幕和元数据。

```bash
# 下载视频
python youtube-downloader/scripts/download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 指定分辨率
python youtube-downloader/scripts/download_video.py "URL" -f 1080

# 仅提取音频（MP3）
python youtube-downloader/scripts/download_video.py "URL" --audio-only

# 下载字幕
python youtube-downloader/scripts/download_video.py "URL" --subtitles

# 下载播放列表
python youtube-downloader/scripts/download_video.py "PLAYLIST_URL" --playlist -n 5

# 指定输出目录
python youtube-downloader/scripts/download_video.py "URL" -o ./videos
```

**选项**：
| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出目录 | 当前目录 |
| `-f, --format` | best、1080、720、480、360 | best |
| `--audio-only` | 仅提取音频（MP3） | - |
| `--subtitles` | 下载字幕 | - |
| `--sub-lang` | 字幕语言 | en,zh-Hans |
| `--playlist` | 启用播放列表模式 | - |
| `-n, --count` | 从播放列表下载几个视频 | - |
| `--metadata` | 保存视频元数据 JSON | true |
| `--thumbnail` | 下载缩略图 | - |
| `--cookies` | Cookies 文件路径 | - |

**依赖**：
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)：`pip install yt-dlp`
- [FFmpeg](https://ffmpeg.org/)（用于音频提取）：`brew install ffmpeg`

## 目录结构

每个技能独立一个目录，通过 `SKILL.md` 定义接口、用法和依赖。

```
skills/
├── .claude-plugin/marketplace.json
├── file-master/
├── disk-cleaner/
├── file-organizer/
├── doc-mindmap/
├── pdf-to-images/
├── podcast-downloader/
├── srt-title-generator/
├── youtube-downloader/
└── README.md
```

## 致谢

这些技能离不开以下优秀的开源项目：

- **[Mole](https://github.com/tw93/Mole)** - macOS 系统清理核心引擎
- **[markitdown](https://github.com/microsoft/markitdown)** - 微软出品的文档转 Markdown 工具
- **[Ollama](https://ollama.com/)** - 本地大模型运行框架，用于文档摘要和分类
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - 视频下载核心引擎
- **[ImageMagick](https://imagemagick.org/)** - PDF 转图片的基础
- **[FFmpeg](https://ffmpeg.org/)** - 音频提取和视频处理必备工具
- **[Requests](https://requests.readthedocs.io/)** & **[Feedparser](https://github.com/kurtmckee/feedparser)** - API 请求和 RSS 解析

感谢这些项目的维护者和贡献者对开源软件的付出。

## 许可证

MIT
