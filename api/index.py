import json
import re
import urllib.request
from typing import Optional

from flask import Flask, Response, request, send_file
import os

from .card import generate_svg

app = Flask(__name__)


def extract_video_id(url_or_id: str) -> Optional[str]:
    url_or_id = url_or_id.strip()
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
        return url_or_id
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def fetch_video_info(video_id: str) -> dict:
    """Fetch title + real thumbnail URL from YouTube oEmbed — no API key required"""
    try:
        oembed_url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )
        req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read())
            # oEmbed gives us thumbnail_url — this is the real per-video preview image.
            # It's usually hqdefault (480×360). We also try maxresdefault (1280×720) first.
            oembed_thumb = data.get("thumbnail_url", "")
            # Upgrade to maxresdefault if possible (same host, just swap the filename)
            if oembed_thumb:
                maxres = oembed_thumb.rsplit("/", 1)[0] + "/maxresdefault.jpg"
            else:
                maxres = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            hq = oembed_thumb or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            return {
                "title": data.get("title", ""),
                "channel": data.get("author_name", ""),
                # maxres first, hq as fallback (server will try maxres, fall back to hq)
                "thumbnail_url": maxres,
                "thumbnail_fallback": hq,
            }
    except Exception:
        fallback = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        return {
            "title": "",
            "channel": "",
            "thumbnail_url": fallback,
            "thumbnail_fallback": fallback,
        }


@app.route("/")
def index():
    html_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    return send_file(os.path.abspath(html_path))


@app.route("/badge")
def badge():
    """
    GET /badge?url=<youtube_url>
    GET /badge?id=<video_id>
    Optional: width, radius, bg, title_color, title_opacity, border_width, border_color, embed
    """
    url_param = request.args.get("url") or request.args.get("id", "")
    if not url_param:
        return Response("Missing 'url' or 'id' parameter", status=400)

    video_id = extract_video_id(url_param)
    if not video_id:
        return Response("Could not extract YouTube video ID from provided input", status=400)

    width = min(max(int(request.args.get("width", 320)), 200), 600)
    radius = min(max(int(request.args.get("radius", 10)), 0), 30)
    bg = "#" + request.args.get("bg", "0f1117").lstrip("#")
    title_color = "#" + request.args.get("title_color", "ffffff").lstrip("#")
    title_opacity = min(max(float(request.args.get("title_opacity", 1)), 0), 1)
    border_width = min(max(int(request.args.get("border_width", 1)), 0), 10)
    border_color = "#" + request.args.get("border_color", "ffffff").lstrip("#")
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
        border_radius=radius,
        border_width=border_width,
        border_color=border_color,
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
    """GET /info?url=<youtube_url> — returns JSON with video metadata"""
    url_param = request.args.get("url") or request.args.get("id", "")
    if not url_param:
        return Response("Missing 'url' or 'id' parameter", status=400)

    video_id = extract_video_id(url_param)
    if not video_id:
        return Response("Could not extract video ID", status=400)

    video_info = fetch_video_info(video_id)
    video_info["id"] = video_id
    video_info["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}"

    return Response(
        json.dumps(video_info),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
