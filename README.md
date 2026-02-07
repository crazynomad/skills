# Skills for Non-Coder

English | [中文](./README.zh.md)

A collection of specialized agent skills designed for **non-coders** to handle media, content processing, and file management tasks. Perform complex operations through simple AI instructions.

## Prerequisites

- Python 3.10+ environment
- macOS for `disk-cleaner`, `file-organizer`, and `file-master` (system-specific tools)

## Installation

### Quick Install (Recommended)

```bash
npx skills add crazynomad/skills
```

### Register as Plugin Marketplace

Run the following command in Claude Code:

```bash
/plugin marketplace add crazynomad/skills
```

### Install Skills

**Option 1: Via Browse UI**

1. Select **Browse and install plugins**
2. Select **noncoder-skills**
3. Select the plugin(s) you want to install
4. Select **Install now**

**Option 2: Direct Install**

```bash
# Install specific plugin
/plugin install media-skills@noncoder-skills
/plugin install file-skills@noncoder-skills
```

**Option 3: Ask the Agent**

Simply tell Claude Code:

> Please install Skills from github.com/crazynomad/skills

### Available Plugins

| Plugin | Description | Skills |
|--------|-------------|--------|
| **media-skills** | Video/podcast downloading, PDF conversion, title generation | [pdf-to-images](#pdf-to-images), [podcast-downloader](#podcast-downloader), [srt-title-generator](#srt-title-generator), [youtube-downloader](#youtube-downloader) |
| **file-skills** | macOS disk cleaning, file organizing, document intelligence | [file-master](#file-master), [disk-cleaner](#disk-cleaner), [file-organizer](#file-organizer), [doc-mindmap](#doc-mindmap) |

For more details, visit **https://skills.sh/docs**.

## Available Skills

Skills are organized into three categories:

### File Management (macOS)

#### file-master

Mac file management master - a prompt-only orchestration skill that chains disk-cleaner, file-organizer, and doc-mindmap into a **Clean > Organize > Analyze** three-phase workflow.

Three phases:
| Phase | Name | Description |
|-------|------|-------------|
| Phase 1 | Clean | Disk cleanup with disk-cleaner |
| Phase 2 | Organize | File organization with file-organizer |
| Phase 3 | Analyze | Document analysis with doc-mindmap |

> Only triggers when user needs combined multi-stage operations. For single tasks, use individual skills directly.

#### disk-cleaner

Smart Mac disk cleaning assistant powered by [Mole](https://github.com/tw93/Mole). Features three-tier cleanup strategies, whitelist protection, categorized reports, and achievement pages.

```bash
# Check environment
python disk-cleaner/scripts/mole_cleaner.py --check

# Preview cleanable items
python disk-cleaner/scripts/mole_cleaner.py --preview

# Preview with HTML report
python disk-cleaner/scripts/mole_cleaner.py --preview --html

# Clean with tier selection (air/pro/max)
python disk-cleaner/scripts/mole_cleaner.py --clean --tier air --confirm
python disk-cleaner/scripts/mole_cleaner.py --clean --tier pro --confirm
python disk-cleaner/scripts/mole_cleaner.py --clean --tier max --confirm

# Manage whitelist
python disk-cleaner/scripts/mole_cleaner.py --whitelist --show
python disk-cleaner/scripts/mole_cleaner.py --whitelist --preset office
```

**Cleanup Tiers**:
| Tier | Description |
|------|-------------|
| `air` | Conservative - system caches only |
| `pro` | Balanced - caches + logs + temp files |
| `max` | Aggressive - all cleanable items |

**Dependencies**: [Mole](https://github.com/tw93/Mole) (`brew install tw93/tap/mole`)

#### file-organizer

Smart Mac file organizer focused on sorting office documents in the Downloads folder. Supports manual mode (Smart Folders) and auto mode (sort by type), with disk-cleaner whitelist integration.

```bash
# Manual mode - create smart folders
python file-organizer/scripts/file_organizer.py --manual

# Auto mode - organize by category
python file-organizer/scripts/file_organizer.py --auto

# Preview without moving
python file-organizer/scripts/file_organizer.py --auto --dry-run

# View/organize screenshots
python file-organizer/scripts/file_organizer.py --screenshots

# Find large files (default >100MB)
python file-organizer/scripts/file_organizer.py --large-files
python file-organizer/scripts/file_organizer.py --large-files --min-size 500
```

**Modes**:
| Mode | Description |
|------|-------------|
| `--manual` | Create smart folders for manual organization |
| `--auto` | Auto-organize files by category |
| `--screenshots` | View and organize screenshots |
| `--large-files` | Find large files above threshold |

**Dependencies**: macOS, Python 3.8+

#### doc-mindmap

Document intelligence assistant - batch convert office documents to Markdown, generate summaries via local Ollama models, and create three-dimension symlink classification (topic/usage/client) with zero extra disk usage.

```bash
# Preview documents + duplicate detection
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --preview

# Batch convert to Markdown
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --convert --confirm

# Generate summaries with Ollama
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --summarize

# Create 3-way classification with symlinks
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --organize

# Full pipeline
python doc-mindmap/scripts/doc_converter.py ~/Documents/reports --convert --confirm --summarize --organize
```

**Supported Formats**: PDF, PPTX, DOCX, XLSX, XLS, CSV, HTML, EPUB, JSON, XML

**Dependencies**:
- [markitdown](https://github.com/microsoft/markitdown): `pip install 'markitdown[all]'`
- [Ollama](https://ollama.com/) (optional, for summaries): `brew install ollama`

### Media Processing

#### pdf-to-images

Convert PDF files into a series of high-quality images (PNG/JPG) using ImageMagick. Useful for extracting slides or creating previews.

```bash
# Basic conversion
python pdf-to-images/scripts/pdf_to_images.py "presentation.pdf"

# Specify output directory
python pdf-to-images/scripts/pdf_to_images.py "document.pdf" -o ./output-images

# High resolution (300 DPI)
python pdf-to-images/scripts/pdf_to_images.py "document.pdf" -d 300

# JPEG output with quality setting
python pdf-to-images/scripts/pdf_to_images.py "document.pdf" -f jpg -q 90
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | Same dir with `-slides` suffix |
| `-d, --dpi` | Resolution DPI | 150 |
| `-f, --format` | png, jpg, tiff | png |
| `-q, --quality` | JPEG quality 1-100 | 85 |
| `-p, --prefix` | Output filename prefix | slide |

**Dependencies**: [ImageMagick](https://imagemagick.org/) (`brew install imagemagick`)

#### podcast-downloader

Download podcast episodes efficiently from Apple Podcasts. Features iTunes API integration for speed, with robust RSS fallback and metadata extraction.

```bash
# Download a single episode
python podcast-downloader/scripts/download_podcast.py "https://podcasts.apple.com/cn/podcast/id1711052890?i=1000744375610"

# Download latest 5 episodes
python podcast-downloader/scripts/download_podcast.py "https://podcasts.apple.com/cn/podcast/id1711052890" -n 5

# Specify output directory
python podcast-downloader/scripts/download_podcast.py "PODCAST_URL" -n 10 -o ./podcasts
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `url` | Apple Podcast URL (required) | - |
| `-n, --count` | Number of latest episodes | All (up to 200) |
| `-o, --output` | Output directory | Current directory |

**Dependencies**: `pip install requests feedparser`

#### srt-title-generator

Analyze SRT subtitle files to generate engaging, viral-potential video titles. Optimized for platforms like YouTube, Bilibili, and Xiaohongshu.

**Workflow**: Read SRT file > Extract transcript > Analyze content > Generate platform-specific titles

**Output format**: Structured titles for multiple platforms:
| Platform | Constraint |
|----------|-----------|
| YouTube | Max 60 characters |
| Xiaohongshu | Max 20 characters |
| Bilibili | Max 80 characters |
| Douyin | Max 55 characters |

**Dependencies**: None (prompt-based skill)

#### youtube-downloader

A powerful video downloader wrapping `yt-dlp`. Supports downloading videos, playlists, subtitles, and metadata from YouTube and 1000+ other sites.

```bash
# Download a video
python youtube-downloader/scripts/download_video.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify resolution
python youtube-downloader/scripts/download_video.py "URL" -f 1080

# Audio only (MP3)
python youtube-downloader/scripts/download_video.py "URL" --audio-only

# Download with subtitles
python youtube-downloader/scripts/download_video.py "URL" --subtitles

# Download playlist
python youtube-downloader/scripts/download_video.py "PLAYLIST_URL" --playlist -n 5

# Specify output directory
python youtube-downloader/scripts/download_video.py "URL" -o ./videos
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | Current directory |
| `-f, --format` | best, 1080, 720, 480, 360 | best |
| `--audio-only` | Extract audio only (MP3) | - |
| `--subtitles` | Download subtitles | - |
| `--sub-lang` | Subtitle language | en,zh-Hans |
| `--playlist` | Enable playlist mode | - |
| `-n, --count` | Number of videos from playlist | - |
| `--metadata` | Save video metadata JSON | true |
| `--thumbnail` | Download thumbnail | - |
| `--cookies` | Path to cookies file | - |

**Dependencies**:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`
- [FFmpeg](https://ffmpeg.org/) (for audio extraction): `brew install ffmpeg`

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

## License

MIT
