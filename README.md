# Skills for Non-Coder

[English](./README.md) | [中文](./README_CN.md)

A collection of specialized agent skills designed for **non-coders** to handle media, content processing, and file management tasks. Perform complex operations through simple AI instructions.

## Skills

### File Management (macOS)

#### [file-master](./file-master)
Mac file management master - a prompt-only orchestration skill that chains disk-cleaner, file-organizer, and doc-mindmap into a "Clean > Organize > Analyze" three-phase workflow.

#### [disk-cleaner](./disk-cleaner)
Smart Mac disk cleaning assistant powered by [Mole](https://github.com/tw93/Mole). Features three-tier cleanup strategies (Air/Pro/Max), whitelist protection, categorized reports, and achievement pages.

#### [file-organizer](./file-organizer)
Smart Mac file organizer focused on sorting office documents in the Downloads folder. Supports manual mode (Smart Folders) and auto mode (sort by type), with disk-cleaner whitelist integration.

#### [doc-mindmap](./doc-mindmap)
Document intelligence assistant - batch convert office documents to Markdown, generate summaries via local Ollama models, and create three-dimension symlink classification (topic/usage/client) with zero extra disk usage.

### Media Processing

#### [pdf-to-images](./pdf-to-images)
Convert PDF files into a series of high-quality images (PNG/JPG) using ImageMagick. Useful for extracting slides or creating previews.

#### [podcast-downloader](./podcast-downloader)
Download podcast episodes efficiently from Apple Podcasts. Features iTunes API integration for speed, with robust RSS fallback and metadata extraction.

#### [srt-title-generator](./srt-title-generator)
Analyze SRT subtitle files to generate engaging, viral-potential video titles. Optimized for platforms like YouTube, Bilibili, and Xiaohongshu.

#### [youtube-downloader](./youtube-downloader)
A powerful video downloader wrapping `yt-dlp`. Supports downloading videos, playlists, subtitles, and metadata from YouTube and 1000+ other sites.

## Prerequisites & Limitations

While most skills are cross-platform, some have specific system requirements:

- **disk-cleaner / file-organizer / file-master**: **macOS Only**
- **disk-cleaner**: Requires [Mole](https://github.com/tw93/Mole) (`brew install tw93/tap/mole`)
- **doc-mindmap**: Requires [markitdown](https://github.com/microsoft/markitdown) (`pip install 'markitdown[all]'`) and optionally [Ollama](https://ollama.com/) for summaries
- **pdf-to-images**: Requires [ImageMagick](https://imagemagick.org/)
- **youtube-downloader**: Requires [FFmpeg](https://ffmpeg.org/) for audio extraction

All scripts assume a working **Python 3.10+** environment.

## Usage

These skills are structured for use with Claude Code or similar agentic environments.

### Installation

Visit **https://skills.sh/docs** for the recommended installation guide.

## Structure

Each skill is contained in its own directory with a `SKILL.md` file defining its interface, usage, and dependencies.

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

## Acknowledgements

These skills stand on the shoulders of giants:

- **[Mole](https://github.com/tw93/Mole)** - Core engine for macOS system cleaning.
- **[markitdown](https://github.com/microsoft/markitdown)** - Microsoft's document-to-Markdown converter.
- **[Ollama](https://ollama.com/)** - Local LLM runtime for document summarization and classification.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The backbone of our video downloading capabilities.
- **[ImageMagick](https://imagemagick.org/)** - Powering our PDF to image conversion.
- **[FFmpeg](https://ffmpeg.org/)** - Essential for high-quality audio extraction and video processing.
- **[Requests](https://requests.readthedocs.io/)** & **[Feedparser](https://github.com/kurtmckee/feedparser)** - Reliable tools for API interaction and RSS parsing.

We are grateful to the maintainers and contributors of these projects for their dedication to open-source software.
