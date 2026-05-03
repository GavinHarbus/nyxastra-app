#!/usr/bin/env python3
"""Validate every template in `community/templates/` and (optionally) emit
the publishable `community/dist/` artifacts.

Two modes — both run by CI:

    --check         Lint-only. Exit non-zero on any error. Used on PRs
                    so the contributor sees problems before merge.

    --build         Lint + emit `community/dist/`:
                      • dist/index.json                        (gallery manifest)
                      • dist/templates/<slug>.nyxtemplate      (single-file downloads)
                      • dist/covers/<slug>.webp                (1024px optimized)
                      • dist/covers/<slug>.thumb.webp          (480px thumbnail)
                      • dist/manifest.json                     (build metadata)

If neither flag is passed, runs `--check` (safest default for a human
running the script locally).
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from lib.lint import (
    lint_body_for_secrets,
    lint_cover_file,
    lint_slug_uniqueness,
)
from lib.pack import pack_template_dir
from lib.schema import (
    TEMPLATE_SCHEMA_MAX_VERSION,
    ValidationResult,
    validate_meta,
    validate_nyxtemplate,
)
from lib.utils import (
    DIST_COVERS,
    DIST_DIR,
    DIST_INDEX,
    DIST_MANIFEST,
    DIST_TEMPLATES,
    REPO_ROOT,
    TEMPLATES_DIR,
    find_cover_file,
)


# Width caps for the two derived gallery images. Chosen to look sharp on
# Retina displays without ballooning the CDN budget.
COVER_LONG_EDGE   = 1024
THUMB_LONG_EDGE   = 480
WEBP_QUALITY_FULL = 82
WEBP_QUALITY_THUMB = 78

INDEX_SCHEMA      = "nyxastra-community-index"
INDEX_SCHEMA_VERSION = 1


# ──────────────────────────────────────────────────────────────────────
# Discovery
# ──────────────────────────────────────────────────────────────────────

def discover_template_dirs() -> list[Path]:
    """Every immediate child of `community/templates/` that contains a
    `template.json` is treated as a template directory."""
    if not TEMPLATES_DIR.exists():
        return []
    out: list[Path] = []
    for child in sorted(TEMPLATES_DIR.iterdir()):
        if child.is_dir() and (child / "template.json").exists():
            out.append(child)
    return out


# ──────────────────────────────────────────────────────────────────────
# Lint pass
# ──────────────────────────────────────────────────────────────────────

def lint_all(template_dirs: list[Path]) -> tuple[ValidationResult, list[dict]]:
    """Lint every template; return aggregate result and the parsed metadata
    for downstream build steps. The metadata list is in discovery order."""
    aggregate = ValidationResult()
    parsed: list[dict] = []

    for tdir in template_dirs:
        rel = tdir.relative_to(REPO_ROOT)
        local = ValidationResult()

        tpl_path  = tdir / "template.json"
        meta_path = tdir / "meta.yml"
        cover_path = find_cover_file(tdir)

        # template.json
        try:
            tpl_doc = json.loads(tpl_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            local.error("tpl-unreadable", f"Cannot read template.json: {exc}", str(rel))
            _print_local(rel, local)
            aggregate.extend(local)
            continue

        local.extend(validate_nyxtemplate(tpl_doc))
        body = tpl_doc.get("body")
        if isinstance(body, str):
            lint_body_for_secrets(body, local)

        # meta.yml
        if not meta_path.exists():
            local.error("meta-missing-file", f"meta.yml not found in {rel}.", str(rel))
            meta_doc: dict[str, Any] = {}
        else:
            try:
                meta_doc = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            except (OSError, yaml.YAMLError) as exc:
                local.error("meta-unreadable", f"Cannot parse meta.yml: {exc}", str(rel))
                meta_doc = {}
        local.extend(validate_meta(meta_doc, allow_placeholders=False))

        # cover
        if cover_path is None:
            local.warn("cover-missing-file", "No cover file found (cover.png/jpg/webp).", str(rel))
        else:
            lint_cover_file(cover_path, local)

        _print_local(rel, local)
        aggregate.extend(local)
        parsed.append({
            "dir": tdir,
            "template": tpl_doc,
            "meta": meta_doc,
            "cover_path": cover_path,
        })

    # Cross-template: slug uniqueness
    slugs = [p["meta"].get("slug") for p in parsed if isinstance(p["meta"].get("slug"), str)]
    lint_slug_uniqueness(slugs, aggregate)

    return aggregate, parsed


def _print_local(rel: Path, local: ValidationResult) -> None:
    if not local.issues:
        print(f"  ✓ {rel}")
        return
    has_err = any(i.severity == "error" for i in local.issues)
    print(f"  {'✗' if has_err else '·'} {rel}")
    for issue in local.issues:
        print(f"      {issue}")


# ──────────────────────────────────────────────────────────────────────
# Build pass
# ──────────────────────────────────────────────────────────────────────

def build_dist(parsed: list[dict]) -> None:
    """Materialize `community/dist/` from the lint-pass output."""
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    DIST_TEMPLATES.mkdir(parents=True, exist_ok=True)
    DIST_COVERS.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []

    for item in parsed:
        tdir       = item["dir"]
        tpl_doc    = item["template"]
        meta       = item["meta"]
        cover_path = item["cover_path"]
        slug       = meta.get("slug") or tdir.name

        # Single-file .nyxtemplate (re-stamped to the current schema)
        single_bytes = pack_template_dir(tdir)
        out_single = DIST_TEMPLATES / f"{slug}.nyxtemplate"
        out_single.write_bytes(single_bytes)

        # Optimized cover variants (always WebP for the gallery)
        cover_url = thumb_url = None
        if cover_path:
            cover_url = f"covers/{slug}.webp"
            thumb_url = f"covers/{slug}.thumb.webp"
            _emit_webp(cover_path, DIST_COVERS / f"{slug}.webp",
                       max_long_edge=COVER_LONG_EDGE, quality=WEBP_QUALITY_FULL)
            _emit_webp(cover_path, DIST_COVERS / f"{slug}.thumb.webp",
                       max_long_edge=THUMB_LONG_EDGE, quality=WEBP_QUALITY_THUMB)

        entries.append({
            "slug": slug,
            "title": meta.get("title") or tpl_doc.get("name"),
            "category": meta.get("category"),
            "locale": meta.get("locale"),
            "tags": meta.get("tags") or tpl_doc.get("tags") or [],
            "models": meta.get("models", []),
            "license": meta.get("license"),
            "featured": bool(meta.get("featured", False)),
            "nsfw": bool(meta.get("nsfw", False)),
            "author": meta.get("author"),
            "basedOn": meta.get("basedOn"),
            "createdAt": _iso_date(meta.get("createdAt")),
            "promptBody": tpl_doc.get("body"),
            "variables": tpl_doc.get("variables", []),
            "parameterPreset": tpl_doc.get("parameterPreset"),
            "downloadUrl": f"templates/{slug}.nyxtemplate",
            "downloadSize": out_single.stat().st_size,
            "coverUrl": cover_url,
            "thumbnailUrl": thumb_url,
        })

    index = {
        "schema":  INDEX_SCHEMA,
        "version": INDEX_SCHEMA_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "templateSchemaVersion": TEMPLATE_SCHEMA_MAX_VERSION,
        "count": len(entries),
        "templates": entries,
    }
    DIST_INDEX.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "generatedAt": index["generatedAt"],
        "templateSchemaVersion": TEMPLATE_SCHEMA_MAX_VERSION,
        "indexSchemaVersion": INDEX_SCHEMA_VERSION,
        "templateCount": len(entries),
        "categoriesPresent": sorted({e["category"] for e in entries if e["category"]}),
    }
    DIST_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n  → Wrote {DIST_INDEX.relative_to(REPO_ROOT)}  ({len(entries)} templates)")
    print(f"  → Wrote {DIST_TEMPLATES.relative_to(REPO_ROOT)}/*.nyxtemplate")
    print(f"  → Wrote {DIST_COVERS.relative_to(REPO_ROOT)}/*.webp")


def _emit_webp(src: Path, dest: Path, *, max_long_edge: int, quality: int) -> None:
    """Re-encode `src` as a WebP with its long edge clamped to `max_long_edge`."""
    with Image.open(src) as img:
        img.load()
        if img.mode in ("P", "LA"):
            img = img.convert("RGBA")
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        # `method=6` is the slowest/best WebP encoder setting; CI runs are
        # cheap and the difference shows up in visible quality at small
        # thumbnail sizes.
        img.save(dest, format="WEBP", quality=quality, method=6)


def _iso_date(value: Any) -> str | None:
    """Coerce a YAML-decoded date (datetime.date or str) to an ISO string."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Lint only.")
    parser.add_argument("--build", action="store_true", help="Lint, then emit dist/.")
    args = parser.parse_args()

    if not args.check and not args.build:
        args.check = True

    template_dirs = discover_template_dirs()
    print(f"Discovered {len(template_dirs)} template(s) under "
          f"{TEMPLATES_DIR.relative_to(REPO_ROOT)}/\n")

    if not template_dirs:
        print("Nothing to lint or build.")
        return 0

    aggregate, parsed = lint_all(template_dirs)

    err_count  = len(aggregate.errors)
    warn_count = len(aggregate.warnings)
    print(f"\n  Errors: {err_count}   Warnings: {warn_count}")

    if err_count > 0:
        print("\nBuild aborted because of errors above.")
        return 1

    if args.build:
        print("\nBuilding dist/ artifacts…")
        build_dist(parsed)

    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
