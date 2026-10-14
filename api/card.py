import base64
import logging
import re
import textwrap
import urllib.error
from typing import Optional

from .net import TTLCache, fetch_bytes

log = logging.getLogger(__name__)

# Thumbnails are only ever fetched from YouTube's image CDN.
THUMBNAIL_DOMAINS = ("ytimg.com", "youtube.com")
ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
# Real YouTube thumbnails are far larger; anything smaller is a placeholder.
MIN_IMAGE_BYTES = 2000
MAX_IMAGE_BYTES = 2 * 1024 * 1024
THUMBNAIL_TIMEOUT = 8

# Base64 payloads are large, so keep the number of cached images small.
_thumbnail_cache = TTLCache(maxsize=32, ttl=6 * 3600)
# URLs known to have no image (404 or placeholder). Remembering them avoids
# repeating a guaranteed-to-fail request (e.g. maxresdefault for old videos).
_missing_cache = TTLCache(maxsize=512, ttl=3600)

TITLE_POSITIONS = {
    "top": "overlay_top",
    "bottom": "overlay_bottom",
    "overlay_top": "overlay_top",
    "overlay_bottom": "overlay_bottom",
    "outside_top": "outside_top",
    "outside_bottom": "outside_bottom",
}
DEFAULT_TITLE_POSITION = "overlay_bottom"

_HEX_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
# Characters that are not allowed in an XML 1.0 document, even when escaped.
_INVALID_XML_CHARS_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")


def normalize_title_position(value: Optional[str]) -> str:
    """Map a user-supplied title position (or alias) to a canonical value."""
    return TITLE_POSITIONS.get((value or "").strip().lower(), DEFAULT_TITLE_POSITION)


def is_hex_color(value: str) -> bool:
    """Return True for ``#rgb``, ``#rrggbb`` and ``#rrggbbaa`` colors."""
    return bool(_HEX_COLOR_RE.fullmatch(value))


def fetch_image_as_base64(url: str, fallback_url: Optional[str] = None) -> Optional[str]:
    """
    Fetch a thumbnail and return it as a base64 data URI.

    Tries ``url`` first; if that fails (e.g. maxresdefault is missing for the
    video), tries ``fallback_url``. Embedding is required so the image renders
    inside GitHub READMEs, which block external images in SVG.
    """
    for target in filter(None, [url, fallback_url]):
        cached = _thumbnail_cache.get(target)
        if cached is not None:
            return cached
        if _missing_cache.get(target):
            continue

        try:
            data, mime_type = fetch_bytes(
                target,
                timeout=THUMBNAIL_TIMEOUT,
                max_bytes=MAX_IMAGE_BYTES,
                allowed_domains=THUMBNAIL_DOMAINS,
            )
        except urllib.error.HTTPError as exc:
            # A 404 is permanent for this URL; other failures may be transient, so do not cache them.
            if exc.code == 404:
                _missing_cache.set(target, True)
            log.info("Thumbnail HTTP %s for %s", exc.code, target)
            continue
        except Exception as exc:  # noqa: BLE001 - any upstream failure means "try the next URL"
            log.info("Thumbnail fetch failed for %s: %s", target, exc)
            continue

        if len(data) < MIN_IMAGE_BYTES or mime_type not in ALLOWED_IMAGE_TYPES:
            # Likely a placeholder or a non-image response; remember it and try the next URL.
            _missing_cache.set(target, True)
            continue

        encoded = base64.b64encode(data).decode("ascii")
        data_uri = f"data:{mime_type};base64,{encoded}"
        _thumbnail_cache.set(target, data_uri)
        return data_uri
    return None


def _wrap(title: str, max_chars: int, max_lines: int = 2) -> list[str]:
    lines = textwrap.wrap(title, width=max(16, max_chars))
    return lines[:max_lines]


def _clean_text(text: str) -> str:
    """Drop characters that would make the SVG invalid XML."""
    return _INVALID_XML_CHARS_RE.sub("", text or "")


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
    title_plate_opacity: float = 0.78,
    title_plate_color: str = "#0f1117",
    title_position: str = "overlay_bottom",
    border_radius: int = 10,
    border_width: int = 1,
    border_color: str = "rgba(255,255,255,0.07)",
    embed_thumbnail: bool = True,
) -> str:
    """
    SVG card: real thumbnail with a title plate.
    Supported title positions: outside_top, overlay_top, overlay_bottom, outside_bottom.
    Thumbnail can be embedded as base64 for GitHub compatibility.

    All text and attribute values are escaped before being placed in the markup.
    """
    title = _clean_text(title)
    position = normalize_title_position(title_position)

    thumb_height = int(width * 9 / 16)

    # Embed as base64 so GitHub can render it (GitHub blocks external <image> sources in SVG).
    thumb_src = thumbnail_url  # direct URL: works on websites, not on GitHub
    if embed_thumbnail:
        embedded = fetch_image_as_base64(thumbnail_url, thumbnail_fallback)
        if embedded:
            thumb_src = embedded
        elif thumbnail_fallback:
            thumb_src = thumbnail_fallback
    thumb_src = _esc(thumb_src or "")

    # Title sizing
    title_lines = _wrap(title, max_chars=max(18, int(width / 8.0)), max_lines=2)
    line_h = 20
    pad_top = 11
    pad_bot = 11
    text_h = pad_top + len(title_lines) * line_h + pad_bot

    r = border_radius
    is_outside = position in {"outside_top", "outside_bottom"}

    card_h = thumb_height + (text_h if is_outside else 0)
    thumb_y = text_h if position == "outside_top" else 0

    if position == "overlay_top":
        plate_y = 0
    elif position == "overlay_bottom":
        plate_y = thumb_y + thumb_height - text_h
    elif position == "outside_top":
        plate_y = 0
    else:
        plate_y = thumb_height

    # Clip path: fully rounded card
    thumb_clip = (
        f'<clipPath id="tc">'
        f'<rect x="0" y="0" width="{width}" height="{card_h}" rx="{r}"/>'
        f'</clipPath>'
    )

    # Title lines
    title_svg = ""
    for i, line in enumerate(title_lines):
        y = plate_y + pad_top + (i + 1) * line_h - 3
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
         x="0" y="{thumb_y}" width="{width}" height="{thumb_height}"
         preserveAspectRatio="xMidYMid slice"
         clip-path="url(#tc)"/>

  <!-- Title plate -->
  <rect x="0" y="{plate_y}" width="{width}" height="{text_h}"
        fill="{_esc(title_plate_color)}" fill-opacity="{title_plate_opacity:.2f}"
        clip-path="url(#tc)"/>

  <!-- Title -->
  {title_svg}

  <!-- Border -->
  <rect width="{width}" height="{card_h}" rx="{r}" fill="none"
        stroke="{_esc(border_color)}" stroke-width="{border_width}"/>
</svg>"""
