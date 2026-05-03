# NyxAstra Template Gallery — moved

> **The template gallery has moved.**
> Browse all templates at **<https://gavinschneestudio.com/nyxastra/templates/>**.

This directory still holds the original `.nyxtemplate` files for legacy
download links. **The canonical source is now [`community/templates/`](../community/templates/)**,
where each template lives in its own folder as `template.json + cover + meta.yml`
for clean PR review and independent cover optimization.

## What changed?

| Before | After |
|---|---|
| `templates/<category>/<name>.nyxtemplate` (single file with inline base64 cover, ~1.5 MB each) | `community/templates/<slug>/{template.json, cover.png, meta.yml}` (cover stored as a separate binary) |
| Add a template by editing this folder | Drop a `.nyxtemplate` into [`community/submissions/`](../community/submissions/) — CI unpacks it for you |
| Direct download from this folder | CI re-packs every template on every build into `community/dist/templates/<slug>.nyxtemplate`, served from the website |

See [`community/README.md`](../community/README.md) for the full pipeline,
and [`community/CONTRIBUTING.md`](../community/CONTRIBUTING.md) to submit
a new template.

---

## For the curious

The previews under [`previews/`](previews/) are still used by the root
README's gallery grid. Once the website is live, those will be replaced
by `<img>` tags pointing at the website's CDN, and this directory can
be removed entirely.
