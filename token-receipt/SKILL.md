---
name: token-receipt
description: Generate a printer-receipt styled PNG bill of AI token usage and cost from local ccusage data, for the 绿皮火车 channel. Use when the user wants a token usage "账单"/"小票"/"收银台"/receipt/invoice, a shareable spend breakdown by model / input / output / cached / by day, or 节目素材 about token 消耗/花费. Triggers on "生成账单", "token 收据", "做张小票", "用量账单", "token receipt", "spend breakdown image".
metadata:
  type: personal
  channel: 绿皮火车 (Green Train Express)
---

# token-receipt

Turns real `ccusage` usage data into a fun, printer-receipt styled PNG bill —
designed as 节目 (show) material for the **绿皮火车** channel's token-consumption
segments. The receipt shows token usage, a token-type mix bar, cost broken down
by model, and a per-day spend chart, ending in a big TOTAL.

## When to use

- "帮我生成 (这个月/这周的) token 账单 / 小票 / 收据"
- "做张图展示我的 token 花在哪了 / 花费分布"
- "节目里要讲 token 消耗,给我一张可上镜的账单图"
- English: "make a token usage receipt", "spend breakdown image by model/day"

## Prerequisites (all already present on this Mac)

- `ccusage` CLI on PATH (`ccusage --version`)
- Google Chrome at `/Applications/Google Chrome.app` (headless screenshot)
- ImageMagick `magick` (auto-trims the screenshot to the receipt edge)
- `python3` (stdlib only — no pip installs)

## Usage

```bash
# Latest month, all agents → ~/Desktop/token-receipt-YYYY-MM.png
python3 scripts/gen_receipt.py

# This week
python3 scripts/gen_receipt.py --period week

# A specific month or a specific week (week = its start date)
python3 scripts/gen_receipt.py --period month --which 2026-05
python3 scripts/gen_receipt.py --period week  --which 2026-06-15

# One agent only (claude / codex / opencode / pi / ...); default = all agents
python3 scripts/gen_receipt.py --agent claude

# Custom name, output path, sharper export, or HTML-only (tweak the design)
python3 scripts/gen_receipt.py --customer "绿皮火车" --out ~/Desktop/bill.png
python3 scripts/gen_receipt.py --scale 3
python3 scripts/gen_receipt.py --html-only   # writes .html, open in a browser
```

The script prints the output path on success.

### Options

| Flag | Default | Meaning |
|------|---------|---------|
| `--period` | `month` | `month` or `week` billing cycle |
| `--which` | `latest` | `latest`, or `YYYY-MM` (month) / `YYYY-MM-DD` week-start |
| `--agent` | all | restrict to one ccusage agent |
| `--customer` | `Burn Wang` | name printed on the receipt (or `RECEIPT_CUSTOMER` env) |
| `--out` | `~/Desktop/token-receipt-<period>.png` | output path |
| `--scale` | `2` | device scale factor (2 = retina; 3 = bigger) |
| `--html-only` | off | emit HTML instead of PNG (for design tweaks) |

## How it works

1. Pulls JSON from `ccusage <agent?> <monthly|weekly>` and, for the per-day
   chart, `ccusage daily` filtered to the chosen month/week window.
2. Shapes it into receipt sections and renders a self-contained HTML
   (monospace, dotted leader lines, ASCII train, CSS barcode, torn edges).
3. Screenshots with headless Chrome at retina scale, then `magick -trim` crops
   to the receipt and adds an even margin.

## Honesty notes (matters for the show)

- Numbers are best-effort **estimates from local logs**, not a real billing API
  (stated on the receipt footer).
- ccusage exposes **cost per model**, not cost per token-type. So the receipt
  splits **cost by model** (accurate) and **token volume by type** (accurate);
  it never fabricates a per-token-type dollar split.
- Cache-read tokens dominate *volume* (often ~95%) and are cheap *per token*
  (~1/10 of input), but at heavy-usage volume they can still be the **largest
  cost line** — verified: in one June sample cache-read was 96% of opus-4-8
  tokens and 61% of its cost. The real point: caching saves ~10x vs paying full
  input price for that re-sent context. The footer states this.

## Customizing the look

Open `scripts/gen_receipt.py`:
- `TRAIN` — the ASCII art header.
- `TOKEN_KINDS` — token categories, labels, and colors of the mix bar.
- The `<style>` block in `build_html` — paper color, accent (`--accent`,
  currently green-train teal `#1f6f5c`), fonts, spacing.
Iterate fast with `--html-only`, then re-render to PNG.
