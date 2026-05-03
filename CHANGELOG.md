# Changelog

All notable changes to NyxAstra will be documented in this file.

## [0.2.1] - 2026-05-03

### OpenAI API Spec Alignment

**New parameters & options**
- Auto option for Size, Quality, and Background — let the model choose the best setting
- WebP output format support across generation, export, and format detection
- 32,000-character prompt limit (was 4,000), matching the actual API spec

**New model**
- Added gpt-image-1-mini with correct capability defaults

**Validation fixes**
- Transparent background now correctly allowed with both PNG and WebP
- Output compression now works with WebP (previously JPEG-only)
- Auto size bypasses pixel validation as expected

### UX Improvements
- Custom size input: editable text fields replace stepper-only controls — type exact pixel values directly
- Custom size fields auto-snap to the nearest valid multiple of 16 on blur
- "Done" badge now stays visible until you interact with the page, instead of disappearing on a fixed timer

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
