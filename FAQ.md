# FAQ

## General

**What is NyxAstra?**

NyxAstra is a native, local-first app for generating AI images with GPT Image models on Mac, iPhone, iPad and Windows. Generation uses your own provider account. The Mac app also offers optional NyxAstra accounts, creator submissions and Discover templates.

**Is it free?**

Yes. NyxAstra is free to download and use. You pay your selected AI provider directly for API usage.

**Do I need my own API key?**

Yes. You need an API key from [OpenAI](https://platform.openai.com/) or an [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) deployment. NyxAstra connects directly to your own provider account.

**Where can I download NyxAstra?**

The current Apple app is available from the [App Store](https://apps.apple.com/us/app/nyxastra/id6804567608?mt=12) for Mac, iPhone, and iPad in supported regions. The existing macOS DMG remains available from [GitHub Releases](https://github.com/GavinHarbus/nyxastra-app/releases), including for regions where the App Store listing is unavailable, but it is an earlier preview and does not include GPT Image 2.5 or 2.6. Windows builds are published in the separate [Windows repository](https://github.com/bbkgl/NyxAstraApp-Win/releases).

## Models & Capabilities

**Which models are supported?**

| Release | Supported models |
|---|---|
| Mac 1.3.1 | OpenAI: `gpt-image-2.6-flare`, `gpt-image-2.6-sunburst`, plus earlier models. Azure retains earlier model choices. |
| Mac / iPhone / iPad v1.1 baseline | `gpt-image-2.5-sunburst`, `gpt-image-2.5-flare`, `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |
| Existing direct-download DMG | `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |
| Windows | `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |

Mac 1.3.1 (build 17) is available on the App Store. Its 2.6 integration uses OpenAI. This Mac update does not announce an iPhone/iPad, direct DMG or Windows update. Model access depends on your provider account.

**Can I use reference images?**

Yes. Add reference images in the Generate view to guide generation or editing. Limits depend on the selected model.

**Which quality and Complexity options can I choose?**

GPT Image 2.5 and the Mac 1.3.1 integration of 2.6 offer `auto`, `low`, `medium`, `high`, `xhigh` and `max` quality. GPT Image 2.6 also offers Low, Medium and High Complexity, which controls planning independently of quality.

**Can I create SVG or GIF files?**

Mac 1.3.1 adds both formats through OpenAI's GPT Image 2.6 models. SVG generates one vector image without references. GIF supports text or static PNG/JPEG/WebP references, 2–16 frames and 20–2000 ms per frame. GIF generation requires your OpenAI account's GIF preview permission. Original SVG/GIF files are preserved on export.

**Will new templates work in older clients?**

Ordinary raster templates remain v2; SVG templates use v3 and GIF templates use v4. Older clients may ask for an update when opening v3/v4. Check that your client also supports the recipe's model, quality and format. Gallery covers stay PNG/JPEG/WebP even when the recipe produces SVG or GIF.

**What's the maximum image size?**

The Mac app's static-image controls for GPT Image 2, 2.5 and 2.6 allow custom dimensions: each edge is a multiple of 16 and at most 3840 pixels, aspect ratio is between 1:3 and 3:1, and total pixels are between 655,360 and 8,294,400. Earlier models use 1024×1024, 1024×1536 and 1536×1024 presets. GIF frame size defaults to Auto and uses separate limits; the provider checks the combined animation pixel budget.

## Privacy & Security

**Does the app collect any data?**

Generation and library storage are local-first. Optional accounts, creator submissions, Discover and App Store purchases use their respective services. See the current [NyxAstra Privacy Policy](https://gavinschneestudio.org/nyxastra/privacy.html) for what those services process.

**What leaves my device?**

Credentials, history, templates, and generated images are stored locally. When you authorize a generation request, its prompt, parameters, and any reference images are sent directly to the OpenAI or Azure OpenAI endpoint you configured. NyxAstra does not proxy the request through a Gavin Schnee Studio server.

**How are my API keys stored?**

macOS uses an AES-256-GCM encrypted vault in the app sandbox, Windows uses DPAPI, and iPhone/iPad use the device-only system Keychain. Keys are not stored on a NyxAstra server.

**Where are my images stored?**

Images stay in the app's local storage until you export or share them. On iPhone and iPad, system pickers and the share sheet handle selecting, sharing, or saving images without giving NyxAstra unrestricted Photos access.

## Troubleshooting

**Generation is taking a long time**

High-quality generation can take longer depending on model, quality, size, provider load, and network conditions. The elapsed timer on the Generate view confirms that a request is still active.

**I get an authentication error**

Double-check your API key in Settings. For Azure OpenAI, verify that your endpoint URL and deployment name are correct and that the selected model family matches the deployment.

**Can I use NyxAstra on Linux?**

No Linux build is currently available. NyxAstra supports macOS 14+, iOS/iPadOS 17+, and Windows x64.

## Contact

Have a question not covered here? [Open an issue](https://github.com/GavinHarbus/nyxastra-app/issues/new/choose) or visit [gavinschneestudio.org](https://gavinschneestudio.org/).
