<div align="center">

[![SVG Animation](https://readme-svg-typing-generator.vercel.app/api?lines=YouTube%20Badge%20Generator&animation=stroke&color=ff0000&background=00000000&size=52&font=monospace&duration=7000&pause=0&width=700&height=60&letterSpacing=-0.05em&center=false&vCenter=false&multiline=false&repeat=true&random=false)](https://github.com/OstinUA)

Embed clickable YouTube cards in any GitHub README — no API key required

[![Deploy to Vercel](https://img.shields.io/badge/Deploy%20to-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/new/clone?repository-url=https://github.com/readme-SVG/readme-SVG-youtube-preview)
[![No API Key](https://img.shields.io/badge/No%20API%20Key-Required-22c55e?style=for-the-badge&logo=youtube&logoColor=white)](#how-it-works)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/Apache-2.0)
[![SVG Output](https://img.shields.io/badge/Output-Pure%20SVG-ff0000?style=for-the-badge)](#)

</div>

---

## ✨ What is this?

**readme-SVG-youtube-preview** turns any YouTube URL into a **clickable, styled SVG card** you can drop into any GitHub README, Markdown file, or webpage.

```markdown
[![Watch on YouTube](https://your-app.vercel.app/badge?id=dQw4w9WgXcQ)](https://youtube.com/watch?v=dQw4w9WgXcQ)
```

> The thumbnail is embedded as **base64 inside the SVG** — so it renders perfectly inside GitHub README without being blocked by GitHub's image proxy.

---

## 🎬 Live Examples

<div align="center">

[![YouTube video](https://readme-svg-youtube-preview.vercel.app/badge?id=FHCoToqLIEg&width=320&radius=8&bg=0d1117&title_color=ffffff&title_opacity=1&plate_color=0f1117&plate_opacity=0.78&title_position=outside_bottom&border_width=1&border_color=ff0000)](https://www.youtube.com/watch?v=FHCoToqLIEg) [![YouTube video](https://readme-svg-youtube-preview.vercel.app/badge?id=hHwY3NDvCAw&width=320&radius=8&bg=0d1117&title_color=ffffff&title_opacity=1&plate_color=0f1117&plate_opacity=0.78&title_position=outside_bottom&border_width=1&border_color=ffffff)](https://www.youtube.com/watch?v=hHwY3NDvCAw) [![YouTube video](https://readme-svg-youtube-preview.vercel.app/badge?id=SAmPKZr-Rm4&width=320&radius=8&bg=0d1117&title_color=ffffff&title_opacity=1&plate_color=0f1117&plate_opacity=0.78&title_position=outside_bottom&border_width=1&border_color=ff0000)](https://www.youtube.com/watch?v=SAmPKZr-Rm4)

</div>

---

## ⚡ Quick Start

### Step 1 — Deploy your own instance

```bash
# Clone and enter the folder
git clone https://github.com/readme-SVG/readme-SVG-youtube-preview.git
cd readme-SVG-youtube-preview

# Install Vercel CLI and deploy (free)
npm install -g vercel
vercel
```

Done! Copy your Vercel URL — that becomes your `BASE_URL`.

### Step 2 — Add to your README

```markdown
[![Watch on YouTube](https://BASE_URL/badge?id=VIDEO_ID)](https://youtube.com/watch?v=VIDEO_ID)
```

**That's it.** Replace `BASE_URL` with your Vercel domain and `VIDEO_ID` with any YouTube video ID.

> **One-click deploy:**  
> [![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/readme-SVG/readme-SVG-youtube-preview)

---

## 🛠️ API Reference

```
GET /badge?id=VIDEO_ID
GET /badge?url=https://youtube.com/watch?v=VIDEO_ID
```

### Parameters

<div align="center">

| Parameter | Default | Range | Description |
|:---|:---:|:---:|:---|
| `url` or `id` | — | **required** | YouTube full URL or bare video ID |
| `width` | `320` | `200 – 600` | Card width in pixels |
| `radius` | `10` | `0 – 30` | Corner border radius |
| `bg` | `0f1117` | hex, no `#` | Background color |
| `title_color` | `ffffff` | hex, no `#` | Title text color |
| `title_opacity` | `1` | `0 – 1` | Title text opacity |
| `plate_color` | auto | hex, no `#` | Bottom label background |
| `plate_opacity` | `0.85` | `0 – 1` | Bottom label opacity |

</div>

### Example URLs

```bash
# Bare video ID — simplest form
/badge?id=dQw4w9WgXcQ

# Full YouTube URL
/badge?url=https://youtube.com/watch?v=dQw4w9WgXcQ

# Dark red theme, larger card
/badge?id=dQw4w9WgXcQ&bg=120000&title_color=FF4444&radius=16&width=420

# Light theme, sharp corners
/badge?id=dQw4w9WgXcQ&bg=ffffff&title_color=111111&radius=4

# Neon on black
/badge?id=dQw4w9WgXcQ&bg=020010&title_color=00FFAA&plate_color=0a0030&radius=14

# Wide card
/badge?id=dQw4w9WgXcQ&width=560&radius=10
```

---

## 🏗️ How It Works

```
Request: /badge?id=dQw4w9WgXcQ
               │
               ▼
   YouTube oEmbed API  ──────────────────────────
   (public endpoint,                             │
    no API key needed)                     title + thumbnail_url
               │
               ▼
   Fetch thumbnail image
   Encode as base64
   (GitHub blocks external img in SVGs)
               │
               ▼
   Render SVG:
   ┌───────────────────────────────┐
   │  [base64 thumbnail image]     │
   │                               │
   │  ▶  Video Title Here          │
   └───────────────────────────────┘
   Entire card = clickable <a> link
               │
               ▼
   Response served with:
   Cache-Control: public, max-age=3600
```

### Why SVG + base64?

| Approach | GitHub renders? | Clickable? | Sharp on Retina? |
|:---|:---:|:---:|:---:|
| Linked PNG | ✅ | ❌ | ❌ |
| SVG with external `<image>` | ❌ blocked | ✅ | ✅ |
| **SVG with base64 thumbnail** | **✅** | **✅** | **✅** |

GitHub's Markdown sanitizer strips external URLs from `<image>` tags inside SVGs. Embedding as base64 bypasses this — the image data travels inside the SVG itself.

---

## 🎨 Style Recipes

Ready-made themes to copy-paste:

```markdown
<!-- Dark (default) -->
[![Video](https://BASE_URL/badge?id=ID&bg=0f1117&title_color=ffffff&radius=12)](https://youtube.com/watch?v=ID)

<!-- YouTube Red -->
[![Video](https://BASE_URL/badge?id=ID&bg=1a0000&title_color=FF4444&radius=8&plate_color=2a0000)](https://youtube.com/watch?v=ID)

<!-- GitHub Dark -->
[![Video](https://BASE_URL/badge?id=ID&bg=161b22&title_color=e6edf3&radius=6)](https://youtube.com/watch?v=ID)

<!-- Clean Light -->
[![Video](https://BASE_URL/badge?id=ID&bg=ffffff&title_color=24292f&radius=6)](https://youtube.com/watch?v=ID)

<!-- Neon -->
[![Video](https://BASE_URL/badge?id=ID&bg=020010&title_color=00FFAA&plate_color=0a0030&radius=16)](https://youtube.com/watch?v=ID)

<!-- Minimal, no rounding -->
[![Video](https://BASE_URL/badge?id=ID&bg=0d0d0d&title_color=cccccc&radius=0&width=360)](https://youtube.com/watch?v=ID)
```

---

## 🔄 Comparison

<div align="center">

| Feature | **readme-SVG-youtube-preview** | github-readme-youtube-cards |
|:---|:---:|:---:|
| No YouTube API key needed | ✅ | ❌ |
| Single video card | ✅ | ❌ channel-only |
| Renders inside GitHub README | ✅ base64 | ✅ |
| Custom colors via URL params | ✅ | ❌ theme files |
| GitHub Actions required | ❌ | ✅ |
| Setup time | ~30 sec | ~10 min |
| Self-hosted on Vercel | ✅ | ✅ |

</div>

---

## 🚀 Deploy Options

### Vercel _(recommended, free)_

```bash
npm install -g vercel
vercel
```

### Railway

```bash
railway login && railway up
```

### Self-hosted (Node.js)

```bash
npm install
npm start
# Running on http://localhost:3000
```

---

## 🤝 Contributing

```bash
# Fork, then:
git clone https://github.com/YOUR_USERNAME/readme-SVG-youtube-preview.git
cd readme-SVG-youtube-preview
npm install
npm run dev
```

PRs welcome for:
- New built-in theme presets
- Additional URL parameters (e.g. font size, icon style)
- Bug fixes and performance improvements
- Translations and documentation

Check [open issues](https://github.com/readme-SVG/readme-SVG-youtube-preview/issues) before starting.

---

<div align="center">

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 60" width="600">
  <rect width="600" height="60" fill="#0f1117" rx="10"/>
  <text x="300" y="26" text-anchor="middle" font-family="'Segoe UI', system-ui, sans-serif" font-size="13" fill="#8b949e">If this saved you time, consider giving it a</text>
  <text x="300" y="46" text-anchor="middle" font-family="'Segoe UI', system-ui, sans-serif" font-size="13" fill="#e6edf3">⭐ star — it helps others find the project</text>
</svg>

<br/><br/>

*Part of the [readme-SVG](https://github.com/readme-SVG) collection — beautiful SVG components for GitHub READMEs*

</div>
