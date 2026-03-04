# readme-SVG YouTube Preview

**Turn any YouTube URL into a GitHub-safe, clickable SVG preview card with zero API-key drama.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](#tech-stack)
[![Vercel Runtime](https://img.shields.io/badge/Runtime-Vercel%20Python-000000?style=for-the-badge&logo=vercel&logoColor=white)](vercel.json)
[![Build](https://img.shields.io/badge/Build-No%20CI%20configured-lightgrey?style=for-the-badge)](#testing)
[![Coverage](https://img.shields.io/badge/Coverage-Not%20Configured-lightgrey?style=for-the-badge)](#testing)

A lightweight Flask service that fetches YouTube metadata via oEmbed, generates polished SVG cards, and optionally embeds thumbnails as base64 so GitHub README rendering doesn’t nuke your preview images.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Technical Notes](#technical-notes)
  - [Project Structure](#project-structure)
  - [Key Design Decisions](#key-design-decisions)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Usage](#usage)
- [Configuration](#configuration)
- [License](#license)
- [Contacts](#contacts)
- [❤️ Support the Project](#️-support-the-project)

## Features

- **YouTube URL parsing that doesn’t flake out**
  - Supports raw 11-char IDs and common formats (`watch?v=`, `youtu.be`, `embed`, `shorts`).
- **Zero API key dependency**
  - Pulls title/thumbnail metadata via public YouTube oEmbed endpoint.
- **GitHub-compatible SVG output**
  - Can embed thumbnail as base64 data URI to bypass GitHub SVG external image restrictions.
- **Highly tweakable card rendering**
  - Width, radius, title opacity, plate opacity, border styling, title placement.
- **Multiple title layouts**
  - `overlay_top`, `overlay_bottom`, `outside_top`, `outside_bottom` (plus aliases).
- **Fast, stateless HTTP API**
  - `/badge` for SVG rendering, `/info` for metadata probing.
- **Cache-friendly responses**
  - `Cache-Control: public, max-age=3600` out of the box.
- **Built-in browser UI**
  - Local playground (`/`) for live config tweaking + instant Markdown/HTML snippet generation.

## Tech Stack

- **Language:** Python (runtime-compatible with Vercel Python serverless)
- **Backend framework:** Flask
- **HTTP layer:** `urllib.request` (standard lib)
- **Serving model:** Vercel serverless via `@vercel/python`
- **Frontend:** vanilla HTML/CSS/JS (`index.html`, `styles.css`, `app.js`)
- **Process server (non-serverless environments):** Gunicorn

## Technical Notes

### Project Structure

```text
.
├── api/
│   ├── __init__.py
│   ├── index.py          # Flask app + routes (/ , /badge, /info)
│   └── card.py           # SVG generation + base64 image embedding
├── app.js                # Frontend logic for generator UI
├── index.html            # Generator UI markup
├── styles.css            # UI styling
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel build/routes config
├── LICENSE
└── README.md
```

### Key Design Decisions

1. **oEmbed over official YouTube Data API**  
   Keeps onboarding friction low: no API keys, no quota setup, no credential handling.

2. **Base64 thumbnail embedding as first-class behavior**  
   GitHub markdown rendering strips/blocks external image references in SVGs, so embedding image payload into SVG is the pragmatic fix.

3. **Server-side SVG composition instead of static templates**  
   Dynamic query parameters let users style cards without forking the project or editing assets.

4. **Hard parameter clamping**  
   Width/radius/opacity/border values are constrained to sane ranges to prevent broken output and tame weird inputs.

5. **Two-route API shape**  
   `/info` for metadata/debugging and `/badge` for render output keeps responsibilities clean and DX nicer.

## Getting Started

### Prerequisites

Install the following before hacking locally:

- Python `3.10+`
- `pip`
- (Optional) virtualenv tooling (`python -m venv`)
- (Optional) Vercel CLI for cloud deploy testing

### Installation

```bash
# 1) Clone your fork (or upstream if you're just evaluating)
git clone https://github.com/readme-SVG/readme-SVG-youtube-preview.git
cd readme-SVG-youtube-preview

# 2) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run Flask app locally (from repository root)
flask --app api.index run --debug
```

Local app should be available at:

```text
http://127.0.0.1:5000
```

## Testing

This repo currently has **no formal unit/integration test suite checked in**. Current baseline validation is smoke-style endpoint checks.

Use these commands locally:

```bash
# Syntax sanity for Python modules
python -m compileall api

# Run local server in one terminal
flask --app api.index run --debug

# In another terminal: metadata endpoint smoke test
curl "http://127.0.0.1:5000/info?id=dQw4w9WgXcQ"

# SVG render smoke test (writes output for manual inspection)
curl "http://127.0.0.1:5000/badge?id=dQw4w9WgXcQ" -o /tmp/card.svg
```

If you’re extending functionality, add tests in your PR (recommended: `pytest`) and document the command in your PR description.

## Deployment

### Vercel (recommended)

```bash
# Install CLI once
npm i -g vercel

# Deploy interactively
vercel
```

`vercel.json` already wires all routes to `api/index.py`, including root UI and API endpoints.

### Generic Python Hosting

```bash
pip install -r requirements.txt
gunicorn -w 2 -b 0.0.0.0:8000 "api.index:app"
```

Then expose via reverse proxy (Nginx/Caddy/Cloud LB) as needed.

### CI/CD Notes

No CI pipeline is currently committed. For production-grade workflows, add:

- lint + format checks
- API smoke tests
- deploy preview per PR
- protected main branch with required checks

## Usage

### Minimal Markdown embed

```markdown
# Swap BASE_URL with your deployed domain and VIDEO_ID with actual YouTube ID
[![Watch on YouTube](https://BASE_URL/badge?id=VIDEO_ID)](https://youtube.com/watch?v=VIDEO_ID)
```

### Full URL input instead of raw video ID

```markdown
# Useful when you already have full YouTube links in scripts/content tooling
[![Watch on YouTube](https://BASE_URL/badge?url=https://youtube.com/watch?v=dQw4w9WgXcQ)](https://youtube.com/watch?v=dQw4w9WgXcQ)
```

### Styled card with explicit visual config

```markdown
# Example with dark palette, outside title plate, and visible border
[![Watch on YouTube](https://BASE_URL/badge?id=dQw4w9WgXcQ&width=420&radius=12&bg=0f1117&title_color=ffffff&title_opacity=1&plate_color=0b0d12&plate_opacity=0.82&title_position=outside_bottom&border_width=1&border_color=ff0000)](https://youtube.com/watch?v=dQw4w9WgXcQ)
```

### API quick reference

```text
GET /badge?id=<VIDEO_ID>
GET /badge?url=<YOUTUBE_URL>
GET /info?id=<VIDEO_ID>
GET /info?url=<YOUTUBE_URL>
```

## Configuration

This project is currently mostly **config-via-query-params** (no mandatory `.env` variables).

### Query parameters for `/badge`

- `id` or `url` (required, one of them)
- `width` (default `320`, clamped `200..600`)
- `radius` (default `10`, clamped `0..30`)
- `bg` (default `0f1117`)
- `title_color` (default `ffffff`)
- `title_opacity` (default `1`, clamped `0..1`)
- `plate_color` (default `0f1117`)
- `plate_opacity` (default `0.78`, clamped `0..1`)
- `title_position` (`overlay_top`, `overlay_bottom`, `outside_top`, `outside_bottom`; aliases supported)
- `border_width` (default `1`, clamped `0..10`)
- `border_color` (default `ffffff`)
- `embed` (`true` by default; set `embed=false` to skip base64 embedding)

### Environment variables

No required runtime env vars are hardcoded in the current code path. If you add config, keep `.env.example` in sync and document every key here.

## License

Distributed under the Apache-2.0 License. See [`LICENSE`](LICENSE).

## Contacts

- GitHub org: [`readme-SVG`](https://github.com/readme-SVG)
- Maintainer profile: [`OstinUA`](https://github.com/OstinUA)
- Issues: <https://github.com/readme-SVG/readme-SVG-youtube-preview/issues>

## ❤️ Support the Project

If you find this tool useful, consider leaving a ⭐ on GitHub or supporting the author directly:

[![Patreon](https://img.shields.io/badge/Patreon-OstinFCT-f96854?style=flat-square&logo=patreon)](https://www.patreon.com/OstinFCT)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-fctostin-29abe0?style=flat-square&logo=ko-fi)](https://ko-fi.com/fctostin)
[![Boosty](https://img.shields.io/badge/Boosty-Support-f15f2c?style=flat-square)](https://boosty.to/ostinfct)
[![YouTube](https://img.shields.io/badge/YouTube-FCT--Ostin-red?style=flat-square&logo=youtube)](https://www.youtube.com/@FCT-Ostin)
[![Telegram](https://img.shields.io/badge/Telegram-FCTostin-2ca5e0?style=flat-square&logo=telegram)](https://t.me/FCTostin)
