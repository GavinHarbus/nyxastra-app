"""Pack an unpacked template directory back into a single-file `.nyxtemplate`.

This is the inverse of `unpack.py` and is called by the build step to
produce `community/dist/templates/<slug>.nyxtemplate` — the file end
users actually download from the gallery.

We always emit the current schema version (TEMPLATE_SCHEMA_MAX_VERSION),
not whatever version the source happened to be, so old contributions
are auto-upgraded on every build.
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

from .schema import TEMPLATE_SCHEMA, TEMPLATE_SCHEMA_MAX_VERSION
from .utils import PIL_FORMAT_TO_NYX


def pack_template_dir(template_dir: Path) -> bytes:
    """Read `template.json + cover.* + meta.yml` from a directory and
    return the bytes of an equivalent single-file `.nyxtemplate`."""
    tpl_path = template_dir / "template.json"
    meta_path = template_dir / "meta.yml"

    with tpl_path.open("r", encoding="utf-8") as f:
        tpl = json.load(f)
    with meta_path.open("r", encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}

    # Always re-stamp schema/version on the way out.
    tpl["schema"] = TEMPLATE_SCHEMA
    tpl["version"] = TEMPLATE_SCHEMA_MAX_VERSION

    # Provenance: stamp the build's identity, not the contributor's
    # original app version. The contributor's app version is preserved
    # in meta.yml.source for archaeological purposes.
    tpl["sourceApp"] = "NyxAstra Community"
    tpl["sourceAppVersion"] = None

    # Re-attach the cover, encoding the on-disk bytes as base64 inline
    # so the downloaded file is self-contained.
    cover = _load_cover(template_dir)
    if cover is not None:
        cover_bytes, cover_fmt = cover
        tpl["cover"] = {
            "format": cover_fmt,
            "dataBase64": base64.b64encode(cover_bytes).decode("ascii"),
        }
    else:
        # Don't include a half-formed `cover` key if we have no image —
        # the schema makes it optional.
        tpl.pop("cover", None)

    # `folderName` ends up driving the in-app folder placement when a
    # user imports the template. Default to the gallery category if the
    # template doesn't already have one.
    if "folderName" not in tpl or not tpl.get("folderName"):
        cat = meta.get("category")
        if isinstance(cat, str) and cat:
            tpl["folderName"] = cat.capitalize()

    # Stable, pretty JSON so binary diffs across builds are minimal.
    return _dump_json(tpl).encode("utf-8")


def _load_cover(template_dir: Path) -> tuple[bytes, str] | None:
    """Load the cover image from `template_dir`. Re-encodes through
    Pillow to ensure the bytes we ship match the format we declare."""
    for ext in ("webp", "png", "jpg", "jpeg"):
        candidate = template_dir / f"cover.{ext}"
        if candidate.exists():
            with Image.open(candidate) as img:
                img.load()
                fmt_upper = (img.format or "").upper()
                nyx_fmt = PIL_FORMAT_TO_NYX.get(fmt_upper)
                if nyx_fmt is None:
                    return None
                buf = io.BytesIO()
                save_kwargs: dict[str, Any] = {}
                if fmt_upper == "JPEG":
                    if img.mode in ("RGBA", "LA", "P"):
                        img = img.convert("RGB")
                    save_kwargs.update(quality=92, optimize=True)
                elif fmt_upper == "PNG":
                    save_kwargs.update(optimize=True)
                elif fmt_upper == "WEBP":
                    save_kwargs.update(quality=92, method=6)
                img.save(buf, format=fmt_upper, **save_kwargs)
                return buf.getvalue(), nyx_fmt
    return None


def _dump_json(obj: dict[str, Any]) -> str:
    """Match NyxAstra's encoder formatting: pretty-printed, sorted keys,
    no escaped slashes. Keeps round-trips byte-identical."""
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)
