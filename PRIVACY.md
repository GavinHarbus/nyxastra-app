# Privacy Policy

**Last updated: May 2, 2026**

NyxAstra is designed with privacy as a core principle. This policy explains what data the app handles and how.

## Data Collection

**NyxAstra collects no data.** There is no telemetry, no analytics, no crash reporting, and no backend server.

## Network Requests

NyxAstra makes network requests **only** to the API endpoint you configure in Settings:

- **OpenAI** (`api.openai.com`) — if you choose OpenAI as your provider
- **Azure OpenAI** (your own Azure endpoint) — if you choose Azure OpenAI as your provider

These requests contain your prompt, generation parameters, and reference images (if any). NyxAstra does not proxy, intercept, or store these requests on any third-party server. Your API key is sent directly to the provider you selected.

## Local Storage

All app data is stored locally on your Mac within the app sandbox:

- **API keys** — encrypted with AES-256-GCM using a key derived from your Mac's hardware identity. Never stored in plaintext.
- **Generated images** — saved as PNG or JPEG files in the app's Library directory.
- **Generation history** — stored in a local SwiftData database.
- **Templates** — stored in a local SwiftData database.
- **Preferences** — stored in standard macOS UserDefaults.

## Third-Party Services

NyxAstra has **zero external dependencies** and contacts no third-party services beyond the API endpoint you configure.

## Data Deletion

Uninstalling NyxAstra removes all app data from your Mac. You can also delete individual generations, templates, and credentials from within the app.

## Contact

Questions about this policy? Visit [gavinschneestudio.org](https://gavinschneestudio.org/).
