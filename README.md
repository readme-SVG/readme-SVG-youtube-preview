# 🎬 YT Badge — YouTube Card Generator

Generate clickable SVG cards from YouTube links — drop them in any GitHub README or website.

## What you get

A card with the video thumbnail and title, linking to the video on YouTube.

```markdown
[![Watch on YouTube](https://your-app.vercel.app/badge?id=dQw4w9WgXcQ)](https://youtube.com/watch?v=dQw4w9WgXcQ)
```

## Deploy to Vercel (free)

```bash
# 1. Clone and enter the folder
git clone <your-repo> && cd yt-badge

# 2. Install Vercel CLI
npm i -g vercel

# 3. Deploy
vercel
```

Done! Your badge service is live.

## API

```
GET /badge?url=https://youtube.com/watch?v=VIDEO_ID
GET /badge?id=VIDEO_ID
```

| Param | Default | Description |
|---|---|---|
| `url` / `id` | — | YouTube URL or bare video ID (required) |
| `width` | `320` | Card width in px (200–600) |
| `radius` | `10` | Border radius (0–30) |
| `bg` | `0f1117` | Background colour (hex, no `#`) |
| `title_color` | `ffffff` | Title text colour |
| `embed` | `true` | Embed thumbnail as base64 (set `false` for speed) |

## Run locally

```bash
pip install flask gunicorn
gunicorn api.index:app
# open http://localhost:8000
```

## How it works

- **No API key needed** — title fetched via YouTube's public oEmbed endpoint
- **Thumbnail** embedded as base64 so it renders in GitHub READMEs
- SVG cached 1 hour via `Cache-Control`
