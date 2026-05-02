# NyxAstra Prompt Templates

Community-curated prompt templates for [NyxAstra](../README.md).

## How to use

**Single template (`.nyxtemplate`)**
1. Click a `.nyxtemplate` file → Download
2. Double-click the file, or drag it into NyxAstra's Templates view
3. Fill in the variables and generate

**Template pack (`.nyxtemplates`)**
1. Download the `.nyxtemplates` file from [Releases](https://github.com/gavinvonmandias/nyxastra-app/releases)
2. Double-click to import all templates at once

## Categories

| Folder | Description |
|--------|-------------|
| [photo/](photo/) | Cinematic portraits, product photography, realistic styles |
| [illustration/](illustration/) | Anime, watercolor, pixel art, posters, line art |
| [branding/](branding/) | Logos, icons, brand assets |

## Create your own

1. In NyxAstra, design a prompt with `{{variables}}`
2. Right-click the template → Export as `.nyxtemplate`
3. Share it here by [opening an issue](https://github.com/gavinvonmandias/nyxastra-app/issues/new) with your file attached

## Template format

Templates are JSON files with these fields:

```json
{
  "schema": "nyxtemplate",
  "version": 1,
  "name": "Template Name",
  "body": "A {{subject}} in {{style}} style",
  "variables": [
    {
      "name": "subject",
      "kind": "text",
      "defaultValue": "cat",
      "description": "What to generate"
    },
    {
      "name": "style",
      "kind": "enumeration",
      "allowedValues": ["watercolor", "oil painting", "pixel art"]
    }
  ],
  "folderName": "illustration",
  "tags": ["art", "creative"]
}
```

Variable kinds: `text`, `multiline`, `enumeration`, `number`.
