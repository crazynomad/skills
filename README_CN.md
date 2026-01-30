# Skills for Non-Coder

[English](./README.md) | [中文](./README_CN.md)

**所有人都用得到**的 Agent 技能合集，涵盖媒体处理、内容加工和文件管理。通过简单的 AI 指令即可完成复杂操作。

## 技能列表

### 文件管理（macOS）

#### [file-master](./file-master)
Mac 文件管理大师 - 纯提示编排技能，将 disk-cleaner、file-organizer、doc-mindmap 串成「清 → 理 → 知」三阶段工作流，一次搞定 Mac 文件管理。

#### [disk-cleaner](./disk-cleaner)
Mac 智能磁盘清理助手，基于 [Mole](https://github.com/tw93/Mole) 打造。支持三档清理策略（Air/Pro/Max）、白名单保护、分类报告和成就页面。

#### [file-organizer](./file-organizer)
Mac 智能文件整理助手，专注整理下载文件夹中的办公文档。支持手动模式（智能文件夹）和自动模式（按类型分类），与 disk-cleaner 白名单联动。

#### [doc-mindmap](./doc-mindmap)
文档智能整理助手 - 批量转换办公文档为 Markdown，通过本地 Ollama 模型生成摘要，三维度软链接分类（主题/用途/客户），零额外磁盘占用。

### 媒体处理

#### [pdf-to-images](./pdf-to-images)
使用 ImageMagick 将 PDF 文件转换为高质量图片（PNG/JPG），适合提取幻灯片或生成预览图。

#### [podcast-downloader](./podcast-downloader)
高效下载 Apple Podcasts 播客节目。支持 iTunes API 快速查询，内置 RSS 回退机制和元数据提取。

#### [srt-title-generator](./srt-title-generator)
分析 SRT 字幕文件，生成有吸引力的爆款视频标题。针对 YouTube、B 站、小红书等平台优化。

#### [youtube-downloader](./youtube-downloader)
基于 `yt-dlp` 的强大视频下载工具，支持从 YouTube 及 1000+ 网站下载视频、播放列表、字幕和元数据。

## 环境要求

大部分技能跨平台可用，部分有特定系统要求：

- **disk-cleaner / file-organizer / file-master**：**仅限 macOS**
- **disk-cleaner**：需安装 [Mole](https://github.com/tw93/Mole)（`brew install tw93/tap/mole`）
- **doc-mindmap**：需安装 [markitdown](https://github.com/microsoft/markitdown)（`pip install 'markitdown[all]'`），摘要功能需 [Ollama](https://ollama.com/)
- **pdf-to-images**：需安装 [ImageMagick](https://imagemagick.org/)
- **youtube-downloader**：音频提取需 [FFmpeg](https://ffmpeg.org/)

所有脚本需要 **Python 3.10+** 环境。

## 使用方式

这些技能专为 Claude Code 或类似 Agent 环境设计。

### 安装

```bash
npx skills add crazynomad/skills
```

更多详情请访问 **https://skills.sh/docs**。

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
