"""Schema definitions and validation for community templates.

We deliberately hand-roll validation rather than pulling in `jsonschema`
because:
  * the rules are few and the error messages we want are tailored to
    template authors, not jsonschema's generic prose;
  * the repo dependency surface stays Pillow + PyYAML only.

Two things are validated here:
  1. The `.nyxtemplate` JSON shape (`TemplateExchangeDocument`,
     schema="nyxtemplate", version<=1) — what the user uploads.
  2. The `meta.yml` companion file we generate on unpack and ask
     contributors to complete.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

# ──────────────────────────────────────────────────────────────────────
# Constants — must stay in sync with NyxAstra's TemplateExchange.swift.
# When NyxAstra bumps the schema, bump TEMPLATE_SCHEMA_MAX_VERSION here
# in the same PR and update the unpack/pack code paths.
# ──────────────────────────────────────────────────────────────────────

TEMPLATE_SCHEMA           = "nyxtemplate"
TEMPLATE_SCHEMA_MAX_VERSION = 1

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

# Models the gallery filter exposes today. New entries are added when
# NyxAstra ships support; older deprecated families stay listed for
# back-compat with templates exported by older app versions.
VALID_MODELS = {
    "gpt-image-2",
    "gpt-image-1.5",
    "gpt-image-1",
    "gpt-image-1-mini",
}

# License identifiers we accept in meta.yml. Anything outside this set
# triggers a lint warning rather than an error — there are real fringe
# cases (e.g. company-specific terms) that maintainers may approve.
KNOWN_LICENSES = {
    "CC0-1.0",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "All Rights Reserved",
}


# ──────────────────────────────────────────────────────────────────────
# In-memory representation
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    """A single problem found while validating a template or its meta."""
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

def validate_nyxtemplate(doc: Any) -> ValidationResult:
    """Validate a parsed `.nyxtemplate` JSON document (single-template form).

    Returns a `ValidationResult`. The caller decides whether warnings are
    fatal in their context.
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
    elif version > TEMPLATE_SCHEMA_MAX_VERSION:
        r.error(
            "future-version",
            f"Template uses schema version {version}, but this pipeline only "
            f"understands up to version {TEMPLATE_SCHEMA_MAX_VERSION}. "
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
# meta.yml validation
# ──────────────────────────────────────────────────────────────────────

# Required and optional fields in meta.yml. Auto-generated meta files
# may have placeholder values for the required fields — that's fine
# during the unpack step but errors during build.

META_REQUIRED = {"slug", "title", "license", "category", "author"}
META_OPTIONAL = {"locale", "models", "tags", "nsfw", "featured", "createdAt", "basedOn", "source"}
META_ALL      = META_REQUIRED | META_OPTIONAL

PLACEHOLDER_AUTHOR_NAME = "FIXME-please-fill-in"


def validate_meta(meta: Any, *, allow_placeholders: bool = False) -> ValidationResult:
    """Validate a parsed `meta.yml` document.

    `allow_placeholders=True` lets the unpack step accept its own
    auto-generated stubs (where author.name is the FIXME sentinel) without
    raising. The build step always passes False.
    """
    r = ValidationResult()
    if not isinstance(meta, dict):
        r.error("meta-not-object", "meta.yml must be a YAML mapping at the top level.")
        return r

    for key in META_REQUIRED:
        if key not in meta:
            r.error("meta-missing", f"Required field `{key}` is missing.", key)

    extra = set(meta.keys()) - META_ALL
    for key in extra:
        r.warn("meta-unknown", f"Unknown field `{key}` will be ignored by the build.", key)

    slug = meta.get("slug")
    if slug is not None and (not isinstance(slug, str) or not slug.strip()):
        r.error("meta-bad-slug", "`slug` must be a non-empty string.", "slug")

    title = meta.get("title")
    if title is not None and (not isinstance(title, str) or not title.strip()):
        r.error("meta-bad-title", "`title` must be a non-empty string.", "title")

    license_id = meta.get("license")
    if license_id is not None and license_id not in KNOWN_LICENSES:
        r.warn(
            "meta-unknown-license",
            f"License {license_id!r} is not in the standard set "
            f"{sorted(KNOWN_LICENSES)}. Maintainer approval required.",
            "license",
        )

    category = meta.get("category")
    if category is not None and category not in VALID_CATEGORIES:
        r.error(
            "meta-bad-category",
            f"`category` must be one of {sorted(VALID_CATEGORIES)}; got {category!r}.",
            "category",
        )

    author = meta.get("author")
    if author is not None:
        if not isinstance(author, dict):
            r.error("meta-bad-author", "`author` must be a mapping with at least `name`.", "author")
        else:
            name = author.get("name")
            if not isinstance(name, str) or not name.strip():
                r.error("meta-author-no-name", "`author.name` is required.", "author.name")
            elif name == PLACEHOLDER_AUTHOR_NAME and not allow_placeholders:
                r.error(
                    "meta-author-placeholder",
                    "`author.name` still contains the auto-generated placeholder. "
                    "Edit meta.yml to credit yourself (or set it to `Anonymous`).",
                    "author.name",
                )

    models = meta.get("models")
    if models is not None:
        if not isinstance(models, list) or not models:
            r.error("meta-bad-models", "`models` must be a non-empty list.", "models")
        else:
            for i, m in enumerate(models):
                if m not in VALID_MODELS:
                    r.warn(
                        "meta-unknown-model",
                        f"Model {m!r} is not in the known set {sorted(VALID_MODELS)}.",
                        f"models[{i}]",
                    )

    locale = meta.get("locale")
    if locale is not None and (not isinstance(locale, str) or not locale.strip()):
        r.error("meta-bad-locale", "`locale` must be a string like 'en', 'zh-CN', or 'universal'.", "locale")

    nsfw = meta.get("nsfw", False)
    if not isinstance(nsfw, bool):
        r.error("meta-bad-nsfw", "`nsfw` must be a boolean.", "nsfw")

    featured = meta.get("featured", False)
    if not isinstance(featured, bool):
        r.error("meta-bad-featured", "`featured` must be a boolean.", "featured")

    created = meta.get("createdAt")
    if created is not None and not isinstance(created, (str, date)):
        r.error("meta-bad-createdAt", "`createdAt` must be an ISO date string (YYYY-MM-DD).", "createdAt")

    return r
