import base64
import textwrap
import urllib.request
from typing import Optional


def fetch_image_as_base64(url: str) -> Optional[str]:
    """Fetch image from URL and return as base64 data URI (needed for GitHub README)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{content_type};base64,{encoded}"
    except Exception:
        return None


def wrap_title(title: str, max_chars: int = 38, max_lines: int = 2) -> list[str]:
    lines = textwrap.wrap(title, width=max_chars)
    return lines[:max_lines]


def _escape(text: str) -> str:
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
    width: int = 320,
    background_color: str = "#0f1117",
    title_color: str = "#ffffff",
    border_radius: int = 10,
    embed_thumbnail: bool = True,
) -> str:
    """
    Generate a clean SVG card: thumbnail (16:9) + title below.
    """
    thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    thumb_height = int(width * 9 / 16)

    title_lines = wrap_title(title, max_chars=max(20, int(width / 8.2)), max_lines=2)
    line_height = 19
    title_padding_top = 14
    title_padding_bottom = 14
    text_area_height = title_padding_top + len(title_lines) * line_height + title_padding_bottom
    card_height = thumb_height + text_area_height

    thumb_src = thumb_url
    if embed_thumbnail:
        embedded = fetch_image_as_base64(thumb_url)
        if embedded:
            thumb_src = embedded

    r = border_radius
    thumb_clip = f"""
    <clipPath id="tc">
      <path d="M{r},0 H{width - r} Q{width},0 {width},{r} V{thumb_height} H0 V{r} Q0,0 {r},0 Z"/>
    </clipPath>"""

    cx, cy = width // 2, thumb_height // 2
    play = f"""
    <g>
      <circle cx="{cx}" cy="{cy}" r="28" fill="rgba(0,0,0,0.55)" stroke="rgba(255,255,255,0.15)" stroke-width="1.5"/>
      <polygon points="{cx-10},{cy-14} {cx+18},{cy} {cx-10},{cy+14}" fill="#ffffff" opacity="0.97"/>
    </g>"""

    grad_y = thumb_height - 48
    gradient_def = f"""
    <defs>
      {thumb_clip}
      <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="transparent"/>
        <stop offset="100%" stop-color="rgba(0,0,0,0.35)"/>
      </linearGradient>
    </defs>"""

    title_svg = ""
    for i, line in enumerate(title_lines):
        y = thumb_height + title_padding_top + (i + 1) * line_height - 3
        title_svg += (
            f'<text x="14" y="{y}" '
            f'fill="{_escape(title_color)}" '
            f'font-size="13.5" font-weight="600" '
            f'font-family="\'Segoe UI\',\'Helvetica Neue\',Arial,sans-serif" '
            f'letter-spacing="-0.01em">'
            f'{_escape(line)}</text>\n    '
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{card_height}" viewBox="0 0 {width} {card_height}" role="img"
     aria-label="{_escape(title)}">
  {gradient_def}

  <!-- Card background -->
  <rect width="{width}" height="{card_height}" rx="{r}" fill="{_escape(background_color)}"/>

  <!-- Thumbnail -->
  <image href="{thumb_src}" x="0" y="0" width="{width}" height="{thumb_height}"
         preserveAspectRatio="xMidYMid slice" clip-path="url(#tc)"/>

  <!-- Gradient fade at bottom of thumbnail -->
  <rect x="0" y="{grad_y}" width="{width}" height="48" fill="url(#fade)" clip-path="url(#tc)"/>

  <!-- Play button -->
  {play}

  <!-- Title -->
  {title_svg}

  <!-- Red accent bar top -->
  <rect x="0" y="0" width="{width}" height="3" fill="#ff0033"/>

  <!-- Border overlay -->
  <rect width="{width}" height="{card_height}" rx="{r}" fill="none"
        stroke="rgba(255,255,255,0.07)" stroke-width="1"/>
</svg>"""

    return svg
