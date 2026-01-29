# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of Claude Code skills for non-coders, focused on media and content processing tasks. Skills are standalone tools that can be invoked by Claude Code to perform specific operations.

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

## Requirements

- Python 3.10+
- macOS for `disk-cleaner` and `file-organizer` (system-specific tools)

## Available Skills

| Skill | Script | Dependencies |
|-------|--------|--------------|
| pdf-to-images | `scripts/pdf_to_images.py` | ImageMagick (`brew install imagemagick`) |
| podcast-downloader | `scripts/download_podcast.py` | `pip install requests feedparser` |
| youtube-downloader | `scripts/download_video.py` | `pip install yt-dlp`, ffmpeg for audio |
| disk-cleaner | `scripts/mole_cleaner.py` | Mole (`brew install tw93/tap/mole`) |
| file-organizer | `scripts/file_organizer.py` | macOS only, no extra deps |
| srt-title-generator | No script (prompt-based) | None |
| doc-mindmap | `scripts/doc_converter.py` | `pip install 'markitdown[all]'` |

## Creating New Skills

1. Create a directory with the skill name
2. Add `SKILL.md` with:
   - YAML frontmatter: `name`, `description`
   - "When to Use" section with trigger keywords
   - Usage examples with CLI syntax
   - Dependencies section
   - Output structure documentation
3. Add implementation in `scripts/` directory
4. Update `.claude-plugin/marketplace.json` to include the new skill path

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
python file-organizer/scripts/file_organizer.py --preview
python file-organizer/scripts/file_organizer.py --organize --confirm

# Doc mindmap
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --preview
python doc-mindmap/scripts/doc_converter.py ~/Documents/test-docs --convert --confirm
```

## Plugin Registration

Skills are registered in `.claude-plugin/marketplace.json`. The `plugins[].skills` array lists skill directory paths. When adding a new skill, add its path here to make it discoverable. Note: `disk-cleaner`, `file-organizer`, and `doc-mindmap` are standalone skills not bundled in the `media-skills` plugin group.
