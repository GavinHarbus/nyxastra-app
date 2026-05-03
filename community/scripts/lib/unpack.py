"""Convert a single-file `.nyxtemplate` (with inline base64 cover) into the
unpacked on-disk representation used inside the repo.

Unpacked representation per template:
    community/templates/<slug>/
      template.json   — TemplateExchangeDocument minus `cover` and minus
                        non-portable provenance (we move provenance into
                        meta.yml.source where reviewers can see it cleanly).
      cover.<ext>     — Decoded cover bytes; EXIF stripped on decode.
      meta.yml        — Author, license, category, tags, models, …

This module never touches the filesystem on its own — it returns
in-memory artifacts so the same code path works for the migrator (which
walks an existing folder) and the intake script (which processes
`community/submissions/`).
"""
from __future__ import annotations

import base64
import binascii
import io
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from .schema import (
    PLACEHOLDER_AUTHOR_NAME,
    TEMPLATE_SCHEMA,
    ValidationResult,
    validate_nyxtemplate,
)
from .utils import PIL_FORMAT_TO_NYX, slugify


# ──────────────────────────────────────────────────────────────────────
# Result type
# ──────────────────────────────────────────────────────────────────────

@dataclass
class UnpackedTemplate:
    """Everything needed to write one template directory to disk."""
    slug: str
    template_json: dict[str, Any]   # `cover` field removed
    cover_bytes: bytes | None
    cover_format: str | None        # "png" | "jpeg" | "webp" | None
    meta: dict[str, Any]            # Auto-stub for meta.yml
    result: ValidationResult        # Errors/warnings produced while unpacking


# ──────────────────────────────────────────────────────────────────────
# Public entry points
# ──────────────────────────────────────────────────────────────────────

def unpack_nyxtemplate(
    raw_bytes: bytes,
    *,
    source_filename: str = "",
    default_category: str = "other",
    default_locale: str = "universal",
    default_models: tuple[str, ...] = ("gpt-image-2", "gpt-image-1.5", "gpt-image-1"),
    featured: bool = False,
    author_name_override: str | None = None,
) -> UnpackedTemplate:
    """Parse `.nyxtemplate` bytes, validate them, and return an `UnpackedTemplate`.

    Defaults are tuned for the intake-from-submissions case where we
    don't know the contributor's intended category / locale and have to
    stub them with a sensible value the contributor will edit.

    The migrator passes more specific defaults derived from the legacy
    folder layout.
    """
    r = ValidationResult()

    # Parse JSON
    try:
        doc = json.loads(raw_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        r.error("not-utf8", f"File is not valid UTF-8: {exc}")
        return UnpackedTemplate("", {}, None, None, {}, r)
    except json.JSONDecodeError as exc:
        r.error("bad-json", f"File is not valid JSON: {exc}")
        return UnpackedTemplate("", {}, None, None, {}, r)

    # Schema validation (non-fatal here — caller decides)
    r.extend(validate_nyxtemplate(doc))

    # Even if validation found errors, try to extract what we can so
    # CI can show the contributor *all* the problems in one round-trip.
    name = doc.get("name") or Path(source_filename).stem or "Untitled"
    slug = slugify(str(name))

    # Decode and clean the cover (strips EXIF as a side effect of the
    # Pillow round-trip).
    cover_bytes: bytes | None = None
    cover_format: str | None = None
    cover_meta = doc.get("cover")
    if isinstance(cover_meta, dict):
        b64 = cover_meta.get("dataBase64") or ""
        try:
            raw_cover = base64.b64decode(b64, validate=False)
            cover_bytes, cover_format = _normalize_cover(raw_cover, r)
        except (binascii.Error, ValueError) as exc:
            r.error("cover-base64", f"Cover dataBase64 didn't decode: {exc}", "cover.dataBase64")

    # Strip cover and provenance fields from the on-disk template.json.
    # We keep schema/version/name/body/variables/tags/folderName/preset.
    cleaned = {k: v for k, v in doc.items() if k not in ("cover", "sourceApp", "sourceAppVersion")}

    # Build the meta.yml stub.
    tags = doc.get("tags") if isinstance(doc.get("tags"), list) else []
    meta: dict[str, Any] = {
        "slug": slug,
        "title": str(name),
        "license": "CC-BY-4.0",
        "category": default_category,
        "locale": default_locale,
        "tags": tags,
        "models": list(default_models),
        "nsfw": False,
        "featured": featured,
        "createdAt": date.today().isoformat(),
        "basedOn": None,
        "author": {
            "name": author_name_override or PLACEHOLDER_AUTHOR_NAME,
            "url": None,
        },
        "source": {
            "app": doc.get("sourceApp") or "NyxAstra",
            "appVersion": doc.get("sourceAppVersion"),
            "importedFrom": source_filename or None,
        },
    }

    return UnpackedTemplate(
        slug=slug,
        template_json=cleaned,
        cover_bytes=cover_bytes,
        cover_format=cover_format,
        meta=meta,
        result=r,
    )


# ──────────────────────────────────────────────────────────────────────
# Cover normalization
# ──────────────────────────────────────────────────────────────────────

def _normalize_cover(raw: bytes, r: ValidationResult) -> tuple[bytes | None, str | None]:
    """Re-encode a cover through Pillow to:
      • strip EXIF / XMP / ICC chunks (Pillow drops them by default on save);
      • detect the *actual* format rather than trusting the JSON `format` field;
      • normalize JPEG/PNG/WebP only — anything else is rejected.
    """
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        r.error("cover-bad-image", f"Cover bytes don't decode as a valid image: {exc}", "cover")
        return None, None

    fmt_upper = (img.format or "").upper()
    nyx_fmt = PIL_FORMAT_TO_NYX.get(fmt_upper)
    if nyx_fmt is None:
        r.error(
            "cover-bad-format",
            f"Cover format {fmt_upper!r} is not supported (must be PNG, JPEG, or WebP).",
            "cover",
        )
        return None, None

    # Re-save through Pillow with no metadata to strip EXIF/XMP/ICC.
    buf = io.BytesIO()
    save_kwargs: dict[str, Any] = {}
    if fmt_upper == "JPEG":
        save_kwargs.update(quality=92, optimize=True)
        # Convert RGBA → RGB for JPEG just in case.
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
    elif fmt_upper == "PNG":
        save_kwargs.update(optimize=True)
    elif fmt_upper == "WEBP":
        save_kwargs.update(quality=92, method=6)

    img.save(buf, format=fmt_upper, **save_kwargs)
    return buf.getvalue(), nyx_fmt
