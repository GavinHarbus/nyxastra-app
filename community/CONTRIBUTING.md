# Contributing a Template

Thanks for sharing! Submitting a community template takes a few minutes.

---

## Path A — submit via Pull Request (recommended)

### 1. Design your template in NyxAstra

Open NyxAstra, create a new template, and design the prompt with
`{{variable}}` placeholders. Give it a name, pick a folder, add a few
tags, and (optionally) set a parameter preset (size / quality / format)
that matches the style.

<p align="center">
  <img src="../assets/screenshots/edittemplate.png" width="720" alt="Editing a template in NyxAstra">
</p>

Test it — generate at least one image to confirm the variables and
parameter preset work end to end. Use the result you like best as the
**cover image** (right-click an image in the Library and choose
*Set as template cover*).

### 2. Fill in the **Community Sharing** section in the editor

Open the template editor and expand the **Community Sharing** section.
There are only three things to fill in:

- **Author name** — how you'd like to be credited (handle, real name,
  or `Anonymous`).
- **Author URL** — *optional* link to your profile. Must be `https://`
  on one of these hosts: `github.com`, `x.com` / `twitter.com`,
  `bsky.app`, `mastodon.social`, `xiaohongshu.com`, `bilibili.com` /
  `space.bilibili.com`, or `gavinschneestudio.org`. Other hosts are
  rejected by CI to keep the gallery free of phishing / SEO spam.
  Need a host added? Open an issue or include the rationale in your PR.
- **License** — see [Licenses](#licenses) below.
- **Category** — `photo` / `illustration` / `branding` / `universal` / `other`.

That's it. Free-text classification lives in the existing `tags` field;
model compatibility is something the gallery surfaces by letting visitors
try the template, so contributors don't need to predict it.

These fields are saved alongside the prompt and travel with the
exported file — there is no separate `meta.yml` to maintain.

### 3. Export the `.nyxtemplate` file

Right-click the template → **Export…** and save the `.nyxtemplate` file
somewhere convenient. The exported file is a single self-contained JSON
document with the cover image embedded and the community block already
filled in — no missing assets, no follow-up commits.

<p align="center">
  <img src="../assets/screenshots/exporttemplate.png" width="720" alt="Exporting a template as .nyxtemplate">
</p>

### 4. Open a Pull Request

1. Fork this repository.
2. Drop your `.nyxtemplate` file into [`community/templates/`](templates/).
   Pick a clear, URL-safe filename (no spaces or `?:*`); the filename
   minus the extension becomes the template's slug on the gallery.
3. Commit with a message like `Add template: <name>`.
4. Open a Pull Request.

### 5. Wait for CI (one round, ~1 minute)

The **Community templates** workflow will:

1. Validate the schema (v2) and the embedded community block.
2. Scan the prompt body for accidentally-pasted secrets.
3. Decode and sanity-check the embedded cover image.
4. Build a preview of the gallery covers and attach them as a workflow
   artifact, so reviewers can see the actual images without staring at
   base64 in the JSON diff.

That's it — no bot rewriting your branch, no second commit needed.

### 6. Review

A maintainer will review for content policy, quality, and whether it
duplicates an existing template. We may suggest small edits or
adjustments. Once merged, the gallery is rebuilt automatically on the
next push to `main` and your template appears at
`https://gavinharbus.github.io/nyxastra-app/`.

---

## Path B — open an issue (no git required)

If you don't use git, [open an issue using the **Submit a template**
template][issue-template] and attach your `.nyxtemplate` file. A
maintainer will create the Pull Request for you.

[issue-template]: https://github.com/GavinHarbus/nyxastra-app/issues/new?template=template_issue.yml

---

## What makes a good template?

| ✅ Yes | ❌ No |
|---|---|
| A clear, reusable prompt with named variables | A one-off prompt for a single image |
| Cover image generated with the template itself | Cover image taken from another source |
| Variables that meaningfully change the output | Variables that don't affect anything |
| Parameter preset matched to the style (size, quality) | Random parameter preset |
| 1–8 variables (more becomes a chore to fill) | 20+ micro-variables |

*Featured templates* are picked entirely by maintainers and live in
[`community/featured.yml`](featured.yml) — there is no "feature me"
button on the contributor side.

---

## Licenses

Pick one in the **Community Sharing** section:

| License | Meaning |
|---|---|
| `CC0-1.0` | Public domain. Anyone can use, modify, redistribute, commercially or otherwise. |
| `CC-BY-4.0` | Free to use; attribution required. **Recommended for most contributions.** |
| `CC-BY-SA-4.0` | Free to use; attribution required; derivatives must use the same license. |
| `All Rights Reserved` | Visible in the gallery but no permission to redistribute or modify. *Not recommended.* |

If you don't pick a license, the maintainers will assume `CC-BY-4.0`
and credit you as the author.

---

## Code of conduct

Be kind, assume good faith, and follow the
[content policy](CONTENT_POLICY.md). Reviewers are humans donating their
time — feedback may take a few days.

Thanks again for contributing!
