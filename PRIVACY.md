# Privacy Policy

**Last updated: August 30, 2026**

NyxAstra is designed with privacy as a core principle. This policy explains what data the app handles and how.

## Data Collection

**NyxAstra collects no data.** There is no telemetry, no analytics, no crash reporting, and no backend server.

## Network Requests

After you authorize AI provider requests, NyxAstra makes network requests **only** to the API endpoint you configure in Settings:

- **OpenAI** (`api.openai.com`) — if you choose OpenAI as your provider
- **Azure OpenAI** (your own Azure endpoint) — if you choose Azure OpenAI as your provider

These requests contain your prompt, generation parameters, and reference images (if any). NyxAstra does not proxy, intercept, or send these requests through a Gavin Schnee Studio server. Your API key and request are sent directly to the provider you selected. The provider handles submitted content under its terms, privacy policy, and the data controls of your provider account.

## Local Storage

All app data is stored locally on your device within the app sandbox:

- **API keys** — encrypted with AES-256-GCM using a randomly generated local master key. Never stored in plaintext.
- **Generated images** — saved as PNG or JPEG files in the app's Library directory.
- **Generation history** — stored in a local SwiftData database.
- **Templates** — stored in a local SwiftData database.
- **Preferences** — stored in standard UserDefaults.

### iPadOS

On iPad, API keys are encrypted with AES-256-GCM and stored in the local app sandbox, as on macOS. The system Photos picker gives NyxAstra access only to images you select. Sharing or saving generated images is handled by the system share sheet; NyxAstra does not request direct access to your Photos library.

## Third-Party Services

NyxAstra has **zero bundled third-party SDK dependencies**. It contacts no third-party service beyond the OpenAI or Azure OpenAI endpoint you configure. OpenAI, Microsoft, and your Azure account owner may process and retain submitted content according to the terms and data controls that apply to your provider account.

## Data Deletion

You can delete individual generations and templates in NyxAstra, remove provider credentials in Settings, and disable AI provider requests under Data & Privacy. Files exported or saved outside the app remain there until you delete them. On iPad, deleting NyxAstra removes its local app container. On macOS, you can remove any remaining sandbox data by deleting NyxAstra's container from your user Library.

## Contact

Questions about this policy? Visit [gavinschneestudio.org](https://gavinschneestudio.org/).
