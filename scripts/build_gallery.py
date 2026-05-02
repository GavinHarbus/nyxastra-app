#!/usr/bin/env python3
"""
Extract preview images from .nyxtemplate files and regenerate showcase READMEs.

Usage:
    python3 scripts/build_gallery.py

Run this after adding/removing/updating .nyxtemplate files in templates/.
It will:
  1. Extract cover images from all .nyxtemplate files → templates/previews/
  2. Compress to 480px-wide JPEG thumbnails
  3. Regenerate README.md for each category folder
  4. Regenerate the main templates/README.md gallery index
"""

import json
import base64
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
PREVIEWS_DIR = TEMPLATES_DIR / "previews"

THUMB_WIDTH = 480
JPEG_QUALITY = 80

# ──────────────────────────────────────────────
# 1. Scan templates
# ──────────────────────────────────────────────

def scan_templates():
    """Walk templates/ and parse every .nyxtemplate file."""
    templates = []
    for path in sorted(TEMPLATES_DIR.rglob("*.nyxtemplate")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        folder = path.parent.relative_to(TEMPLATES_DIR)
        folder_name = str(folder) if str(folder) != "." else ""

        name = data.get("name", path.stem)
        safe_name = name.replace(" ", "_").replace("·", "-").replace("/", "-")
        variables = [v["name"] for v in data.get("variables", [])]
        tags = data.get("tags", [])
        body = data.get("body", "")
        cover = data.get("cover")
        has_cover = cover is not None and "dataBase64" in cover

        templates.append({
            "path": path,
            "folder": folder_name,
            "name": name,
            "safe_name": safe_name,
            "body": body,
            "variables": variables,
            "tags": tags,
            "cover": cover if has_cover else None,
        })

    return templates


# ──────────────────────────────────────────────
# 2. Extract & compress cover images
# ──────────────────────────────────────────────

def extract_previews(templates):
    """Decode base64 covers and compress to JPEG thumbnails."""
    PREVIEWS_DIR.mkdir(exist_ok=True)

    # Track which preview files we create so we can clean stale ones
    created = set()

    for t in templates:
        if t["cover"] is None:
            continue

        img_bytes = base64.b64decode(t["cover"]["dataBase64"])
        out_jpg = PREVIEWS_DIR / f"{t['safe_name']}.jpg"
        tmp_png = PREVIEWS_DIR / f"{t['safe_name']}_tmp.png"

        tmp_png.write_bytes(img_bytes)

        subprocess.run(
            [
                "sips",
                "--resampleWidth", str(THUMB_WIDTH),
                "--setProperty", "format", "jpeg",
                "--setProperty", "formatOptions", str(JPEG_QUALITY),
                str(tmp_png),
                "--out", str(out_jpg),
            ],
            capture_output=True,
        )
        tmp_png.unlink()

        size_kb = out_jpg.stat().st_size // 1024
        print(f"  {out_jpg.name}  ({size_kb} KB)")
        created.add(out_jpg.name)

    # Remove stale previews
    for f in PREVIEWS_DIR.iterdir():
        if f.suffix == ".jpg" and f.name not in created:
            print(f"  [removed stale] {f.name}")
            f.unlink()

    return created


# ──────────────────────────────────────────────
# 3. Generate category READMEs
# ──────────────────────────────────────────────

CATEGORY_DESCRIPTIONS = {
    "photo":            "Cinematic portraits, product photography, and realistic styles.",
    "illustration":     "Anime, watercolor, pixel art, posters, ink art, and more.",
    "branding":         "Logos, icons, and brand assets.",
    "Universal Briefs": "Production-ready templates with detailed creative briefs.",
    # Add new categories here. Unknown folders fall back to their name.
}

def brief_description(body: str, max_len: int = 120) -> str:
    """First sentence or first max_len chars of the prompt body,
    with {{variable}} placeholders stripped for readability."""
    import re
    text = body.strip()
    # Strip system-prompt-style preambles
    for prefix in ("You are designing", "You are creating"):
        if text.startswith(prefix):
            text = text[len("You are "):]
            break
    # Remove {{variable}} placeholders
    text = re.sub(r"\{\{[^}]+\}\}", "", text)
    # Collapse whitespace
    text = re.sub(r"[ ,，]+", " ", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    # Take first sentence
    for end in (".", "。", "\n"):
        idx = text.find(end)
        if 0 < idx < max_len:
            return text[: idx + 1]
    return text[:max_len] + "..."


def generate_category_readme(folder: str, templates: list):
    """Write a README.md for one category folder."""
    folder_path = TEMPLATES_DIR / folder
    desc = CATEGORY_DESCRIPTIONS.get(folder, "")

    lines = [
        f"# {folder.replace('_', ' ').title()} Templates\n",
        f"{desc}\n",
        '> **How to use:** Click a `.nyxtemplate` file → Download → Double-click to import into NyxAstra.\n',
    ]

    for t in templates:
        filename = t["path"].name
        encoded_filename = quote(filename)
        preview_path = f"../previews/{t['safe_name']}.jpg"
        var_list = ", ".join(f"`{v}`" for v in t["variables"]) if t["variables"] else "*(none)*"
        desc_text = brief_description(t["body"])

        lines.append("---\n")
        lines.append(f"## {t['name']}\n")
        lines.append(f"{desc_text}\n")
        lines.append(f"**Variables:** {var_list}\n")

        if t["cover"] is not None:
            lines.append(f'<p align="center">')
            lines.append(f'  <img src="{preview_path}" width="400" alt="{t["name"]}">')
            lines.append(f'</p>\n')

        lines.append(f"[Download template]({encoded_filename})\n")

    readme_path = folder_path / "README.md"
    readme_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {readme_path.relative_to(REPO_ROOT)}")


# ──────────────────────────────────────────────
# 4. Generate main gallery index
# ──────────────────────────────────────────────

def generate_gallery_index(all_templates: list):
    """Write the top-level templates/README.md."""
    # Group by folder
    folders = {}
    for t in all_templates:
        folders.setdefault(t["folder"], []).append(t)

    total = len(all_templates)

    # Category table
    cat_rows = []
    for folder, items in sorted(folders.items()):
        encoded = quote(folder)
        desc = CATEGORY_DESCRIPTIONS.get(folder, folder.replace("_", " ").title())
        cat_rows.append(f"| [{folder}]({encoded}/) | {len(items)} | {desc} |")

    # Pick up to 9 templates with covers for the preview grid
    with_covers = [t for t in all_templates if t["cover"] is not None]
    grid_items = with_covers[:9]

    # Build 3-column grid
    grid_lines = []
    for i in range(0, len(grid_items), 3):
        row = grid_items[i : i + 3]
        img_cells = " | ".join(
            f"![](previews/{t['safe_name']}.jpg)" for t in row
        )
        label_cells = " | ".join(
            f"[{t['name']}]({quote(t['folder'])}/)".strip() for t in row
        )
        # Pad if fewer than 3
        while img_cells.count("|") < 2:
            img_cells += " | "
            label_cells += " | "
        grid_lines.append(f"| {img_cells} |")
        grid_lines.append(f"| {label_cells} |")

    grid_header = "| | | |\n|:---:|:---:|:---:|"

    content = f"""\
# NyxAstra Template Gallery

Curated prompt templates for [NyxAstra](../README.md). Browse the previews below, download what you like, and double-click to import.

## Categories

| Category | Templates | Description |
|----------|:---------:|-------------|
{chr(10).join(cat_rows)}

**{total} templates total** — click a category to see previews and download.

---

## Quick Preview

{grid_header}
{chr(10).join(grid_lines)}

---

## How to use

1. Click a `.nyxtemplate` file → **Download**
2. Double-click the file, or drag it into NyxAstra's Templates view
3. Fill in the variables and generate

## Create & share your own

1. In NyxAstra, design a prompt with `{{{{variables}}}}`
2. Right-click the template → **Export as .nyxtemplate**
3. [Open an issue](https://github.com/GavinHarbus/nyxastra-app/issues/new) with your file attached to share it here
"""

    index_path = TEMPLATES_DIR / "README.md"
    index_path.write_text(content, encoding="utf-8")
    print(f"  {index_path.relative_to(REPO_ROOT)}")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    print(f"Scanning {TEMPLATES_DIR} ...\n")
    templates = scan_templates()
    print(f"Found {len(templates)} templates\n")

    if not templates:
        print("No .nyxtemplate files found. Nothing to do.")
        sys.exit(0)

    print("Extracting previews:")
    extract_previews(templates)

    print("\nGenerating category READMEs:")
    folders = {}
    for t in templates:
        if t["folder"]:
            folders.setdefault(t["folder"], []).append(t)
    for folder, items in sorted(folders.items()):
        generate_category_readme(folder, items)

    print("\nGenerating gallery index:")
    generate_gallery_index(templates)

    print(f"\nDone. {len(templates)} templates processed.")


if __name__ == "__main__":
    main()
