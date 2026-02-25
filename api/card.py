import base64
import textwrap
import urllib.request
from typing import Optional


def fetch_image_as_base64(url: str, fallback_url: Optional[str] = None) -> Optional[str]:
    """
    Fetch image and return as base64 data URI.
    Tries `url` first; if that fails (e.g. maxresdefault not available), tries `fallback_url`.
    Embedding is required so GitHub README can render the image cross-origin.
    """
    for target in filter(None, [url, fallback_url]):
        try:
            req = urllib.request.Request(
                target,
                headers={"User-Agent": "Mozilla/5.0 (compatible; ytbadge/1.0)"},
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                # maxresdefault returns 404 for some videos — detect via status or small size
                data = resp.read()
                if len(data) < 2000:
                    # Likely a 1×1 placeholder — try next
                    continue
                ct = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
                encoded = base64.b64encode(data).decode("utf-8")
                return f"data:{ct};base64,{encoded}"
        except Exception:
            continue
    return None


def _wrap(title: str, max_chars: int, max_lines: int = 2) -> list[str]:
    lines = textwrap.wrap(title, width=max(16, max_chars))
    return lines[:max_lines]


def _esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
    )


def generate_svg(
    video_id: str,
    title: str,
    thumbnail_url: str,
    thumbnail_fallback: Optional[str] = None,
    width: int = 320,
    background_color: str = "#0f1117",
    title_color: str = "#ffffff",
    title_opacity: float = 1.0,
    border_radius: int = 10,
    border_width: int = 1,
    border_color: str = "rgba(255,255,255,0.07)",
    embed_thumbnail: bool = True,
) -> str:
    """
    SVG card: real thumbnail (16:9) on top, title text below.
    No play button. Thumbnail is embedded as base64 for GitHub compatibility.
    """
    thumb_height = int(width * 9 / 16)

    # Embed as base64 so GitHub can render it (GitHub blocks external <image> sources in SVG)
    thumb_src = thumbnail_url  # fallback: direct URL (works on websites, not GitHub)
    if embed_thumbnail:
        embedded = fetch_image_as_base64(thumbnail_url, thumbnail_fallback)
        if embedded:
            thumb_src = embedded
        elif thumbnail_fallback:
            thumb_src = thumbnail_fallback

    # Title sizing
    title_lines = _wrap(title, max_chars=max(18, int(width / 8.0)), max_lines=2)
    line_h = 20
    pad_top = 13
    pad_bot = 13
    text_h = pad_top + len(title_lines) * line_h + pad_bot
    card_h = thumb_height + text_h

    r = border_radius

    # Clip path: rounded top corners only (bottom is square where card bg shows)
    thumb_clip = (
        f'<clipPath id="tc">'
        f'<path d="M{r},0 H{width-r} Q{width},0 {width},{r} V{thumb_height} H0 V{r} Q0,0 {r},0 Z"/>'
        f'</clipPath>'
    )

    # Title lines
    title_svg = ""
    for i, line in enumerate(title_lines):
        y = thumb_height + pad_top + (i + 1) * line_h - 3
        title_svg += (
            f'<text x="14" y="{y}" '
            f'fill="{_esc(title_color)}" '
            f'fill-opacity="{title_opacity:.2f}" '
            f'font-size="13.5" font-weight="600" '
            f'font-family="\'Segoe UI\',\'Helvetica Neue\',Arial,sans-serif" '
            f'letter-spacing="-0.01em">{_esc(line)}</text>\n  '
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{card_h}" viewBox="0 0 {width} {card_h}"
     role="img" aria-label="{_esc(title)}">
  <defs>
    {thumb_clip}
  </defs>

  <!-- Card background -->
  <rect width="{width}" height="{card_h}" rx="{r}" fill="{_esc(background_color)}"/>

  <!-- Thumbnail -->
  <image href="{thumb_src}"
         x="0" y="0" width="{width}" height="{thumb_height}"
         preserveAspectRatio="xMidYMid slice"
         clip-path="url(#tc)"/>

  <!-- Title -->
  {title_svg}

  <!-- Border -->
  <rect width="{width}" height="{card_h}" rx="{r}" fill="none"
        stroke="{_esc(border_color)}" stroke-width="{border_width}"/>
</svg>"""
