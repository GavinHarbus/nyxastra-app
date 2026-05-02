<p align="center">
  <img src="assets/icon.png" width="128" height="128" alt="NyxAstra icon">
</p>

<h1 align="center">NyxAstra</h1>

<p align="center">
  <strong>The AI image studio that stays on your Mac.</strong><br>
  Generate stunning images with GPT-Image-2 — no cloud, no subscriptions, no data leaves your machine.
</p>

<p align="center">
  <a href="https://github.com/gavinvonmandias/nyxastra-app/releases/latest">
    <img src="https://img.shields.io/github/v/release/gavinvonmandias/nyxastra-app?label=Download&style=for-the-badge&color=brightgreen" alt="Download latest release">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-14.0%2B-blue?style=flat-square" alt="macOS 14.0+">
  <img src="https://img.shields.io/badge/Price-Free-green?style=flat-square" alt="Free">
  <img src="https://img.shields.io/badge/Telemetry-None-purple?style=flat-square" alt="No Telemetry">
  <img src="https://img.shields.io/github/downloads/gavinvonmandias/nyxastra-app/total?style=flat-square&label=Downloads" alt="Downloads">
  <img src="https://img.shields.io/github/stars/gavinvonmandias/nyxastra-app?style=flat-square" alt="Stars">
</p>

---

<p align="center">
  <img src="assets/screenshots/generate.png" width="720" alt="NyxAstra Generate view">
</p>

## Why NyxAstra?

Most AI image tools lock you into a web app, charge monthly fees, and route everything through their servers. **NyxAstra is different:**

- **Your API key, your control.** Connect your own OpenAI or Azure OpenAI account. No middleman, no markup.
- **Nothing leaves your Mac.** Zero telemetry. Zero analytics. Images and credentials stored locally with AES-256 encryption.
- **Native macOS experience.** Built with SwiftUI — fast, lightweight, and feels like it belongs on your Mac.
- **Free.** No trials, no feature gates, no subscriptions.

---

## What you can do

### Generate up to 4K images

Full parameter control — quality, size, format, transparent backgrounds, moderation. Supports **gpt-image-2**, gpt-image-1.5, and gpt-image-1.

<p align="center">
  <img src="assets/screenshots/generate.png" width="600" alt="Generation interface">
</p>

### Edit with reference images

Drag & drop reference images to guide the AI. Perfect for style transfer, variations, and iterative refinement.

### Organize everything in the Library

Tag, rate, search, filter, batch export. Every image keeps its full generation metadata embedded in the file.

<p align="center">
  <img src="assets/screenshots/library.png" width="600" alt="Library view">
</p>

### Reusable prompt templates

12 starter templates included. Create your own with variables, multi-choice parameters, and folder organization. Share them as `.nyxtemplate` files.

Browse and download more templates from the **[Template Gallery](templates/)**.

<p align="center">
  <img src="assets/screenshots/usetemplate.png" width="600" alt="Template workflow">
</p>

---

## Privacy — by design, not by promise

| | |
|---|---|
| **Network** | Requests go only to the OpenAI / Azure endpoint *you* configure. Nothing else. |
| **Credentials** | AES-256-GCM encrypted, scoped to your Mac's hardware identity. |
| **Storage** | All data lives in the macOS app sandbox. Uninstall = everything gone. |
| **Telemetry** | None. No analytics, no crash reporting, no phone-home. |
| **Dependencies** | Zero. The app ships with no third-party libraries. |

Read the full [Privacy Policy](PRIVACY.md).

---

## Getting started

1. **Download** the latest `.dmg` from [Releases](https://github.com/gavinvonmandias/nyxastra-app/releases/latest)
2. **Drag** NyxAstra to your Applications folder
3. **Open** NyxAstra and go to Settings
4. **Paste** your OpenAI or Azure OpenAI API key
5. **Generate** your first image

> **Requirements:** macOS 14.0 (Sonoma) or later, Apple Silicon or Intel Mac, your own API key from [OpenAI](https://platform.openai.com/) or [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service).

---

## More

- [Template Gallery](templates/) — download community prompt templates
- [Changelog](CHANGELOG.md) — what's new in each version
- [FAQ](FAQ.md) — common questions answered
- [Privacy Policy](PRIVACY.md) — the full details
- [Product Page](https://gavinschneestudio.com/products/nyxastra.html)

## Feedback & Support

Found a bug? Have an idea? [Open an issue](https://github.com/gavinvonmandias/nyxastra-app/issues/new/choose) — every report helps make NyxAstra better.

---

<p align="center">
  Made by <a href="https://gavinschneestudio.org/">Gavin Schnee Studio</a><br>
  &copy; 2026 Gavin Schnee Studio. All Rights Reserved.
</p>
