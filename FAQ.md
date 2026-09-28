# FAQ

## General

**What is NyxAstra?**

NyxAstra is a native, local-first app for generating AI images with GPT Image models. It is available for Mac, iPhone, iPad, and Windows. There is no NyxAstra account, subscription, telemetry, or cloud backend.

**Is it free?**

Yes. NyxAstra is free to download and use. You pay your selected AI provider directly for API usage.

**Do I need my own API key?**

Yes. You need an API key from [OpenAI](https://platform.openai.com/) or an [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) deployment. NyxAstra connects directly to your own provider account.

**Where can I download NyxAstra?**

The current Apple app is available from the [App Store](https://apps.apple.com/us/app/nyxastra/id6804567608?mt=12) for Mac, iPhone, and iPad in supported regions. The existing macOS DMG remains available from [GitHub Releases](https://github.com/GavinHarbus/nyxastra-app/releases), including for regions where the App Store listing is unavailable, but it is an earlier preview and does not include GPT Image 2.5 support. Windows builds are published in the separate [Windows repository](https://github.com/bbkgl/NyxAstraApp-Win/releases).

## Models & Capabilities

**Which models are supported?**

| Release | Supported models |
|---|---|
| Apple app v1.1+ | `gpt-image-2.5-sunburst`, `gpt-image-2.5-flare`, `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |
| Existing direct-download DMG | `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |
| Windows | `gpt-image-2`, `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |

[OpenAI's image generation guide](https://developers.openai.com/api/docs/guides/image-generation) describes GPT Image 2.5 Flare as the fast, high-quality option for everyday generation and Sunburst as the option for workflows where editing precision matters most. Model access can depend on your OpenAI or Azure OpenAI account and deployment.

**Can I use reference images?**

Yes. Add reference images in the Generate view to guide generation or editing. Limits depend on the selected model.

**What quality options does GPT Image 2.5 support?**

In addition to `auto`, `low`, `medium`, and `high`, GPT Image 2.5 Flare and Sunburst support `xhigh` and `max`.

**What's the maximum image size?**

GPT Image 2 and GPT Image 2.5 support custom dimensions. Each edge must be a multiple of 16, neither edge may exceed 3840 pixels, the aspect ratio must be between 1:3 and 3:1, and total pixel count must be between 655,360 and 8,294,400. Earlier GPT Image models use the standard 1024×1024, 1024×1536, and 1536×1024 presets.

## Privacy & Security

**Does the app collect any data?**

No. NyxAstra has no telemetry, analytics, crash reporting, or backend server. See the full [Privacy Policy](PRIVACY.md).

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
