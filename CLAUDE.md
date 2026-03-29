# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of Claude Code skills for non-coders, covering media processing and file management tasks. Skills are standalone tools that can be invoked by Claude Code to perform specific operations.

## Repository Structure

```
skills/
├── .claude-plugin/marketplace.json  # Plugin marketplace registration
├── <skill-name>/
│   ├── SKILL.md                     # Skill interface definition (required)
│   └── scripts/                     # Implementation scripts
└── README.md
```

Each skill follows the pattern:
- `SKILL.md`: YAML frontmatter (name, description) + usage documentation
- `scripts/`: Python scripts that implement the skill functionality

Two skills are **prompt-based** (no scripts): `srt-title-generator` uses Claude's own analysis, and `file-master` orchestrates other skills via prompt chaining.

## Requirements

- Python 3.10+
- `media-skills` plugin: cross-platform
- `file-skills` plugin: macOS only (`disk-cleaner`, `file-organizer`, `file-master` use macOS-native APIs; `doc-mindmap` is cross-platform)

## Available Skills

| Plugin | Skill | Script | Dependencies |
|--------|-------|--------|--------------|
| media-skills | pdf-to-images | `scripts/pdf_to_images.py` | ImageMagick (`brew install imagemagick`) |
| media-skills | podcast-downloader | `scripts/download_podcast.py` | `pip install requests feedparser` |
| media-skills | youtube-downloader | `scripts/download_video.py` | `pip install yt-dlp`, ffmpeg for audio |
| media-skills | srt-title-generator | No script (prompt-based) | None |
| media-skills | tts | `scripts/vox_tts.py` | Vox CLI (`pipx install .` from [3Craft/tts](https://github.com/3Craft/tts)), Apple Silicon only |
| media-skills | twitter-downloader | `scripts/download_tweet.py` | `pip install yt-dlp` (same as youtube-downloader) |
| file-skills | file-master | No script (prompt-based orchestrator) | All file-skills deps |
| file-skills | disk-cleaner | `scripts/mole_cleaner.py` | Mole (`brew install tw93/tap/mole`) |
| file-skills | file-organizer | `scripts/file_organizer.py` | macOS only, no extra deps |
| file-skills | doc-mindmap | `scripts/doc_converter.py` | `pip install 'markitdown[all]'`; Ollama optional for summarization |

## Creating New Skills

1. Create a directory with the skill name
2. Add `SKILL.md` with:
   - YAML frontmatter: `name`, `description`
   - "When to Use" section with trigger keywords
   - Usage examples with CLI syntax
   - Dependencies section
   - Output structure documentation
3. Add implementation in `scripts/` directory
4. Update `.claude-plugin/marketplace.json` to include the new skill path in the appropriate plugin group
5. Update `README.md` and `README.zh.md` to document the new skill

## Script Safety Pattern

All destructive scripts share a consistent safety convention before making changes:
- `--preview` / `--dry-run`: show what would happen, no changes made
- `--confirm`: required flag to actually execute (guards against accidental runs)

Always run preview mode first when testing a script.

## Skill Interface Pattern

Skills should follow this documentation pattern in SKILL.md:
- **When to Use**: Keywords and phrases that trigger skill activation
- **Usage**: CLI syntax with common scenarios
- **Arguments**: Flag descriptions with defaults
- **Dependencies**: System and Python package requirements
- **Output Structure**: Expected file/directory output format
- **Claude Integration**: Step-by-step workflow for Claude to follow

## Testing Skills Locally

```bash
# PDF to images
python pdf-to-images/scripts/pdf_to_images.py "input.pdf" -o ./output -d 150

# Podcast download
python podcast-downloader/scripts/download_podcast.py "APPLE_PODCAST_URL" -n 3

# YouTube download
python youtube-downloader/scripts/download_video.py "YOUTUBE_URL" -o ./output

# Disk cleaner
python disk-cleaner/scripts/mole_cleaner.py --preview
python disk-cleaner/scripts/mole_cleaner.py --clean --confirm

# File organizer (Downloads folder only by default)
python file-organizer/scripts/file_organizer.py --auto --dry-run
python file-organizer/scripts/file_organizer.py --auto

# TTS - text to speech
python tts/scripts/vox_tts.py check
python tts/scripts/vox_tts.py speak "Hello world" --voice Chelsie -o ./output
python tts/scripts/vox_tts.py speak "Hello world" --play
python tts/scripts/vox_tts.py transcribe recording.wav -o ./output
python tts/scripts/vox_tts.py clone "Text" --ref sample.wav -o ./output
python tts/scripts/vox_tts.py voices

# Twitter/X video download
python twitter-downloader/scripts/download_tweet.py "https://x.com/username/status/1234567890"
python twitter-downloader/scripts/download_tweet.py "URL" --url-only   # check URL without downloading
python twitter-downloader/scripts/download_tweet.py "URL" -o ./output -q 720

# Doc mindmap (convert to Markdown)
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --preview
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --convert --confirm

# Doc mindmap (with Ollama summarization — requires: brew install ollama && ollama pull qwen2.5:3b)
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --convert --confirm --summarize

# Doc mindmap (symlink-based 3-way classification into by-topic/by-usage/by-client)
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --organize --confirm

# Doc mindmap (AI-suggested filenames for symlinks)
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --organize --rename --confirm
```

## Plugin Registration

Skills are registered in `.claude-plugin/marketplace.json` (marketplace name: `greentrain-skills`). Two plugin groups:
- `greentrain-media`: pdf-to-images, podcast-downloader, srt-title-generator, tts, twitter-downloader, youtube-downloader
- `greentrain-files`: file-master, disk-cleaner, file-organizer, doc-mindmap

When adding or updating a skill, **always update all three files together**:
1. `.claude-plugin/marketplace.json` - add skill path to the appropriate plugin group
2. `README.md` - English documentation
3. `README.zh.md` - Chinese documentation
