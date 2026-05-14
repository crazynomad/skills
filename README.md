# Green Train Skills

English | [中文](./README.zh.md)

Agent skills by [绿皮火车](https://www.youtube.com/channel/UCJhUtNsR5pvU_gWWkxxUXUQ) for media processing, file management, and local AI. Perform complex operations through simple AI instructions.

## Video Tutorials

| Video | Skills Covered | Duration |
|-------|---------------|----------|
| [Turn 4000+ PPTs into a Personal Knowledge Base](https://youtu.be/lGRbMZw23ic) | disk-cleaner, file-organizer, doc-mindmap | 17:30 |
| [Vibe Coding Challenge: Building a Podcast Downloader](https://youtu.be/zaj9ouF7VFQ) | podcast-downloader | 10:55 |

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
2. Select **greentrain-skills**
3. Select the plugin(s) you want to install
4. Select **Install now**

**Option 2: Direct Install**

```bash
# Install specific plugin
/plugin install greentrain-media@greentrain-skills
/plugin install greentrain-files@greentrain-skills
/plugin install greentrain-planning@greentrain-skills
```

**Option 3: Ask the Agent**

Simply tell Claude Code:

> Please install Skills from github.com/crazynomad/skills

### Available Plugins

| Plugin | Description | Skills |
|--------|-------------|--------|
| **greentrain-media** | Video/podcast downloading, PDF conversion, title generation, TTS/STT, visual PPT generation | [pdf-to-images](#pdf-to-images), [podcast-downloader](#podcast-downloader), [srt-title-generator](#srt-title-generator), [tts](#tts), [twitter-downloader](#twitter-downloader), [visual-deck](#visual-deck), [visual-slides](#visual-slides), [youtube-downloader](#youtube-downloader) |
| **greentrain-files** | macOS disk cleaning, file organizing, document intelligence | [file-master](#file-master), [disk-cleaner](#disk-cleaner), [file-organizer](#file-organizer), [doc-mindmap](#doc-mindmap) |
| **greentrain-planning** | Think-before-you-slide PPT methodology: classify, research-driven thesis, storyline review | [ppt-classify](#ppt-classify), [ppt-research-setup](#ppt-research-setup), [ppt-narrative-review](#ppt-narrative-review) |

For more details, visit **https://skills.sh/docs**.

## Available Skills

Skills are organized into four categories:

### File Management (macOS)

#### file-master

Mac file management master - a prompt-only orchestration skill that chains disk-cleaner, file-organizer, and doc-mindmap into a **Clean > Organize > Analyze** three-phase workflow. In a real-world demo, this workflow freed 120GB of disk space, organized 1,600+ files, and converted 4,000+ PPTs into a searchable knowledge base. ([Watch the full walkthrough](https://youtu.be/lGRbMZw23ic))

Three phases:
| Phase | Name | Description |
|-------|------|-------------|
| Phase 1 | Clean | Disk cleanup with disk-cleaner |
| Phase 2 | Organize | File organization with file-organizer |
| Phase 3 | Analyze | Document analysis with doc-mindmap |

> Only triggers when user needs combined multi-stage operations. For single tasks, use individual skills directly.

#### disk-cleaner

Smart Mac disk cleaning assistant powered by [Mole](https://github.com/tw93/Mole). Features three-tier cleanup strategies, whitelist protection, categorized reports, and achievement pages. In a real-world test, it freed over 106GB of disk space across browser caches, app caches, system logs, and package manager artifacts.

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

Smart Mac file organizer focused on sorting office documents in the Downloads folder. Supports manual mode (Smart Folders) and auto mode (sort by type), with disk-cleaner whitelist integration. Built on macOS native capabilities (Finder Smart Folders + Spotlight), so files stay in place - no vendor lock-in. Tested with 1,600+ files in a single Downloads folder.

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

Document intelligence assistant - batch convert office documents to Markdown, generate summaries via local Ollama models, and create three-dimension symlink classification (topic/usage/client) with zero extra disk usage. All AI processing runs locally via Ollama - your documents never leave your machine. Tested with 4,000+ PPTs and 14,000+ PDFs.

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

Download podcast episodes efficiently from Apple Podcasts. Features iTunes API integration for speed, with robust RSS fallback and metadata extraction. Born from a [Vibe Coding challenge](https://youtu.be/zaj9ouF7VFQ) - built in 3 rounds of AI-assisted development using Claude, Gemini, and NotebookLM to reverse-engineer Apple's podcast API.

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

#### tts

Local text-to-speech, speech-to-text, and voice cloning on Apple Silicon, powered by [Vox CLI](https://github.com/3Craft/tts) (Qwen3-TTS + MLX). All processing runs entirely on-device - your data never leaves your machine.

```bash
# Text-to-speech
python tts/scripts/vox_tts.py speak "Hello world" --voice Chelsie -o ./output

# Speak with emotion/style
python tts/scripts/vox_tts.py speak "I can't believe it!" --instruct "excited" -o ./output

# Play audio immediately
python tts/scripts/vox_tts.py speak "Hello world" --play

# Transcribe audio to text
python tts/scripts/vox_tts.py transcribe recording.wav -o ./output

# Transcribe with SRT subtitles
python tts/scripts/vox_tts.py transcribe recording.wav --subtitle srt -o ./output

# Clone a voice from a sample
python tts/scripts/vox_tts.py clone "Text in cloned voice" --ref sample.wav -o ./output

# Register a cloned voice for reuse
python tts/scripts/vox_tts.py clone --ref sample.wav --register my-voice

# Design a voice from description
python tts/scripts/vox_tts.py design "Hello" --desc "warm friendly female voice" -o ./output

# Batch TTS from file
python tts/scripts/vox_tts.py batch texts.txt --voice Chelsie -o ./output

# List available voices
python tts/scripts/vox_tts.py voices
```

**Options (speak)**:
| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | Current directory |
| `-v, --voice` | Voice name | Chelsie |
| `-m, --model` | small, large, large-hq | small |
| `-s, --speed` | Speed multiplier | 1.0 |
| `-i, --instruct` | Emotion/style instruction | - |
| `--play` | Play audio after generation | - |
| `--subtitle` | Generate srt or vtt | - |

**Dependencies**:
- Apple Silicon Mac (M1/M2/M3/M4), macOS 13+
- [Vox CLI](https://github.com/3Craft/tts): `pipx install /path/to/tts`

#### twitter-downloader

Download videos from individual X (Twitter) posts using `twmd`, an API-less Go-based downloader.

```bash
# Download a video from a tweet
python twitter-downloader/scripts/download_tweet.py "https://x.com/username/status/1234567890"

# Specify output directory
python twitter-downloader/scripts/download_tweet.py "URL" -o ~/Downloads/twitter

# Print video URL without downloading
python twitter-downloader/scripts/download_tweet.py "URL" --url-only
```

**Options**:
| Option | Description | Default |
|--------|-------------|---------|
| `url` | X/Twitter post URL (required) | - |
| `-o, --output` | Output directory | Current directory |
| `-q, --quality` | Video quality: best, 1080, 720, 480 | best |
| `--url-only` | Print video URL without downloading | - |
| `--cookies` | Path to cookies file (for private content) | - |

**Dependencies**: [yt-dlp](https://github.com/yt-dlp/yt-dlp): `pip install yt-dlp`

#### visual-deck

Generate "image + text" style visual PPT decks via an HTML→PPTX pipeline. Uses safe-zone typography (text only lands in designated image regions), overflow-to-notes discipline (never shrink fonts — spillover goes into speaker notes), and Nano Banana backgrounds. Ships with 8 layouts (cover, quote, l34/r34, 2col, 3col, timeline, stats) and a theme system (dark-coral, dark-teal). Intended for evangelism / internal sharing / client-facing decks where layout is image-driven; **not** for data reports or text-heavy docs.

```bash
# Run the minimal example (playwright + pptxgenjs + sharp required)
cd visual-deck/examples/minimal
npm install
node build.js   # → output/deck.pptx
```

**Dependencies**: Node.js 18+, `npm install` inside the example/template directory pulls in `playwright`, `pptxgenjs`, and `sharp`.

#### visual-slides

Inject content into a hand-authored Google Slides template via the [`gws` CLI](https://github.com/googleworkspace/cli). Shares the visual-deck design language (safe-zone typography, V2 four-segment image prompts, Nano Banana backgrounds, scrim baking) but outputs to a live Google Slides URL instead of a local `.pptx`. Pipeline: copy template deck → upload images to Drive (made public-readable) → `slides.batchUpdate` with `replaceAllText` + `replaceAllShapesWithImage`. Best for decks that need to live on Drive (collaboration, comments) or for templates filled with many content variants. **Not** a drop-in for visual-deck — different output target, different constraints; see `visual-slides/SKILL.md` for the comparison.

```bash
# Walk through the minimal 2-slide example
cd visual-slides/examples/minimal
cat README.md
python ../../scripts/validate_plan.py content-plan.json
python ../../scripts/inject.py content-plan.json --dry-run
python ../../scripts/inject.py content-plan.json
```

**Dependencies**: `gws` CLI on PATH + `gws auth login` completed; Python 3.10+ with `Pillow` (for scrim baking).

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

### Planning & Methodology

A "think-before-you-slide" PPT toolkit. Pairs with `visual-deck` to form a full **classify → thesis → review → render** pipeline. Distilled from 绿皮火车 EP10 《AI 做 PPT》 experiments.

#### ppt-classify

Classify a PPT brief into one of four types — **Pitch / Research / Teaching / Narrative** — and route to the right thesis-setup method. Different PPT types need different立论 frameworks: a research PPT is not a pitch, a pitch is not a narrative. Using the wrong type's structure is the single biggest PPT mistake.

**When to Use**: At the very start of PPT planning, BEFORE writing any slide. Especially useful when the user says "help me make a PPT about X" but hasn't decided how to frame it.

**Workflow**: Ask Q1-Q3 diagnostic chain (decision-driven? → teaching目标? → event vs argument?) → output type + recommended next skill + one-line thesis framework preview.

**Dependencies**: None (prompt-based skill)

#### ppt-research-setup

Set up a research-driven PPT thesis using a three-section framework plus a six-question specificity diagnostic. Distilled from research-grade content like Dylan Patel, Dwarkesh × Jensen, and 硅谷101 GTC 2026.

**Three-Section Framework**:
1. **Counter-consensus paradox** (research motivation) — a question everyone thinks is answered but isn't
2. **Structural decomposition framework** (research boundary) — 3-5 analytical dimensions
3. **3-4 investigation paths** (concrete sub-questions) — each independently verifiable, layered (intuitive → reverse-reasoning → blind-spot)

**Six-Question Specificity Diagnostic** (borrowed from YC forcing questions, reframed for research):
Demand Reality / Status Quo / Desperate Specificity / Narrowest Wedge / Observation & Surprise / Future-Fit.

Core principle: *Specificity is the only currency. Vague answers get pushed.*

**Dependencies**: None (prompt-based skill)

#### ppt-narrative-review

Review a PPT storyline for structural fit, pacing, and key-visual anchors. **Type-aware** — research-driven, pitch-driven, teaching-driven, and narrative-driven decks each have a distinct valid storyline shape. Catches structural mismatches (e.g. research deck using pitch opening) before you burn hours on visuals.

**Four Storyline Shapes**:
| Type | Shape |
|------|-------|
| Research | Paradox → Framework → Investigation paths → Synthesis |
| Pitch | Conclusion → Pain → Evidence laddering → Counterargument → CTA |
| Teaching | Pain → Capability promise → Steps → Traps → Advanced |
| Narrative | Protagonist → Inciting event → Struggle → Turning point → New state |

**Output**: Structure-fit score, page-by-page review (✅ core / 🔶 support / ❌ cut), key-visual anchor recommendations.

**Dependencies**: None (prompt-based skill)

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
├── tts/
├── twitter-downloader/
├── visual-deck/
├── youtube-downloader/
├── ppt-classify/
├── ppt-research-setup/
├── ppt-narrative-review/
└── README.md
```

## Acknowledgements

These skills stand on the shoulders of giants:

- **[Mole](https://github.com/tw93/Mole)** - Core engine for macOS system cleaning.
- **[markitdown](https://github.com/microsoft/markitdown)** - Microsoft's document-to-Markdown converter.
- **[Ollama](https://ollama.com/)** - Local LLM runtime for document summarization and classification.
- **[Vox CLI](https://github.com/3Craft/tts)** - Local TTS/STT engine for Apple Silicon via Qwen3-TTS + MLX.
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The backbone of our video downloading capabilities.
- **[ImageMagick](https://imagemagick.org/)** - Powering our PDF to image conversion.
- **[FFmpeg](https://ffmpeg.org/)** - Essential for high-quality audio extraction and video processing.
- **[Requests](https://requests.readthedocs.io/)** & **[Feedparser](https://github.com/kurtmckee/feedparser)** - Reliable tools for API interaction and RSS parsing.

We are grateful to the maintainers and contributors of these projects for their dedication to open-source software.

## License

MIT
