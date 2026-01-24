# Skills for Non-Coder

This repository contains a collection of specialized agent skills designed specifically for **non-coders** to handle media and content processing tasks. These skills allow anyone to perform complex operations related to audio, video, and document manipulation through simple AI instructions.

## Skills

### [pdf-to-images](./pdf-to-images)
Convert PDF files into a series of high-quality images (PNG/JPG) using ImageMagick. Useful for extracting slides or creating previews.

### [podcast-downloader](./podcast-downloader)
Download podcast episodes efficiently from Apple Podcasts. Features iTunes API integration for speed, with robust RSS fallback and metadata extraction.

### [srt-title-generator](./srt-title-generator)
Analyze SRT subtitle files to generate engaging, viral-potential video titles. Optimized for platforms like YouTube, Bilibili, and Little Red Book (Xiaohongshu).

### [youtube-downloader](./youtube-downloader)
A powerful video downloader wrapping `yt-dlp`. Supports downloading videos, playlists, subtitles, and metadata from YouTube and 1000+ other sites.

## Prerequisites & Limitations

While most skills are cross-platform, some have specific system requirements:

- **disk-cleaner**: ⚠️ **macOS Only**. This skill relies on the `mole` CLI tool which is designed for macOS system cleaning.
- **pdf-to-images**: Requires **[ImageMagick](https://imagemagick.org/)** to be installed on the system.
- **youtube-downloader**: Requires **[FFmpeg](https://ffmpeg.org/)** for audio extraction and format merging.

All scripts assume a working **Python 3.10+** environment.

## Usage

These skills are structured for use with Claude Code or similar agentic environments.

### Claude Code Installation

You can register this repository as a plugin source:

```bash
/plugin marketplace add burn.wang/skills
```
*(Note: Replace `burn.wang/skills` with your actual git repository URL or identifier if different)*

Or install the media skills group directly:

```bash
/plugin install media-skills@burn.wang/skills
```

## Structure

Each skill is contained in its own directory with a `SKILL.md` file defining its interface, usage, and dependencies.

## Acknowledgements

These skills stand on the shoulders of giants. We would like to thank the following open-source projects that make these automation tasks possible:

- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** - The backbone of our video downloading capabilities.
- **[ImageMagick](https://imagemagick.org/)** - Powering our PDF to image conversion.
- **[FFmpeg](https://ffmpeg.org/)** - Essential for high-quality audio extraction and video processing.
- **[Requests](https://requests.readthedocs.io/)** & **[Feedparser](https://github.com/kurtmckee/feedparser)** - Reliable tools for API interaction and RSS parsing.
- **[Mole](https://github.com/tw93/mole)** - Inspiration and core logic for system cleaning tasks.

We are grateful to the maintainers and contributors of these projects for their dedication to open-source software.