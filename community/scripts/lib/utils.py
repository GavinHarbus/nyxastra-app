"""Path constants and small string helpers shared across the pipeline.

Keeping these in one place means scripts never hardcode paths and the
slug rule used by the migrator, the intake script, and the build script
is guaranteed to be identical.
"""
from __future__ import annotations

import re
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────
# Repo-relative paths
# ──────────────────────────────────────────────────────────────────────

# This file lives at  community/scripts/lib/utils.py  →  parents[3] = repo root.
REPO_ROOT = Path(__file__).resolve().parents[3]

COMMUNITY_DIR    = REPO_ROOT / "community"
TEMPLATES_DIR    = COMMUNITY_DIR / "templates"
SUBMISSIONS_DIR  = COMMUNITY_DIR / "submissions"
DIST_DIR         = COMMUNITY_DIR / "dist"

DIST_INDEX        = DIST_DIR / "index.json"
DIST_TEMPLATES    = DIST_DIR / "templates"
DIST_COVERS       = DIST_DIR / "covers"
DIST_MANIFEST     = DIST_DIR / "manifest.json"

# Files that make up one unpacked template on disk.
TEMPLATE_JSON     = "template.json"
META_YAML         = "meta.yml"
COVER_BASENAME    = "cover"   # extension is one of: .png, .jpg, .jpeg, .webp


# ──────────────────────────────────────────────────────────────────────
# Slug generation
# ──────────────────────────────────────────────────────────────────────

# Characters we strip out of titles entirely when forming a slug.
# We keep CJK and other non-ASCII letters because they're meaningful to
# the audience; URL encoding handles them just fine.
_SLUG_STRIP = re.compile(r"[\\/:*?\"<>|\x00-\x1f]")

# Characters we collapse to a single dash. Spaces, mid-dot, slashes and
# repeated punctuation all become "-" so slugs are URL-safe and stable.
_SLUG_DASH  = re.compile(r"[\s·•/.,，。、:：;；!！?？\\\"'`’“”]+")
_DASH_RUN   = re.compile(r"-{2,}")


def slugify(title: str) -> str:
    """Return a URL-safe, filesystem-safe slug for a template title.

    Goals:
      - Stable: same title → same slug, every run.
      - Lossless for CJK: we don't romanize; "电影感人像" stays "电影感人像".
      - Safe for git, web URLs, macOS / Linux filesystems.
    """
    s = (title or "").strip()
    s = _SLUG_STRIP.sub("", s)
    s = _SLUG_DASH.sub("-", s)
    s = _DASH_RUN.sub("-", s).strip("-")
    return s or "untitled"


# ──────────────────────────────────────────────────────────────────────
# Image helpers
# ──────────────────────────────────────────────────────────────────────

# Maps the `format` string declared in a NyxAstra cover to the file
# extension we write out. We accept both "jpeg" and "jpg" on input.
COVER_EXTENSIONS = {
    "png":  "png",
    "jpg":  "jpg",
    "jpeg": "jpg",
    "webp": "webp",
}

# Maps Pillow's `Image.format` (uppercase) back to a stable lowercase
# string suitable for the .nyxtemplate `format` field.
PIL_FORMAT_TO_NYX = {
    "PNG":  "png",
    "JPEG": "jpeg",
    "WEBP": "webp",
}


def cover_extension(nyx_format: str) -> str:
    """File extension to use for a cover declared as `format=<nyx_format>`."""
    return COVER_EXTENSIONS.get((nyx_format or "").lower(), "bin")


def find_cover_file(template_dir: Path) -> Path | None:
    """Locate the cover file inside a template directory, regardless of extension."""
    for ext in ("webp", "png", "jpg", "jpeg"):
        candidate = template_dir / f"{COVER_BASENAME}.{ext}"
        if candidate.exists():
            return candidate
    return None
