#!/usr/bin/env python3
"""Lint a content-plan.json before sending it to inject.py.

Catches the classes of errors that cost a Drive round-trip:
    - duplicate page numbers
    - non-kebab-case or non-ASCII keys (Slides matchCase is byte-exact)
    - missing image files
    - Drive IDs that look obviously wrong (URL pasted, too short)
    - {{pN-notes}} stored at the wrong level (must be slide.notes, not slide.text.notes)

Exit codes:
    0 — clean
    1 — at least one error
"""

import argparse
import json
import re
import sys
from pathlib import Path

KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DRIVE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def validate(plan_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        plan = json.loads(plan_path.read_text())
    except json.JSONDecodeError as e:
        return [f"plan is not valid JSON: {e}"]

    plan_dir = plan_path.parent

    for required in ("title", "templateDeckId", "driveImageFolderId", "slides"):
        if required not in plan:
            errors.append(f"missing top-level key: {required}")
    if errors:
        return errors

    for id_field in ("templateDeckId", "driveImageFolderId"):
        if not DRIVE_ID_RE.match(plan[id_field]):
            errors.append(
                f"{id_field} doesn't look like a Drive ID (got {plan[id_field]!r}); "
                "paste only the ID, not the full URL"
            )

    seen_pages: set[int] = set()
    for i, slide in enumerate(plan["slides"]):
        if "page" not in slide:
            errors.append(f"slides[{i}] missing 'page'")
            continue
        page = slide["page"]
        if page in seen_pages:
            errors.append(f"slides[{i}] duplicate page number {page}")
        seen_pages.add(page)

        for key in (slide.get("text") or {}):
            if not KEY_RE.match(key):
                errors.append(
                    f"p{page} text key {key!r} is not kebab-case ASCII; "
                    "use lowercase letters, digits, hyphens (placeholder grammar)"
                )
            if key == "notes":
                errors.append(
                    f"p{page} 'notes' should be at slide.notes, not slide.text.notes "
                    "(different replacement scope)"
                )
        for key, rel in (slide.get("image") or {}).items():
            if not KEY_RE.match(key):
                errors.append(f"p{page} image key {key!r} is not kebab-case ASCII")
            full = (plan_dir / rel).resolve()
            if not full.exists():
                errors.append(f"p{page} image missing: {rel} (resolved: {full})")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path)
    args = parser.parse_args()

    errors = validate(args.plan)
    if errors:
        print(f"{len(errors)} error(s) in {args.plan}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"ok: {args.plan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
