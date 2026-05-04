#!/usr/bin/env python3
"""Validate every template in `community/templates/` and (optionally) emit
the publishable `community/dist/` artifacts.

Source of truth: `community/templates/<slug>.nyxtemplate` — one flat
file per template, exported directly from NyxAstra (which embeds the
cover image and `community` block). The filename minus the extension
becomes the slug; CI never rewrites or moves contributor files.

Two modes — both run by CI:

    --check         Lint-only. Exit non-zero on any error. Used on PRs
                    so the contributor sees problems before merge.

    --build         Lint + emit `community/dist/`:
                      • dist/index.json                        (gallery manifest)
                      • dist/templates/<slug>.nyxtemplate      (re-stamped download)
                      • dist/covers/<slug>.webp                (1024px optimized)
                      • dist/covers/<slug>.thumb.webp          (480px thumbnail)
                      • dist/manifest.json                     (build metadata)

If neither flag is passed, runs `--check` (safest default for a human
running the script locally).
"""
from __future__ import annotations

import argparse
import base64
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
    lint_cover_bytes,
)
from lib.schema import (
    TEMPLATE_SCHEMA,
    TEMPLATE_SCHEMA_MAX_VERSION,
    ValidationResult,
    validate_nyxtemplate,
)
from lib.utils import (
    COMMUNITY_DIR,
    DIST_COVERS,
    DIST_DIR,
    DIST_INDEX,
    DIST_MANIFEST,
    DIST_TEMPLATES,
    NYXTEMPLATE_EXT,
    REPO_ROOT,
    TEMPLATES_DIR,
    slugify,
)


# Width caps for the two derived gallery images. Chosen to look sharp on
# Retina displays without ballooning the CDN budget.
COVER_LONG_EDGE    = 1024
THUMB_LONG_EDGE    = 480
WEBP_QUALITY_FULL  = 82
WEBP_QUALITY_THUMB = 78

# Stamp written into every emitted .nyxtemplate so the gallery download
# has clear provenance. Bumped manually when the build does anything
# the macOS app needs to know about.
SOURCE_APP_STAMP = "nyxastra-community"

INDEX_SCHEMA         = "nyxastra-community-index"
INDEX_SCHEMA_VERSION = 1

# Maintainer-only file. Contributors cannot mark themselves featured
# — the only way a template lights up is for a maintainer to add its
# slug here. See `community/featured.yml` for the rationale.
FEATURED_FILE = COMMUNITY_DIR / "featured.yml"


def load_featured_slugs() -> list[str]:
    """Read `community/featured.yml` and return the curated slug list.

    Missing file or empty list returns []. Bad YAML aborts the build
    loudly; we'd rather surface the typo than silently un-feature
    every template.
    """
    if not FEATURED_FILE.exists():
        return []
    raw = yaml.safe_load(FEATURED_FILE.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise SystemExit(f"{FEATURED_FILE.name} must be a mapping with a `featured:` list.")
    items = raw.get("featured") or []
    if not isinstance(items, list):
        raise SystemExit(f"{FEATURED_FILE.name}: `featured` must be a list of slugs.")
    out: list[str] = []
    for entry in items:
        if not isinstance(entry, str) or not entry.strip():
            raise SystemExit(f"{FEATURED_FILE.name}: every entry must be a non-empty string.")
        out.append(entry.strip())
    return out


# ──────────────────────────────────────────────────────────────────────
# Discovery
# ──────────────────────────────────────────────────────────────────────

def discover_template_files() -> list[Path]:
    """Every `*.nyxtemplate` directly under `community/templates/`."""
    if not TEMPLATES_DIR.exists():
        return []
    out: list[Path] = []
    for child in sorted(TEMPLATES_DIR.iterdir()):
        if child.is_file() and child.suffix == NYXTEMPLATE_EXT:
            out.append(child)
    return out


# ──────────────────────────────────────────────────────────────────────
# Lint pass
# ──────────────────────────────────────────────────────────────────────

def lint_all(template_files: list[Path]) -> tuple[ValidationResult, list[dict]]:
    """Lint every template; return aggregate result and the parsed payload
    for downstream build steps. The list is in discovery order."""
    aggregate = ValidationResult()
    parsed: list[dict] = []
    seen_slugs: dict[str, Path] = {}

    for tpath in template_files:
        rel = tpath.relative_to(REPO_ROOT)
        local = ValidationResult()

        slug = tpath.stem  # filename without `.nyxtemplate`
        if not slug:
            local.error("slug-empty", "Filename has no stem.", str(rel))
            _print_local(rel, local)
            aggregate.extend(local)
            continue

        # Filename hygiene: must match the slug rule we suggest in the docs.
        # Using slugify on the filename itself makes this idempotent — if
        # slugify(slug) != slug, the contributor used characters we don't
        # allow in URLs.
        if slugify(slug) != slug:
            local.error(
                "slug-not-clean",
                f"Filename {tpath.name!r} contains characters not allowed in a slug. "
                f"Suggested rename: {slugify(slug)}{NYXTEMPLATE_EXT}.",
                str(rel),
            )

        if slug.lower() in {s.lower() for s in seen_slugs}:
            other = seen_slugs[next(s for s in seen_slugs if s.lower() == slug.lower())]
            local.error(
                "slug-collision",
                f"Filename {tpath.name!r} collides (case-insensitively) with "
                f"{other.relative_to(REPO_ROOT)}.",
                str(rel),
            )
        else:
            seen_slugs[slug] = tpath

        # Parse the .nyxtemplate file as JSON.
        try:
            doc = json.loads(tpath.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            local.error("file-unreadable", f"Cannot parse JSON: {exc}", str(rel))
            _print_local(rel, local)
            aggregate.extend(local)
            continue

        local.extend(validate_nyxtemplate(doc, require_community=True))

        body = doc.get("body")
        if isinstance(body, str):
            lint_body_for_secrets(body, local)

        # Decode and lint the embedded cover (if any). `validate_nyxtemplate`
        # has already error-ed if the cover field is malformed, but it
        # doesn't decode the bytes — that's our job here.
        cover_bytes: bytes | None = None
        cover = doc.get("cover")
        if isinstance(cover, dict):
            data_b64 = cover.get("dataBase64")
            if isinstance(data_b64, str) and data_b64:
                try:
                    cover_bytes = base64.b64decode(data_b64, validate=True)
                except (ValueError, base64.binascii.Error) as exc:
                    local.error("cover-base64", f"`cover.dataBase64` is not valid base64: {exc}", "cover.dataBase64")
            if cover_bytes is not None:
                lint_cover_bytes(cover_bytes, expected_format=cover.get("format"), r=local)

        _print_local(rel, local)
        aggregate.extend(local)
        parsed.append({
            "path": tpath,
            "slug": slug,
            "doc": doc,
            "cover_bytes": cover_bytes,
        })

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

    featured_slugs = load_featured_slugs()
    known_slugs = {item["slug"] for item in parsed}
    unknown_featured = [s for s in featured_slugs if s not in known_slugs]
    if unknown_featured:
        # Don't fail the build — a slug may be transiently missing during
        # a rename PR. Surface it loudly so a maintainer notices.
        print("  ! featured.yml references unknown slug(s):")
        for s in unknown_featured:
            print(f"      - {s}")
    featured_set = set(featured_slugs) & known_slugs

    entries: list[dict[str, Any]] = []

    for item in parsed:
        slug        = item["slug"]
        doc         = item["doc"]
        cover_bytes = item["cover_bytes"]

        # Re-stamp the .nyxtemplate so the gallery download is recognizable.
        # We never modify the contributor's source file, only the published
        # copy in dist/.
        stamped = dict(doc)
        stamped["schema"]    = TEMPLATE_SCHEMA
        stamped["version"]   = TEMPLATE_SCHEMA_MAX_VERSION
        stamped["sourceApp"] = SOURCE_APP_STAMP

        out_single = DIST_TEMPLATES / f"{slug}{NYXTEMPLATE_EXT}"
        out_single.write_text(
            json.dumps(stamped, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )

        # Optimized cover variants (always WebP for the gallery).
        cover_url = thumb_url = None
        if cover_bytes:
            cover_url = f"covers/{slug}.webp"
            thumb_url = f"covers/{slug}.thumb.webp"
            _emit_webp(cover_bytes, DIST_COVERS / f"{slug}.webp",
                       max_long_edge=COVER_LONG_EDGE, quality=WEBP_QUALITY_FULL)
            _emit_webp(cover_bytes, DIST_COVERS / f"{slug}.thumb.webp",
                       max_long_edge=THUMB_LONG_EDGE, quality=WEBP_QUALITY_THUMB)

        community = doc.get("community") or {}
        entries.append({
            "slug": slug,
            "title": doc.get("name"),
            "category": community.get("category"),
            "tags": doc.get("tags") or [],
            "license": community.get("license"),
            "featured": slug in featured_set,
            "author": community.get("author"),
            "promptBody": doc.get("body"),
            "variables": doc.get("variables", []),
            "parameterPreset": doc.get("parameterPreset"),
            "downloadUrl": f"templates/{slug}{NYXTEMPLATE_EXT}",
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


def _emit_webp(src_bytes: bytes, dest: Path, *, max_long_edge: int, quality: int) -> None:
    """Re-encode in-memory cover bytes as a WebP with its long edge clamped."""
    with Image.open(io.BytesIO(src_bytes)) as img:
        img.load()
        if img.mode in ("P", "LA"):
            img = img.convert("RGBA")
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
            img = img.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))),
                Image.LANCZOS,
            )
        # `method=6` is the slowest/best WebP encoder setting; CI runs are
        # cheap and the difference shows up in visible quality at small
        # thumbnail sizes.
        img.save(dest, format="WEBP", quality=quality, method=6)


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

    template_files = discover_template_files()
    print(f"Discovered {len(template_files)} template(s) under "
          f"{TEMPLATES_DIR.relative_to(REPO_ROOT)}/\n")

    if not template_files:
        print("Nothing to lint or build.")
        return 0

    aggregate, parsed = lint_all(template_files)

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
