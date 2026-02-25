import re
import urllib.parse
import urllib.request
import json
from typing import Optional

from flask import Flask, Response, redirect, request

from .card import generate_svg

app = Flask(__name__)


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract YouTube video ID from URL or return as-is if already an ID"""
    url_or_id = url_or_id.strip()

    # Already a plain video ID (11 chars, alphanumeric + - _)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id

    # Various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def fetch_video_info(video_id: str, api_key: Optional[str] = None) -> dict:
    """Fetch video title and channel from YouTube oEmbed (no API key needed)"""
    try:
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            return {
                "title": data.get("title", ""),
                "channel": data.get("author_name", ""),
                "views": None,
                "duration": None,
            }
    except Exception:
        return {"title": "", "channel": "", "views": None, "duration": None}


@app.route("/")
def index():
    """Serve the main page"""
    return redirect("/index.html")


@app.route("/badge")
def badge():
    """
    Generate an SVG badge for a YouTube video.

    Query params:
      - url or id: YouTube URL or video ID (required)
      - width: card width in pixels (default: 320)
      - bg: background color hex (default: 0d1117)
      - title_color: title text color (default: ffffff)
      - stats_color: stats text color (default: adbac7)
      - radius: border radius (default: 8)
      - embed: whether to embed thumbnail as base64 (default: true)
    """
    url_param = request.args.get("url") or request.args.get("id", "")
    if not url_param:
        return Response("Missing 'url' or 'id' parameter", status=400)

    video_id = extract_video_id(url_param)
    if not video_id:
        return Response("Could not extract video ID from the provided URL", status=400)

    width = min(max(int(request.args.get("width", 320)), 200), 600)
    bg = "#" + request.args.get("bg", "0d1117").lstrip("#")
    title_color = "#" + request.args.get("title_color", "ffffff").lstrip("#")
    stats_color = "#" + request.args.get("stats_color", "adbac7").lstrip("#")
    radius = min(max(int(request.args.get("radius", 8)), 0), 30)
    embed = request.args.get("embed", "true").lower() != "false"

    info = fetch_video_info(video_id)

    svg = generate_svg(
        video_id=video_id,
        title=info["title"],
        channel=info["channel"],
        views=info["views"],
        duration_seconds=info["duration"],
        width=width,
        background_color=bg,
        title_color=title_color,
        stats_color=stats_color,
        border_radius=radius,
        embed_thumbnail=embed,
    )

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.route("/info")
def info():
    """Return video info as JSON"""
    url_param = request.args.get("url") or request.args.get("id", "")
    if not url_param:
        return Response("Missing 'url' or 'id' parameter", status=400)

    video_id = extract_video_id(url_param)
    if not video_id:
        return Response("Could not extract video ID", status=400)

    video_info = fetch_video_info(video_id)
    video_info["id"] = video_id
    video_info["thumbnail"] = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
    video_info["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}"

    return Response(
        json.dumps(video_info),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
