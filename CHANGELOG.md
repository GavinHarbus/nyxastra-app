# Changelog

All notable changes to NyxAstra will be documented in this file.

## [0.2.0] - 2026-05-02

### Initial Public Release

**Generation**
- Full parameter inspector for gpt-image-2, gpt-image-1.5, gpt-image-1
- Quality, size (up to 4K), output format, compression, background transparency, moderation control
- Reference image editing with drag & drop support
- Token usage display per generation

**Templates**
- 12 curated starter templates with variable placeholders
- Create, edit, duplicate, and organize templates in folders
- Import/export as `.nyxtemplate` and `.nyxtemplates` bundles
- Live cover preview from generation results
- Drag-to-reorder within folders

**Library**
- Full generation history with metadata
- Tag, rate (1-5 stars), search by prompt/model/tag/format/rating
- Batch select, export, and delete
- Embedded PNG/JPEG metadata

**Settings**
- Azure OpenAI and OpenAI provider support
- AES-256-GCM encrypted credential storage
- Per-deployment model configuration

**Privacy**
- Zero telemetry, zero analytics
- All data stored locally in app sandbox
- No backend server
