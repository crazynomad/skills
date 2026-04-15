# Changelog

Per-skill version history. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).
Marketplace-level version tracked in `.claude-plugin/marketplace.json`.

---

## visual-deck

### 0.2.0 — 2026-04-15
- **Added**: 4 new layouts — `slide-2col`, `slide-3col`, `slide-timeline`, `slide-stats`
- **Added**: theme system — `dark-coral.css` (default) + `dark-teal.css`, all tokens as CSS variables
- **Added**: decision tree in SKILL.md for layout selection (6 branching questions across 8 layouts)
- **Added**: `references/workflow-multi-skill.md` — composition with `/office-hours`, `/plan-ceo-review`, `nano-banana-pro` for full proposal workflow
- **Fixed**: inline `<span>` with `margin-*` rejected by `html2pptx.js` — use `padding-*` instead (caught in stats layout)
- **Fixed**: `linear-gradient` on `div` background rejected by `html2pptx.js` — use solid color or move gradient into image
- **Changed**: migrated from `~/.claude/skills/` into this repo for proper version control; symlink via `bin/dev-setup`

### 0.1.0 — 2026-04-xx
- Initial skill extracted from `business-outlook/deck-visual/` pipeline
- Layouts: `slide-cover` (HF), `slide-quote`, `slide-r34`, `slide-l34`
- HTML → PPTX pipeline via playwright + pptxgenjs + sharp
- Safe-zone typography contract; overflow-to-notes discipline
- Nano Banana V2 four-section image prompt format
- Minimal runnable example at `examples/minimal/`

---

## Repo infrastructure

### 2026-04-15
- Added `bin/dev-setup` + `bin/dev-teardown` — symlink skills into `~/.claude/skills/` for live local development (pattern from gstack)
- Added per-skill `version` field in SKILL.md frontmatter
- Added this CHANGELOG
