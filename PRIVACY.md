# Privacy Policy

**Last updated: September 13, 2026**

NyxAstra is designed with privacy as a core principle. This policy explains what data the app handles and how.

## Data Collection

**NyxAstra collects no data.** There is no telemetry, no analytics, no crash reporting, and no backend server.

## Network Requests

After you authorize AI provider requests, NyxAstra makes network requests **only** to the API endpoint you configure in Settings:

- **OpenAI** (`api.openai.com`) — if you choose OpenAI as your provider
- **Azure OpenAI** (your own Azure endpoint) — if you choose Azure OpenAI as your provider

These requests contain your prompt, generation parameters, and reference images (if any). NyxAstra does not proxy, intercept, or send these requests through a Gavin Schnee Studio server. Your API key and request are sent directly to the provider you selected. The provider handles submitted content under its terms, privacy policy, and the data controls of your provider account.

## Local Storage

App data is stored locally on your device using the storage appropriate to each platform:

- **API keys** — stored using platform-specific protection: AES-256-GCM with a randomly generated local master key on macOS, Windows DPAPI on Windows, and the device-only system Keychain on iPhone and iPad.
- **Generated images** — saved as PNG or JPEG files in the app's Library directory.
- **Generation history** — stored in a local SwiftData database.
- **Templates** — stored in a local SwiftData database.
- **Preferences** — stored in standard UserDefaults.

### iOS and iPadOS

On iPhone and iPad, API keys are stored in the system Keychain with a device-only accessibility class, so they do not sync through iCloud. The system Photos picker gives NyxAstra access only to images you select. Sharing or saving generated images is handled by the system share sheet; NyxAstra does not request direct access to your Photos library.

## Third-Party Services

NyxAstra has **zero bundled third-party SDK dependencies**. It contacts no third-party service beyond the OpenAI or Azure OpenAI endpoint you configure. OpenAI, Microsoft, and your Azure account owner may process and retain submitted content according to the terms and data controls that apply to your provider account.

## Data Deletion

You can delete individual generations and templates in NyxAstra, remove provider credentials in Settings, and disable AI provider requests under Data & Privacy. Files exported or saved outside the app remain there until you delete them. On iPhone and iPad, remove provider credentials in Settings before uninstalling if you also want to delete Keychain items; deleting the app removes its local app container. On macOS, you can remove any remaining sandbox data by deleting NyxAstra's container from your user Library. Windows app data is stored under `%LOCALAPPDATA%\NyxAstra`.

## Contact

Questions about this policy? Visit [gavinschneestudio.org](https://gavinschneestudio.org/).
