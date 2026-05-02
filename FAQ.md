# FAQ

## General

**What is NyxAstra?**
NyxAstra is a native macOS app for generating AI images using OpenAI's GPT-Image models. It runs entirely on your Mac — no account registration, no cloud backend, no subscriptions.

**Is it free?**
Yes. NyxAstra is free to download and use.

**Do I need my own API key?**
Yes. You need an API key from [OpenAI](https://platform.openai.com/) or an [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service) deployment. NyxAstra does not provide API access — it connects to your own account.

## Models & Capabilities

**Which models are supported?**
- gpt-image-2 (up to 4K resolution, transparent background, reference image editing)
- gpt-image-1.5
- gpt-image-1

**Can I use reference images?**
Yes. Drag & drop reference images onto the Generate view to guide generation. This uses the model's edit (inpainting) capability.

**What's the maximum image size?**
Up to 4096x4096 with gpt-image-2. Other models support standard sizes (1024x1024, 1024x1792, 1792x1024).

## Privacy & Security

**Does the app collect any data?**
No. Zero telemetry, zero analytics, zero crash reporting. See the full [Privacy Policy](PRIVACY.md).

**How are my API keys stored?**
Encrypted locally with AES-256-GCM. Keys are never stored in plaintext and never leave your Mac except when sent directly to your configured API endpoint.

**Where are my images stored?**
In the app's local sandbox directory on your Mac. You can export them anywhere via the Library.

## Troubleshooting

**Generation is taking a long time**
High-quality gpt-image-2 generations can take 60-180 seconds. NyxAstra has extended timeouts (up to 5 minutes) to handle this. The elapsed timer on the Generate view confirms the request is still active.

**I get an authentication error**
Double-check your API key in Settings. For Azure OpenAI, verify that your endpoint URL and deployment name are correct.

**Can I use NyxAstra on Windows or Linux?**
Not currently. NyxAstra is a native macOS app built with SwiftUI and requires macOS 14.0 (Sonoma) or later.

## Contact

Have a question not covered here? [Open an issue](https://github.com/GavinHarbus/nyxastra-app/issues/new/choose) or visit [gavinschneestudio.org](https://gavinschneestudio.org/).
