#!/usr/bin/env python3
"""Process pending submissions in `community/submissions/`.

For every `.nyxtemplate` in the inbox:
  1. Lint it (full schema + secret scan + cover validity).
  2. If it passes, unpack it into `community/templates/<slug>/`.
  3. Delete the original `.nyxtemplate` from the inbox.

Designed to be run by CI on PRs that touch `community/submissions/**`.
The CI then commits the resulting changes back to the PR branch, so the
contributor sees a clean unpacked diff in the next CI iteration.

Exit code:
    0  — every submission processed successfully (or no submissions).
    1  — one or more submissions had errors. Inbox files are left in
         place for the contributor to fix.

Usage:
    python3 community/scripts/intake_submissions.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from lib.lint import lint_body_for_secrets, lint_cover_bytes
from lib.unpack import unpack_nyxtemplate
from lib.utils import (
    REPO_ROOT,
    SUBMISSIONS_DIR,
    TEMPLATES_DIR,
    cover_extension,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Lint everything but don't write or delete files.")
    args = parser.parse_args()

    pending = sorted(SUBMISSIONS_DIR.glob("*.nyxtemplate"))
    if not pending:
        print(f"No pending submissions in {SUBMISSIONS_DIR.relative_to(REPO_ROOT)}/.")
        return 0

    print(f"Processing {len(pending)} pending submission(s)…\n")

    failures = 0
    for src in pending:
        rel = src.relative_to(REPO_ROOT)
        print(f"── {rel}")
        try:
            raw = src.read_bytes()
        except OSError as exc:
            print(f"   ✗ Could not read file: {exc}")
            failures += 1
            continue

        unpacked = unpack_nyxtemplate(raw, source_filename=str(rel))

        # Run the additional lints that go beyond schema validation.
        if unpacked.cover_bytes:
            lint_cover_bytes(
                unpacked.cover_bytes,
                expected_format=unpacked.cover_format,
                r=unpacked.result,
            )
        body = unpacked.template_json.get("body")
        if isinstance(body, str):
            lint_body_for_secrets(body, unpacked.result)

        for issue in unpacked.result.issues:
            mark = "✗" if issue.severity == "error" else "·"
            print(f"   {mark} {issue}")

        if unpacked.result.errors:
            print(f"   → REJECTED: fix the errors above and resubmit.")
            failures += 1
            continue

        target_dir = TEMPLATES_DIR / unpacked.slug
        if target_dir.exists():
            print(f"   ! Slug {unpacked.slug!r} already exists at "
                  f"{target_dir.relative_to(REPO_ROOT)}/. ")
            print( "     If this is an intentional update, delete the existing "
                  "directory first and resubmit.")
            failures += 1
            continue

        if args.dry_run:
            print(f"   ✓ Would unpack to {target_dir.relative_to(REPO_ROOT)}/  (dry run)")
            continue

        _write_template_dir(target_dir, unpacked)
        src.unlink()
        print(f"   ✓ Unpacked to {target_dir.relative_to(REPO_ROOT)}/")
        print(f"   ✓ Removed {rel}")

    print()
    print(f"Done. Failures: {failures}")
    return 0 if failures == 0 else 1


def _write_template_dir(target_dir: Path, unpacked) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    (target_dir / "template.json").write_text(
        json.dumps(unpacked.template_json, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (target_dir / "meta.yml").write_text(
        yaml.safe_dump(unpacked.meta, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    if unpacked.cover_bytes and unpacked.cover_format:
        ext = cover_extension(unpacked.cover_format)
        (target_dir / f"cover.{ext}").write_bytes(unpacked.cover_bytes)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    sys.exit(main())
