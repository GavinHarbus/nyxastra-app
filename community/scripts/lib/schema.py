"""Schema validation for community `.nyxtemplate` files (v2).

The community pipeline consumes a flat directory of single-file
`.nyxtemplate` documents at `community/templates/*.nyxtemplate`.
Every file is the same JSON shape NyxAstra writes when the user picks
"Export…" — schema=`nyxtemplate`, version=2, with an embedded
`community` block carrying author / license / category / locale /
models / nsfw.

We deliberately hand-roll validation rather than pulling in
`jsonschema` because:
  * the rules are few and the error messages we want are tailored to
    template authors, not jsonschema's generic prose;
  * the repo dependency surface stays Pillow + PyYAML only.

This module never touches the filesystem on its own — pass it a
parsed document and it appends issues to a `ValidationResult`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlsplit

# ──────────────────────────────────────────────────────────────────────
# Constants — must stay in sync with NyxAstra's TemplateExchange.swift.
# When NyxAstra bumps the schema, bump TEMPLATE_SCHEMA_MAX_VERSION here
# in the same PR and update the validators below.
# ──────────────────────────────────────────────────────────────────────

TEMPLATE_SCHEMA              = "nyxtemplate"
TEMPLATE_SCHEMA_MIN_VERSION  = 2
TEMPLATE_SCHEMA_MAX_VERSION  = 2

VALID_VARIABLE_KINDS = {"text", "multiline", "enumeration", "number"}
VALID_IMAGE_FORMATS  = {"png", "jpeg", "webp"}
VALID_QUALITIES      = {"auto", "low", "medium", "high"}
VALID_BACKGROUNDS    = {"auto", "opaque", "transparent"}

# Canonical category list. Expanded only via PR + maintainer review so
# the gallery filters stay meaningful instead of becoming a tag soup.
VALID_CATEGORIES = {
    "photo", "illustration", "branding", "ui", "infographic",
    "poster", "social", "universal", "other",
}

# License identifiers we accept in the community block. Anything outside
# this set triggers a lint warning rather than an error — there are real
# fringe cases (e.g. company-specific terms) that maintainers may approve.
KNOWN_LICENSES = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "All Rights Reserved",
}

# `author.url` security/quality gate.
#
# The gallery renders this URL as a clickable link on the public site,
# so it must come from a known, trustworthy host. Without this gate a
# malicious PR could attach a phishing site, an SEO/affiliate spam URL,
# or a `javascript:` payload to a community template.
#
# Allowed schemes: https only (no http, no javascript:, no data:, etc.).
# Allowed hosts: contributor profile pages on platforms where identity
# is meaningfully verifiable (GitHub) or socially attributable (X/BSky/
# Mastodon flagship/Xiaohongshu/Bilibili) plus the studio's own site.
# To add a host, edit this set and bump it in the same PR — that way
# new attribution sources go through human review.
ALLOWED_AUTHOR_URL_HOSTS = frozenset({
    "github.com",
    "x.com",
    "twitter.com",
    "bsky.app",
    "mastodon.social",
    "xiaohongshu.com",
    "www.xiaohongshu.com",
    "bilibili.com",
    "space.bilibili.com",
    "gavinschneestudio.org",
})

# Hard cap to keep the link cell tidy and avoid people stuffing tracking
# parameters / referral chains into it.
MAX_AUTHOR_URL_LENGTH = 200


# ──────────────────────────────────────────────────────────────────────
# In-memory representation
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    """A single problem found while validating a template document."""
    severity: str          # "error" | "warning"
    code: str              # short stable identifier, e.g. "missing-field"
    message: str           # human-friendly explanation
    location: str = ""     # optional dot-path into the document

    def __str__(self) -> str:
        loc = f" [{self.location}]" if self.location else ""
        return f"{self.severity.upper():7} {self.code}{loc}: {self.message}"


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, code: str, message: str, location: str = "") -> None:
        self.issues.append(ValidationIssue("error", code, message, location))

    def warn(self, code: str, message: str, location: str = "") -> None:
        self.issues.append(ValidationIssue("warning", code, message, location))

    def extend(self, other: "ValidationResult") -> None:
        self.issues.extend(other.issues)


# ──────────────────────────────────────────────────────────────────────
# .nyxtemplate JSON validation (single-document shape only — bundles
# are not accepted as community submissions; one PR = one template).
# ──────────────────────────────────────────────────────────────────────

def validate_nyxtemplate(doc: Any, *, require_community: bool = True) -> ValidationResult:
    """Validate a parsed `.nyxtemplate` JSON document (v2, single template).

    Files placed into `community/templates/` are the public-gallery
    source of truth, so by default the embedded `community` block is
    required and validated. Pass `require_community=False` only if you
    want to lint a private template that doesn't carry attribution.
    """
    r = ValidationResult()

    if not isinstance(doc, dict):
        r.error("not-object", "Template file must be a JSON object at the top level.")
        return r

    schema = doc.get("schema")
    if schema != TEMPLATE_SCHEMA:
        r.error(
            "wrong-schema",
            f"Expected schema={TEMPLATE_SCHEMA!r}, got {schema!r}. "
            "Bundle files (.nyxtemplates) cannot be submitted to the community — "
            "split them into individual templates first.",
            "schema",
        )
        return r

    version = doc.get("version")
    if not isinstance(version, int):
        r.error("missing-version", "Top-level `version` must be an integer.", "version")
    elif version < TEMPLATE_SCHEMA_MIN_VERSION:
        r.error(
            "stale-version",
            f"Template uses schema v{version}, but the community pipeline now "
            f"requires v{TEMPLATE_SCHEMA_MIN_VERSION}+. Re-export the template from "
            "a recent NyxAstra build.",
            "version",
        )
    elif version > TEMPLATE_SCHEMA_MAX_VERSION:
        r.error(
            "future-version",
            f"Template uses schema v{version}, but this pipeline only "
            f"understands up to v{TEMPLATE_SCHEMA_MAX_VERSION}. "
            "Update the build scripts before merging.",
            "version",
        )

    name = doc.get("name")
    if not isinstance(name, str) or not name.strip():
        r.error("missing-name", "Top-level `name` is required and must be a non-empty string.", "name")

    body = doc.get("body")
    if not isinstance(body, str) or not body.strip():
        r.error("missing-body", "Top-level `body` is required and must be a non-empty string.", "body")

    # Variables
    variables = doc.get("variables", [])
    if not isinstance(variables, list):
        r.error("variables-not-list", "`variables` must be a list.", "variables")
        variables = []
    declared_var_names: set[str] = set()
    for i, v in enumerate(variables):
        loc = f"variables[{i}]"
        if not isinstance(v, dict):
            r.error("variable-not-object", "Each variable must be an object.", loc)
            continue
        vname = v.get("name")
        if not isinstance(vname, str) or not vname.strip():
            r.error("variable-no-name", "Variable is missing a `name`.", loc)
        else:
            if vname in declared_var_names:
                r.error("variable-duplicate", f"Variable {vname!r} is declared more than once.", loc)
            declared_var_names.add(vname)
        kind = v.get("kind")
        if kind not in VALID_VARIABLE_KINDS:
            r.error(
                "variable-bad-kind",
                f"Variable kind must be one of {sorted(VALID_VARIABLE_KINDS)}; got {kind!r}.",
                f"{loc}.kind",
            )
        if kind == "enumeration":
            allowed = v.get("allowedValues") or []
            if not isinstance(allowed, list) or not allowed:
                r.error(
                    "enum-no-values",
                    "Enumeration variables must declare a non-empty `allowedValues` list.",
                    f"{loc}.allowedValues",
                )

    # Body / variable consistency
    if isinstance(body, str):
        used = _placeholders_in(body)
        for u in used:
            if u not in declared_var_names:
                r.error(
                    "undeclared-variable",
                    f"Body uses {{{{{u}}}}} but no matching entry exists in `variables`.",
                    "body",
                )
        for d in declared_var_names:
            if d not in used:
                r.warn(
                    "unused-variable",
                    f"Variable {d!r} is declared but never used in the body.",
                    "variables",
                )

    # Tags
    tags = doc.get("tags", [])
    if not isinstance(tags, list):
        r.error("tags-not-list", "`tags` must be a list of strings.", "tags")
    elif any(not isinstance(t, str) or not t.strip() for t in tags):
        r.error("tag-not-string", "Every entry in `tags` must be a non-empty string.", "tags")

    # Parameter preset
    preset = doc.get("parameterPreset")
    if preset is not None:
        _validate_parameter_preset(preset, r)

    # Cover
    cover = doc.get("cover")
    if cover is not None:
        if not isinstance(cover, dict):
            r.error("cover-not-object", "`cover` must be an object.", "cover")
        else:
            fmt = (cover.get("format") or "").lower()
            if fmt not in VALID_IMAGE_FORMATS:
                r.error(
                    "cover-bad-format",
                    f"Cover `format` must be one of {sorted(VALID_IMAGE_FORMATS)}; got {fmt!r}.",
                    "cover.format",
                )
            data_b64 = cover.get("dataBase64")
            if not isinstance(data_b64, str) or not data_b64:
                r.error("cover-no-data", "Cover `dataBase64` must be a non-empty string.", "cover.dataBase64")

    # Community block
    community = doc.get("community")
    if community is None:
        if require_community:
            r.error(
                "community-missing",
                "Files in `community/templates/` must carry a `community` block "
                "(author, license, category, …). Open the template in NyxAstra, "
                "fill in the Community Sharing section in the editor, and re-export.",
                "community",
            )
    else:
        _validate_community(community, r)

    return r


def _validate_parameter_preset(preset: Any, r: ValidationResult) -> None:
    if not isinstance(preset, dict):
        r.error("preset-not-object", "`parameterPreset` must be an object.", "parameterPreset")
        return
    if "quality" in preset and preset["quality"] not in VALID_QUALITIES:
        r.error(
            "preset-bad-quality",
            f"`quality` must be one of {sorted(VALID_QUALITIES)}; got {preset['quality']!r}.",
            "parameterPreset.quality",
        )
    if "format" in preset and preset["format"] not in VALID_IMAGE_FORMATS:
        r.error(
            "preset-bad-format",
            f"`format` must be one of {sorted(VALID_IMAGE_FORMATS)}; got {preset['format']!r}.",
            "parameterPreset.format",
        )
    if "background" in preset and preset["background"] not in VALID_BACKGROUNDS:
        r.error(
            "preset-bad-background",
            f"`background` must be one of {sorted(VALID_BACKGROUNDS)}; got {preset['background']!r}.",
            "parameterPreset.background",
        )
    if "n" in preset:
        n = preset["n"]
        if not isinstance(n, int) or n < 1 or n > 10:
            r.error("preset-bad-n", f"`n` must be an integer between 1 and 10; got {n!r}.", "parameterPreset.n")
    if "size" in preset:
        size = preset["size"]
        if isinstance(size, dict):
            w, h = size.get("width"), size.get("height")
            if not (isinstance(w, int) and isinstance(h, int)):
                r.error("preset-bad-size", "`size` must have integer `width` and `height`.", "parameterPreset.size")
            elif (w, h) != (0, 0):  # (0,0) is the documented "auto" sentinel
                if w <= 0 or h <= 0:
                    r.error("preset-bad-size", "`size.width` and `size.height` must be > 0 (or both 0 for auto).", "parameterPreset.size")
                if w % 16 or h % 16:
                    # gpt-image-2 requires 16-aligned dimensions; gpt-image-1
                    # accepts only fixed presets. Flag as warning rather than
                    # error since templates are model-aware.
                    r.warn(
                        "preset-size-not-aligned",
                        f"`size` {w}x{h} is not 16-aligned; this is required for gpt-image-2 arbitrary sizes.",
                        "parameterPreset.size",
                    )


def _placeholders_in(body: str) -> set[str]:
    """Mirror of NyxPromptKit.PromptResolver.placeholders. Order doesn't matter
    for validation, only the set of names."""
    out: set[str] = set()
    i = 0
    while i < len(body):
        if body[i:i + 2] == "{{":
            end = body.find("}}", i + 2)
            if end < 0:
                break
            name = body[i + 2:end].strip()
            if name:
                out.add(name)
            i = end + 2
        else:
            i += 1
    return out


# ──────────────────────────────────────────────────────────────────────
# `community` block validation
# ──────────────────────────────────────────────────────────────────────

# Required fields when a community block is present and we're treating
# the file as a public-gallery submission. `models`, `locale`, `nsfw`,
# `featured`, `basedOn` stay optional.
COMMUNITY_REQUIRED = {"author", "license", "category"}


def _validate_community(community: Any, r: ValidationResult) -> None:
    if not isinstance(community, dict):
        r.error("community-not-object", "`community` must be a JSON object.", "community")
        return

    for field in COMMUNITY_REQUIRED:
        if field not in community or community[field] in (None, "", [], {}):
            r.error(
                "community-missing-field",
                f"`community.{field}` is required for templates in the public gallery.",
                f"community.{field}",
            )

    license_id = community.get("license")
    if license_id is not None:
        if not isinstance(license_id, str):
            r.error("community-bad-license", "`community.license` must be a string.", "community.license")
        elif license_id not in KNOWN_LICENSES:
            r.warn(
                "community-unknown-license",
                f"License {license_id!r} is not in the standard set "
                f"{sorted(KNOWN_LICENSES)}. Maintainer approval required.",
                "community.license",
            )

    category = community.get("category")
    if category is not None:
        if not isinstance(category, str):
            r.error("community-bad-category", "`community.category` must be a string.", "community.category")
        elif category not in VALID_CATEGORIES:
            r.error(
                "community-bad-category",
                f"`community.category` must be one of {sorted(VALID_CATEGORIES)}; got {category!r}.",
                "community.category",
            )

    author = community.get("author")
    if author is not None:
        if not isinstance(author, dict):
            r.error("community-bad-author", "`community.author` must be a mapping with at least `name`.", "community.author")
        else:
            name = author.get("name")
            if not isinstance(name, str) or not name.strip():
                r.error(
                    "community-author-no-name",
                    "`community.author.name` is required (use 'Anonymous' if you'd rather not be credited).",
                    "community.author.name",
                )
            url = author.get("url")
            if url not in (None, ""):
                _validate_author_url(url, r)

    # Gently warn (not error) if the contributor still has fields from
    # the old schema lying around. Older NyxAstra builds wrote these
    # straight into the file; newer builds drop them on export.
    legacy_fields = {"locale", "models", "basedOn", "nsfw", "featured"}
    for legacy in sorted(legacy_fields & set(community)):
        r.warn(
            "community-legacy-field",
            f"`community.{legacy}` is no longer recognized and will be ignored. "
            "Re-export the template from a current NyxAstra build to drop it.",
            f"community.{legacy}",
        )


def _validate_author_url(url: Any, r: ValidationResult) -> None:
    """Enforce the author.url security/quality gate.

    See `ALLOWED_AUTHOR_URL_HOSTS` for context. We split the rules into
    distinct error codes so a contributor sees the exact thing to fix.
    """
    if not isinstance(url, str):
        r.error("community-author-url-type", "`community.author.url` must be a string (or omitted).", "community.author.url")
        return

    if len(url) > MAX_AUTHOR_URL_LENGTH:
        r.error(
            "community-author-url-too-long",
            f"`community.author.url` is {len(url)} chars; max is {MAX_AUTHOR_URL_LENGTH}. "
            "Strip tracking parameters and use the canonical profile URL.",
            "community.author.url",
        )
        return

    try:
        parts = urlsplit(url)
    except ValueError:
        r.error("community-author-url-malformed", "`community.author.url` is not a parseable URL.", "community.author.url")
        return

    if parts.scheme != "https":
        r.error(
            "community-author-url-scheme",
            f"`community.author.url` must use https:// (got scheme {parts.scheme!r}). "
            "http://, javascript:, data:, and other schemes are rejected.",
            "community.author.url",
        )
        return

    host = (parts.hostname or "").lower()
    if not host:
        r.error("community-author-url-no-host", "`community.author.url` has no host component.", "community.author.url")
        return

    if host not in ALLOWED_AUTHOR_URL_HOSTS:
        r.error(
            "community-author-url-host",
            f"`community.author.url` host {host!r} is not in the allow-list. "
            f"Allowed: {sorted(ALLOWED_AUTHOR_URL_HOSTS)}. "
            "If you need a new platform added, open an issue or include the rationale in your PR.",
            "community.author.url",
        )
