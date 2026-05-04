"""Lint checks that go beyond raw schema validation.

These work on either:
  * raw bytes already decoded from `cover.dataBase64`, or
  * the prompt body string,
and append `ValidationIssue`s to a `ValidationResult`. They never
raise — bad input shows up as an error issue.
"""
from __future__ import annotations

import io
import re

from PIL import Image, UnidentifiedImageError

from .schema import ValidationResult


# ──────────────────────────────────────────────────────────────────────
# Cover image validation
# ──────────────────────────────────────────────────────────────────────

# Soft cap on cover dimensions. Anything larger is downscaled at build
# time anyway; we only warn so authors know their input is being shrunk.
MAX_COVER_LONG_EDGE_PX  = 2048
MAX_COVER_SHORT_EDGE_PX = 2048

# Hard cap on raw bytes. Above this we reject the submission rather than
# silently storing a multi-MB blob.
MAX_COVER_BYTES = 4 * 1024 * 1024  # 4 MiB

# Minimum dimensions — anything smaller is too tiny to make a useful
# gallery thumbnail.
MIN_COVER_LONG_EDGE_PX = 256


def lint_cover_bytes(cover_bytes: bytes, *, expected_format: str | None, r: ValidationResult) -> None:
    """Decode `cover_bytes`, sanity-check size and format."""
    if not cover_bytes:
        r.error("cover-empty", "Cover image is empty (0 bytes).", "cover")
        return

    if len(cover_bytes) > MAX_COVER_BYTES:
        r.error(
            "cover-too-large",
            f"Cover is {len(cover_bytes) // 1024} KB, exceeding the {MAX_COVER_BYTES // 1024} KB limit. "
            "Re-export at lower quality or downscale before resubmitting.",
            "cover",
        )
        return

    try:
        img = Image.open(io.BytesIO(cover_bytes))
        img.verify()                              # cheap structural check
        img = Image.open(io.BytesIO(cover_bytes)) # reopen — verify() consumed it
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        r.error("cover-bad-image", f"Cover bytes don't decode as a valid image: {exc}", "cover")
        return

    fmt = (img.format or "").upper()
    if fmt not in {"PNG", "JPEG", "WEBP"}:
        r.error(
            "cover-bad-format",
            f"Cover format {fmt!r} is not allowed (must be PNG, JPEG, or WebP).",
            "cover",
        )
    elif expected_format and fmt.lower() != expected_format.lower().replace("jpg", "jpeg"):
        r.warn(
            "cover-format-mismatch",
            f"Declared cover format is {expected_format!r} but bytes look like {fmt}. "
            "Build will trust the actual bytes.",
            "cover",
        )

    w, h = img.size
    long_edge, short_edge = max(w, h), min(w, h)
    if long_edge < MIN_COVER_LONG_EDGE_PX:
        r.error(
            "cover-too-small",
            f"Cover is {w}x{h}; long edge must be at least {MIN_COVER_LONG_EDGE_PX}px.",
            "cover",
        )
    if long_edge > MAX_COVER_LONG_EDGE_PX or short_edge > MAX_COVER_SHORT_EDGE_PX:
        r.warn(
            "cover-oversize",
            f"Cover is {w}x{h}; build will downscale to fit {MAX_COVER_LONG_EDGE_PX}px long edge.",
            "cover",
        )


# ──────────────────────────────────────────────────────────────────────
# Secret scanning in the prompt body
# ──────────────────────────────────────────────────────────────────────

# Patterns chosen to be fast, false-positive-tolerant, and to catch the
# common shapes of leaked credentials. Better to be a little noisy than
# to ship a key in the public gallery. Each entry is (regex, label).
_SECRET_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bsk-[A-Za-z0-9\-_]{20,}\b"),
     "OpenAI API key (sk-...)"),
    (re.compile(r"\bsk-proj-[A-Za-z0-9\-_]{20,}\b"),
     "OpenAI project API key (sk-proj-...)"),
    (re.compile(r"\bsk-svcacct-[A-Za-z0-9\-_]{20,}\b"),
     "OpenAI service-account key (sk-svcacct-...)"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
     "AWS access key id (AKIA...)"),
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"),
     "Google API key (AIza...)"),
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
     "GitHub personal access token (ghp_...)"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),
     "Slack token (xox..)"),
    # Bearer tokens with non-trivial payloads
    (re.compile(r"\bBearer\s+[A-Za-z0-9\-_\.]{32,}\b"),
     "Bearer token in body"),
    # Generic 32+ hex / base64-looking string after key-like words
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*[A-Za-z0-9\-_/+]{20,}"),
     "credential-shaped assignment"),
]

# Personal-info patterns — these stay warnings, not errors, because
# legitimate templates can mention emails/phones in a generic way.
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
     "looks like an email address"),
    (re.compile(r"\b(?:\+?\d{1,3}[-\s]?)?(?:\(\d{2,4}\)[-\s]?)?\d{3,4}[-\s]?\d{4}\b"),
     "looks like a phone number"),
]


def lint_body_for_secrets(body: str, r: ValidationResult) -> None:
    """Scan the prompt body for embedded credentials and PII."""
    if not body:
        return
    for pattern, label in _SECRET_PATTERNS:
        match = pattern.search(body)
        if match:
            r.error(
                "secret-in-body",
                f"Prompt body contains what looks like a {label}: '{_redact(match.group(0))}'. "
                "Remove it before resubmitting.",
                "body",
            )
    for pattern, label in _PII_PATTERNS:
        match = pattern.search(body)
        if match:
            r.warn(
                "pii-in-body",
                f"Prompt body {label}: '{_redact(match.group(0))}'. "
                "Confirm this is intentional before merging.",
                "body",
            )


def _redact(s: str) -> str:
    """Truncate a matched secret for display, preserving the prefix so
    the author can locate it without us echoing the full value."""
    return (s[:6] + "…") if len(s) > 8 else s
