# 🎬 YouTube Badge Generator

Generate clickable SVG badges/cards for YouTube videos to embed in GitHub READMEs or websites.

## Example

Paste a YouTube URL → get a badge like this (click to watch):

[![YouTube video](https://your-domain.vercel.app/badge?id=dQw4w9WgXcQ)](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

## Usage

### Via web interface

Go to `https://your-domain.vercel.app/` and paste your YouTube link.

### Via API

```
GET /badge?url=https://youtube.com/watch?v=VIDEO_ID
```

Or with a bare video ID:

```
GET /badge?id=VIDEO_ID
```

#### Parameters

| Param | Description | Default |
|-------|-------------|---------|
| `url` or `id` | YouTube URL or video ID | required |
| `width` | Card width in pixels | `320` |
| `radius` | Border radius | `8` |
| `bg` | Background color (hex without `#`) | `0d1117` |
| `title_color` | Title text color | `ffffff` |
| `stats_color` | Stats text color | `adbac7` |
| `embed` | Embed thumbnail as base64 (`true`/`false`) | `true` |

### Markdown embed

```markdown
[![Watch on YouTube](https://your-domain.vercel.app/badge?id=VIDEO_ID)](https://youtube.com/watch?v=VIDEO_ID)
```

### HTML embed

```html
<a href="https://youtube.com/watch?v=VIDEO_ID" target="_blank">
  <img src="https://your-domain.vercel.app/badge?id=VIDEO_ID" alt="Watch on YouTube" />
</a>
```

## Deploy to Vercel

1. Fork or clone this repo
2. Install [Vercel CLI](https://vercel.com/cli): `npm i -g vercel`
3. Run `vercel` in the project directory
4. Done! Your badge service is live.

## Run locally

```bash
pip install -r requirements.txt
gunicorn api.index:app
```

Then open `http://localhost:8000`

## How it works

- **No API key needed** — uses YouTube's public oEmbed endpoint for title/channel info
- **Thumbnails** — fetched from `img.youtube.com` and embedded as base64 for GitHub README compatibility
- **SVG generation** — pure Python, no external image libraries required
- SVG cards are cached for 1 hour via `Cache-Control` headers
