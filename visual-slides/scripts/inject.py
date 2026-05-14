#!/usr/bin/env python3
"""Inject a content-plan into a master Google Slides template via the gws CLI.

Pipeline:
    1. Validate content-plan.json
    2. Copy master template -> working deck
    3. Upload each referenced image to Drive (folder from plan), make public-readable
    4. Build a batchUpdate request list:
         - replaceAllText for {{pN-...}} text placeholders
         - replaceAllShapesWithImage for {{pN-img-...}} image placeholders
         - replaceAllText for {{pN-notes}} speaker notes
    5. Apply batchUpdate
    6. Print the final deck URL

Usage:
    python inject.py content-plan.json                 # real run
    python inject.py content-plan.json --dry-run       # print requests, no changes
    python inject.py content-plan.json --keep-images   # don't re-upload if image
                                                       # cache file lists the same path

Authentication:
    Requires `gws` on PATH and a prior `gws auth login`.
    See references/gws-cli-cheatsheet.md.
"""

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ---------- gws subprocess helpers ----------


def gws_check_installed() -> None:
    if shutil.which("gws") is None:
        sys.exit("error: `gws` not on PATH. See references/gws-cli-cheatsheet.md to install.")


def gws_call(
    args: list[str],
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    upload_file: Path | None = None,
) -> dict[str, Any]:
    cmd = ["gws", *args]
    if params is not None:
        cmd += ["--params", json.dumps(params)]
    if body is not None:
        cmd += ["--json", json.dumps(body)]
    if upload_file is not None:
        cmd += ["--upload", str(upload_file)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(
            f"gws call failed: {' '.join(cmd[:3])}...\n"
            f"  stderr: {result.stderr.strip()}\n"
            f"  stdout: {result.stdout.strip()}"
        )
    if not result.stdout.strip():
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"_raw": result.stdout}


def drive_copy(source_id: str, new_name: str) -> str:
    out = gws_call(
        ["drive", "files", "copy"],
        params={"fileId": source_id},
        body={"name": new_name},
    )
    return out["id"]


def drive_upload(local_path: Path, parent_folder_id: str) -> str:
    out = gws_call(
        ["drive", "files", "create"],
        body={"name": local_path.name, "parents": [parent_folder_id]},
        upload_file=local_path,
    )
    return out["id"]


def drive_make_public(file_id: str) -> None:
    gws_call(
        ["drive", "permissions", "create"],
        params={"fileId": file_id},
        body={"role": "reader", "type": "anyone"},
    )


def slides_batch_update(presentation_id: str, requests: list[dict[str, Any]]) -> None:
    gws_call(
        ["slides", "presentations", "batchUpdate"],
        params={"presentationId": presentation_id},
        body={"requests": requests},
    )


# ---------- content-plan parsing ----------


@dataclass
class SlideEntry:
    page: int
    text: dict[str, str] = field(default_factory=dict)
    image: dict[str, str] = field(default_factory=dict)  # key -> local image path
    notes: str | None = None


@dataclass
class Plan:
    title: str
    template_deck_id: str
    drive_image_folder_id: str
    output_deck_title: str
    slides: list[SlideEntry]


def load_plan(path: Path) -> Plan:
    raw = json.loads(path.read_text())
    slides = [
        SlideEntry(
            page=int(s["page"]),
            text=s.get("text") or {},
            image=s.get("image") or {},
            notes=s.get("notes"),
        )
        for s in raw["slides"]
    ]
    return Plan(
        title=raw["title"],
        template_deck_id=raw["templateDeckId"],
        drive_image_folder_id=raw["driveImageFolderId"],
        output_deck_title=raw.get("outputDeckTitle", raw["title"]),
        slides=slides,
    )


# ---------- request building ----------


def drive_image_url(file_id: str) -> str:
    # The Slides server fetches this URL. Requires the file to be readable
    # by "anyone with link" (set by drive_make_public above).
    return f"https://drive.google.com/uc?export=view&id={file_id}"


def build_requests(plan: Plan, image_id_map: dict[str, str]) -> list[dict[str, Any]]:
    """image_id_map: local_path_str -> Drive fileId"""
    requests: list[dict[str, Any]] = []
    for slide in plan.slides:
        for key, value in slide.text.items():
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": f"{{{{p{slide.page}-{key}}}}}", "matchCase": True},
                        "replaceText": value,
                    }
                }
            )
        for key, local_path in slide.image.items():
            file_id = image_id_map[local_path]
            requests.append(
                {
                    "replaceAllShapesWithImage": {
                        "imageReplaceMethod": "CENTER_INSIDE",
                        "containsText": {"text": f"{{{{p{slide.page}-img-{key}}}}}", "matchCase": True},
                        "imageUrl": drive_image_url(file_id),
                    }
                }
            )
        if slide.notes is not None:
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": f"{{{{p{slide.page}-notes}}}}", "matchCase": True},
                        "replaceText": slide.notes,
                    }
                }
            )
    return requests


# ---------- main ----------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", type=Path, help="content-plan.json")
    parser.add_argument("--dry-run", action="store_true", help="print requests without applying")
    parser.add_argument("--output-json", type=Path, help="write generated batchUpdate body to this path")
    args = parser.parse_args()

    plan = load_plan(args.plan)
    plan_dir = args.plan.parent

    # 1. Resolve all image paths relative to the plan file
    image_paths: dict[str, Path] = {}
    for slide in plan.slides:
        for key, rel_path in slide.image.items():
            full = (plan_dir / rel_path).resolve()
            if not full.exists():
                sys.exit(f"error: image not found for p{slide.page}-img-{key}: {full}")
            image_paths[rel_path] = full

    if args.dry_run:
        print(f"[dry-run] would copy template {plan.template_deck_id} -> '{plan.output_deck_title}'")
        for rel, full in image_paths.items():
            print(f"[dry-run] would upload {rel} ({full.stat().st_size:,} bytes) to folder {plan.drive_image_folder_id}")
        # use placeholder IDs so the requests JSON is shape-correct
        fake_map = {rel: f"<FAKE_ID_{i}>" for i, rel in enumerate(image_paths)}
        requests = build_requests(plan, fake_map)
        out_body = {"requests": requests}
        if args.output_json:
            args.output_json.write_text(json.dumps(out_body, ensure_ascii=False, indent=2))
            print(f"[dry-run] wrote {len(requests)} requests to {args.output_json}")
        else:
            print(json.dumps(out_body, ensure_ascii=False, indent=2))
        return 0

    gws_check_installed()

    # 2. Copy template
    print(f"copying template {plan.template_deck_id} -> '{plan.output_deck_title}'")
    new_deck_id = drive_copy(plan.template_deck_id, plan.output_deck_title)
    print(f"  new deck id: {new_deck_id}")

    # 3. Upload images and make public-readable
    image_id_map: dict[str, str] = {}
    for rel, full in image_paths.items():
        print(f"uploading {rel} ({full.stat().st_size:,} bytes)...")
        file_id = drive_upload(full, plan.drive_image_folder_id)
        drive_make_public(file_id)
        image_id_map[rel] = file_id
        print(f"  -> {file_id} (public-readable)")

    # 4. Build + apply batchUpdate
    requests = build_requests(plan, image_id_map)
    print(f"applying {len(requests)} requests to deck {new_deck_id}...")
    if args.output_json:
        args.output_json.write_text(json.dumps({"requests": requests}, ensure_ascii=False, indent=2))
    slides_batch_update(new_deck_id, requests)

    url = f"https://docs.google.com/presentation/d/{new_deck_id}/edit"
    print(f"\ndone: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
