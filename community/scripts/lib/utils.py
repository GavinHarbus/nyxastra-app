"""Path constants and small string helpers shared across the pipeline.

The community pipeline's source of truth is now a flat directory of
`.nyxtemplate` files at `community/templates/`. Each filename (without
extension) doubles as the template's slug — we no longer derive it
from the template name, so contributors get full control over the URL
their template ends up at.
"""
from __future__ import annotations

import re
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# Repo-relative paths
# ──────────────────────────────────────────────────────────────────────

# This file lives at  community/scripts/lib/utils.py  →  parents[3] = repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]

COMMUNITY_DIR  = REPO_ROOT / "community"
TEMPLATES_DIR  = COMMUNITY_DIR / "templates"      # flat *.nyxtemplate files
DIST_DIR       = COMMUNITY_DIR / "dist"

DIST_INDEX     = DIST_DIR / "index.json"
DIST_TEMPLATES = DIST_DIR / "templates"
DIST_COVERS    = DIST_DIR / "covers"
DIST_MANIFEST  = DIST_DIR / "manifest.json"

NYXTEMPLATE_EXT = ".nyxtemplate"

# Maps Pillow's `Image.format` (uppercase) back to a stable lowercase
# string suitable for the .nyxtemplate `format` field.
PIL_FORMAT_TO_NYX = {
    "PNG":  "png",
    "JPEG": "jpeg",
    "WEBP": "webp",
}


# ──────────────────────────────────────────────────────────────────────
# Slug helpers (used to validate the filename → name relationship)
# ──────────────────────────────────────────────────────────────────────

# Characters we strip out of titles entirely when forming a reference
# slug for filename validation. Identical to the rule the macOS app
# uses internally — see `TemplatesView.safeFilename`.
_SLUG_STRIP = re.compile(r"[\\/:*?\"<>|\x00-\x1f]")
_SLUG_DASH  = re.compile(r"[\s·•/.,，。、:：;；!！?？\\\"'`’“”]+")
_DASH_RUN   = re.compile(r"-{2,}")


def slugify(title: str) -> str:
    """Return a URL-safe, filesystem-safe slug for a template title.

    Used only to *suggest* a filename, not to *enforce* one — the
    contributor picks the filename and CI just checks it has the
    `.nyxtemplate` extension and is unique within the directory.
    """
    s = (title or "").strip()
    s = _SLUG_STRIP.sub("", s)
    s = _SLUG_DASH.sub("-", s)
    s = _DASH_RUN.sub("-", s).strip("-")
    return s or "untitled"
