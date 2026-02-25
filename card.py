import base64
import textwrap
import urllib.request
from typing import Optional


def fetch_image_as_base64(url: str) -> Optional[str]:
    """Fetch image from URL and return as base64 data URI"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "image/jpeg").split(";")[0]
            encoded = base64.b64encode(data).decode("utf-8")
            return f"data:{content_type};base64,{encoded}"
    except Exception:
        return None


def wrap_title(title: str, max_chars: int = 34, max_lines: int = 2) -> list[str]:
    """Wrap title text into lines"""
    lines = textwrap.wrap(title, width=max_chars)
    return lines[:max_lines]


def format_duration(seconds: Optional[int]) -> Optional[str]:
    """Format seconds to MM:SS or HH:MM:SS"""
    if seconds is None:
        return None
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(views: Optional[int]) -> Optional[str]:
    """Format view count"""
    if views is None:
        return None
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    return f"{views} views"


def generate_svg(
    video_id: str,
    title: str,
    channel: str,
    views: Optional[int] = None,
    duration_seconds: Optional[int] = None,
    width: int = 320,
    background_color: str = "#0d1117",
    title_color: str = "#ffffff",
    stats_color: str = "#adbac7",
    border_radius: int = 8,
    embed_thumbnail: bool = True,
) -> str:
    """Generate SVG card for a YouTube video"""

    thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    thumb_height = int(width * 9 / 16)
    card_height = thumb_height + 72

    # Try to embed thumbnail as base64 (works in GitHub README)
    thumb_data = None
    if embed_thumbnail:
        thumb_data = fetch_image_as_base64(thumb_url)

    thumb_src = thumb_data if thumb_data else thumb_url

    title_lines = wrap_title(title, max_chars=int(width / 8.5), max_lines=2)
    title_svg_lines = ""
    for i, line in enumerate(title_lines):
        y = thumb_height + 18 + i * 17
        title_svg_lines += f'<text x="12" y="{y}" fill="{title_color}" font-size="13" font-weight="600" font-family="\'Segoe UI\', system-ui, sans-serif" xml:space="preserve">{_escape(line)}</text>\n'

    # Stats line
    stats_parts = []
    if channel:
        stats_parts.append(_escape(channel))
    if views is not None:
        stats_parts.append(format_views(views) or "")
    stats_text = " · ".join(filter(None, stats_parts))

    stats_y = thumb_height + 18 + len(title_lines) * 17 + 2
    stats_svg = f'<text x="12" y="{stats_y}" fill="{stats_color}" font-size="11" font-family="\'Segoe UI\', system-ui, sans-serif">{stats_text}</text>' if stats_text else ""

    # Duration badge
    duration_svg = ""
    duration_str = format_duration(duration_seconds)
    if duration_str:
        dur_w = len(duration_str) * 7 + 10
        dur_x = width - dur_w - 6
        dur_y = thumb_height - 22
        duration_svg = f'''
        <rect x="{dur_x}" y="{dur_y}" width="{dur_w}" height="16" rx="3" fill="rgba(0,0,0,0.85)"/>
        <text x="{dur_x + dur_w // 2}" y="{dur_y + 11}" fill="#ffffff" font-size="10" font-weight="700"
              font-family="\'Segoe UI\', system-ui, sans-serif" text-anchor="middle">{duration_str}</text>
        '''

    # Play button overlay
    play_cx = width // 2
    play_cy = thumb_height // 2
    play_svg = f'''
    <circle cx="{play_cx}" cy="{play_cy}" r="26" fill="rgba(0,0,0,0.6)"/>
    <polygon points="{play_cx - 9},{play_cy - 13} {play_cx + 16},{play_cy} {play_cx - 9},{play_cy + 13}"
             fill="#ffffff" opacity="0.95"/>
    '''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{card_height}" viewBox="0 0 {width} {card_height}">

  <!-- Background -->
  <rect width="{width}" height="{card_height}" rx="{border_radius}" fill="{background_color}"/>

  <!-- Thumbnail clip -->
  <clipPath id="thumb-clip">
    <rect width="{width}" height="{thumb_height}" rx="{border_radius}" ry="{border_radius}"/>
  </clipPath>

  <!-- Bottom corners square for thumbnail -->
  <rect y="{thumb_height - border_radius}" width="{width}" height="{border_radius}" fill="{background_color}" clip-path="url(#thumb-clip)"/>

  <!-- Thumbnail image -->
  <image href="{thumb_src}" x="0" y="0" width="{width}" height="{thumb_height}"
         preserveAspectRatio="xMidYMid slice" clip-path="url(#thumb-clip)"/>

  <!-- Play button -->
  {play_svg}

  <!-- Duration badge -->
  {duration_svg}

  <!-- Text area -->
  {title_svg_lines}
  {stats_svg}

  <!-- Border -->
  <rect width="{width}" height="{card_height}" rx="{border_radius}" fill="none"
        stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
</svg>'''

    return svg


def _escape(text: str) -> str:
    """Escape XML special characters"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )
