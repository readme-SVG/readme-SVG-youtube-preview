import json
import logging
import math
import os
import re
from typing import Optional, Tuple
from urllib.parse import urlencode

from flask import Flask, Response, request, send_from_directory

from .card import (
    THUMBNAIL_DOMAINS,
    generate_svg,
    is_hex_color,
    normalize_title_position,
)
from .net import TTLCache, fetch_bytes, host_allowed

log = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Upper bound for the raw query value; anything longer is not a valid YouTube URL.
MAX_INPUT_LENGTH = 2048
# oEmbed responses are a few hundred bytes; anything much bigger is not oEmbed.
MAX_OEMBED_BYTES = 64 * 1024
OEMBED_TIMEOUT = 6
OEMBED_DOMAINS = ("youtube.com",)

# Metadata for a video rarely changes; caching it avoids a YouTube round trip
# for every /badge request served by a warm instance.
_info_cache = TTLCache(maxsize=512, ttl=3600)

# Responses that are identical for identical query strings can be cached by clients and CDNs.
CACHE_CONTROL = "public, max-age=3600"

_VIDEO_ID_RE = re.compile(r"[a-zA-Z0-9_-]{11}")
_URL_PATTERNS = [
    re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})"),
]

# Content-Security-Policy for the generator page. Inline <style> attributes are
# still used by the markup, hence 'unsafe-inline' for styles only; scripts are
# restricted to same-origin files.
HTML_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https:; "
    "connect-src 'self'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)
# SVG cards never need scripts or sub-resources other than images.
SVG_CSP = "default-src 'none'; style-src 'unsafe-inline'; img-src data: https:"

app = Flask(__name__)


@app.after_request
def add_security_headers(response: Response) -> Response:
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if response.mimetype == "text/html":
        response.headers.setdefault("Content-Security-Policy", HTML_CSP)
        response.headers.setdefault("X-Frame-Options", "DENY")
    elif response.mimetype == "image/svg+xml":
        response.headers.setdefault("Content-Security-Policy", SVG_CSP)
    return response


def extract_video_id(url_or_id: str) -> Optional[str]:
    url_or_id = url_or_id.strip()
    if _VIDEO_ID_RE.fullmatch(url_or_id):
        return url_or_id
    for pattern in _URL_PATTERNS:
        match = pattern.search(url_or_id)
        if match:
            return match.group(1)
    return None


def fetch_video_info(video_id: str) -> dict:
    """Fetch title + real thumbnail URL from YouTube oEmbed (no API key required)."""
    cached = _info_cache.get(video_id)
    if cached is not None:
        return dict(cached)

    hq_fallback = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    oembed_url = "https://www.youtube.com/oembed?" + urlencode({
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "format": "json",
    })
    try:
        body, _ = fetch_bytes(
            oembed_url,
            timeout=OEMBED_TIMEOUT,
            max_bytes=MAX_OEMBED_BYTES,
            allowed_domains=OEMBED_DOMAINS,
        )
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("oEmbed payload is not a JSON object")
    except Exception as exc:  # noqa: BLE001 - metadata is optional; degrade gracefully
        log.warning("oEmbed lookup failed for %s: %s", video_id, exc)
        return {
            "title": "",
            "channel": "",
            "thumbnail_url": hq_fallback,
            "thumbnail_fallback": hq_fallback,
        }

    # oEmbed gives us thumbnail_url, the real per-video preview image, usually hqdefault (480x360).
    # Only trust it when it points at YouTube's image CDN.
    oembed_thumb = data.get("thumbnail_url") or ""
    if not isinstance(oembed_thumb, str) or not host_allowed(oembed_thumb, THUMBNAIL_DOMAINS):
        oembed_thumb = ""

    # Prefer maxresdefault (1280x720) by swapping the filename on the same host; the
    # downloader falls back to the hq variant if it is missing.
    if oembed_thumb:
        maxres = oembed_thumb.rsplit("/", 1)[0] + "/maxresdefault.jpg"
    else:
        maxres = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
    hq = oembed_thumb or hq_fallback

    info = {
        "title": str(data.get("title") or ""),
        "channel": str(data.get("author_name") or ""),
        "thumbnail_url": maxres,
        "thumbnail_fallback": hq,
    }
    _info_cache.set(video_id, dict(info))
    return info


def _resolve_video_id() -> Tuple[Optional[str], Optional[Response]]:
    """Read the ``url`` or ``id`` query parameter; return (video_id, None) or (None, error)."""
    url_param = request.args.get("url") or request.args.get("id", "")
    if not url_param:
        return None, Response("Missing 'url' or 'id' parameter", status=400, mimetype="text/plain")
    if len(url_param) > MAX_INPUT_LENGTH:
        return None, Response("Input is too long", status=400, mimetype="text/plain")

    video_id = extract_video_id(url_param)
    if not video_id:
        return None, Response(
            "Could not extract YouTube video ID from provided input",
            status=400,
            mimetype="text/plain",
        )
    return video_id, None


def _int_arg(name: str, default: int, low: int, high: int) -> int:
    """Parse an integer query parameter, clamped to [low, high]; invalid input yields the default."""
    raw = request.args.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if not math.isfinite(value):
        return default
    return min(max(int(value), low), high)


def _float_arg(name: str, default: float, low: float, high: float) -> float:
    """Parse a float query parameter, clamped to [low, high]; invalid input yields the default."""
    raw = request.args.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if not math.isfinite(value):
        return default
    return min(max(value, low), high)


def _color_arg(name: str, default: str) -> str:
    """Parse a hex color query parameter (with or without '#'); invalid input yields the default."""
    raw = request.args.get(name, "").strip()
    if not raw:
        return default
    candidate = raw if raw.startswith("#") else "#" + raw
    return candidate if is_hex_color(candidate) else default


def _serve_static(filename: str, mimetype: str) -> Response:
    return send_from_directory(BASE_DIR, filename, mimetype=mimetype)


@app.route("/")
def index():
    return _serve_static("index.html", "text/html")


@app.route("/styles.css")
def styles():
    return _serve_static("styles.css", "text/css")


@app.route("/app.js")
def script():
    return _serve_static("app.js", "application/javascript")


@app.route("/badge")
def badge():
    """
    GET /badge?url=<youtube_url>
    GET /badge?id=<video_id>
    Optional: width, radius, bg, title_color, title_opacity, plate_color,
    plate_opacity, title_position, border_width, border_color, embed
    """
    video_id, error = _resolve_video_id()
    if error is not None:
        return error

    width = _int_arg("width", 320, 200, 600)
    radius = _int_arg("radius", 10, 0, 30)
    bg = _color_arg("bg", "#0f1117")
    title_color = _color_arg("title_color", "#ffffff")
    title_opacity = _float_arg("title_opacity", 1.0, 0.0, 1.0)
    plate_color = _color_arg("plate_color", "#0f1117")
    plate_opacity = _float_arg("plate_opacity", 0.78, 0.0, 1.0)
    title_position = normalize_title_position(request.args.get("title_position", "overlay_bottom"))
    border_width = _int_arg("border_width", 1, 0, 10)
    border_color = _color_arg("border_color", "#ffffff")
    embed = request.args.get("embed", "true").lower() != "false"

    info = fetch_video_info(video_id)

    svg = generate_svg(
        video_id=video_id,
        title=info["title"],
        thumbnail_url=info["thumbnail_url"],
        thumbnail_fallback=info["thumbnail_fallback"],
        width=width,
        background_color=bg,
        title_color=title_color,
        title_opacity=title_opacity,
        title_plate_opacity=plate_opacity,
        title_plate_color=plate_color,
        title_position=title_position,
        border_radius=radius,
        border_width=border_width,
        border_color=border_color,
        embed_thumbnail=embed,
    )

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": CACHE_CONTROL,
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/info")
def info():
    """GET /info?url=<youtube_url> — returns JSON with video metadata"""
    video_id, error = _resolve_video_id()
    if error is not None:
        return error

    video_info = fetch_video_info(video_id)
    video_info["id"] = video_id
    video_info["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}"

    return Response(
        json.dumps(video_info),
        mimetype="application/json",
        headers={
            "Cache-Control": CACHE_CONTROL,
            "Access-Control-Allow-Origin": "*",
        },
    )
