#!/usr/bin/env python3
"""Bake a translucent dark overlay into background PNGs.

Google Slides has no CSS gradient. To keep foreground text legible on
Nano Banana-generated backgrounds, the scrim must be composited into the
PNG before the image is uploaded to Drive and referenced from a Slides
shape.

Usage:
    python scrim_bake.py images/bg-01-cover.png 0.55
    python scrim_bake.py images/bg-01.png 0.55 images/bg-02.png 0.70 ...
    python scrim_bake.py --config scrim.json
    python scrim_bake.py --dir ./images --alpha 0.65   # batch, same alpha

Alpha guidance:
    cover / closing (sparse text):  0.45 - 0.55
    standard slide:                 0.60 - 0.65
    dense grid (many cards):        0.70 - 0.75
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def bake(src: Path, alpha: float) -> Path:
    if not src.exists():
        raise FileNotFoundError(f"source not found: {src}")
    if not 0 <= alpha <= 1:
        raise ValueError(f"alpha must be 0..1, got {alpha}")

    out = src.with_name(src.stem + "-scrimmed" + src.suffix)
    base = Image.open(src).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (10, 10, 10, int(round(alpha * 255))))
    composited = Image.alpha_composite(base, overlay)
    composited.save(out, format="PNG")
    return out


def parse_pairs(argv: list[str]) -> list[tuple[Path, float]]:
    if len(argv) % 2:
        raise SystemExit("positional args must come in (path, alpha) pairs")
    return [(Path(argv[i]), float(argv[i + 1])) for i in range(0, len(argv), 2)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pairs", nargs="*", help="alternating path alpha path alpha ...")
    parser.add_argument("--config", type=Path, help='JSON file: [{"file": "x.png", "alpha": 0.6}, ...]')
    parser.add_argument("--dir", type=Path, help="batch a whole directory of .png files with --alpha")
    parser.add_argument("--alpha", type=float, help="alpha value when using --dir")
    args = parser.parse_args()

    jobs: list[tuple[Path, float]] = []
    if args.config:
        for entry in json.loads(args.config.read_text()):
            jobs.append((Path(entry["file"]), float(entry["alpha"])))
    if args.dir:
        if args.alpha is None:
            raise SystemExit("--dir requires --alpha")
        jobs.extend((p, args.alpha) for p in sorted(args.dir.glob("*.png")) if "-scrimmed" not in p.stem)
    if args.pairs:
        jobs.extend(parse_pairs(args.pairs))

    if not jobs:
        parser.print_help()
        return 1

    for src, alpha in jobs:
        out = bake(src, alpha)
        print(f"  baked {src.name} @ alpha={alpha} -> {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
