#!/usr/bin/env python3
"""One-shot migration of the legacy `templates/<category>/<name>.nyxtemplate`
layout into the new `community/templates/<slug>/{template.json,cover.*,meta.yml}`
form.

Run once after merging the community-pipeline PR. Idempotent: re-running
will overwrite any matching slug directories with the latest source from
the legacy folder, so it's safe to re-run after editing the legacy files.

Usage:
    python3 community/scripts/migrate_legacy.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make `from lib...` work when invoked from any cwd.
sys.path.insert(0, str(Path(__file__).parent))

import yaml  # noqa: E402

from lib.unpack import unpack_nyxtemplate  # noqa: E402
from lib.utils import REPO_ROOT, TEMPLATES_DIR, cover_extension  # noqa: E402


# Legacy folder name → (gallery category, default locale). Categories
# below are the ones promoted to the canonical VALID_CATEGORIES set in
# lib/schema.py. Locales are inferred from the bundled starter pack's
# actual content, not detected at runtime.
LEGACY_CATEGORY_MAP: dict = {
    "photo":            ("photo",        "zh-CN"),
    "illustration":     ("illustration", "zh-CN"),
    "branding":         ("branding",     "zh-CN"),
    "Universal Briefs": ("universal",    "en"),
}

STARTER_PACK_AUTHOR_NAME = "Gavin Schnee"
STARTER_PACK_AUTHOR_URL  = "https://x.com/Alaric4678"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would be migrated; don't write anything.")
    args = parser.parse_args()

    legacy_root = REPO_ROOT / "templates"
    if not legacy_root.exists():
        print(f"No legacy templates/ directory at {legacy_root} — nothing to migrate.")
        return 0

    sources = sorted(legacy_root.rglob("*.nyxtemplate"))
    if not sources:
        print(f"No .nyxtemplate files found under {legacy_root}.")
        return 0

    print(f"Migrating {len(sources)} legacy templates into {TEMPLATES_DIR.relative_to(REPO_ROOT)}/\n")

    migrated = 0
    skipped = []  # list of (path, reason)

    for src in sources:
        rel = src.relative_to(legacy_root)
        legacy_folder = rel.parts[0] if len(rel.parts) > 1 else ""
        category, locale = LEGACY_CATEGORY_MAP.get(legacy_folder, ("other", "universal"))

        try:
            raw = src.read_bytes()
            unpacked = unpack_nyxtemplate(
                raw,
                source_filename=str(rel),
                default_category=category,
                default_locale=locale,
                featured=True,
                author_name_override=STARTER_PACK_AUTHOR_NAME,
            )
        except Exception as exc:  # noqa: BLE001 — surface unexpected failures
            skipped.append((src, f"unexpected error: {exc}"))
            continue

        if unpacked.result.errors:
            print(f"  ✗ {rel}  — validation errors:")
            for issue in unpacked.result.errors:
                print(f"      • {issue}")
            skipped.append((src, "validation errors"))
            continue

        # Force the starter-pack author URL on top of the unpack stub.
        unpacked.meta["author"]["url"] = STARTER_PACK_AUTHOR_URL

        target_dir = TEMPLATES_DIR / unpacked.slug
        if args.dry_run:
            print(f"  ✓ {rel}  →  {target_dir.relative_to(REPO_ROOT)}/  (dry run)")
        else:
            _write_template_dir(target_dir, unpacked)
            print(f"  ✓ {rel}  →  {target_dir.relative_to(REPO_ROOT)}/")
        migrated += 1

    print()
    print(f"Migrated: {migrated}   Skipped: {len(skipped)}")
    if skipped:
        print("\nSkipped files:")
        for path, reason in skipped:
            print(f"  - {path.relative_to(REPO_ROOT)}: {reason}")
    return 0 if not skipped else 1


def _write_template_dir(target_dir: Path, unpacked) -> None:
    """Materialize one UnpackedTemplate to disk."""
    target_dir.mkdir(parents=True, exist_ok=True)

    # template.json — UTF-8, pretty-printed, sorted keys for stable diffs.
    (target_dir / "template.json").write_text(
        json.dumps(unpacked.template_json, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # meta.yml — block style, no flow, UTF-8.
    (target_dir / "meta.yml").write_text(
        yaml.safe_dump(
            unpacked.meta,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        ),
        encoding="utf-8",
    )

    # cover.<ext> — only if we have one.
    if unpacked.cover_bytes and unpacked.cover_format:
        ext = cover_extension(unpacked.cover_format)
        (target_dir / f"cover.{ext}").write_bytes(unpacked.cover_bytes)


if __name__ == "__main__":
    sys.exit(main())
