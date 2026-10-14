"""Hardened outbound HTTP helpers and a small bounded in-process cache.

Every outbound request made by the API goes through :func:`fetch_bytes`, which:

* only talks to an explicit allow-list of HTTPS hosts (SSRF defence, including
  redirects);
* caps the response size so a hostile or broken upstream cannot exhaust memory;
* applies a hard timeout.
"""

import threading
import time
import urllib.request
from collections import OrderedDict
from typing import Hashable, Optional, Sequence, Tuple
from urllib.parse import urlsplit

USER_AGENT = "Mozilla/5.0 (compatible; ytbadge/1.0)"


class FetchError(Exception):
    """Raised when an outbound fetch is refused or fails."""


class TTLCache:
    """Thread-safe LRU cache whose entries expire after ``ttl`` seconds."""

    def __init__(self, maxsize: int, ttl: float) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._data: "OrderedDict[Hashable, Tuple[float, object]]" = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: Hashable):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < time.monotonic():
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: Hashable, value: object) -> None:
        with self._lock:
            self._data[key] = (time.monotonic() + self._ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)


def host_allowed(url: str, allowed_domains: Sequence[str]) -> bool:
    """Return True when ``url`` is HTTPS and its host equals or is under an allowed domain."""
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname:
        return False
    host = parts.hostname.lower()
    return any(host == domain or host.endswith("." + domain) for domain in allowed_domains)


class _AllowListRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Refuse redirects that would leave the allow-listed domains."""

    def __init__(self, allowed_domains: Sequence[str]) -> None:
        self._allowed_domains = tuple(allowed_domains)

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        if not host_allowed(newurl, self._allowed_domains):
            raise FetchError("Redirect to a host outside the allow-list was blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bytes(
    url: str,
    *,
    timeout: float,
    max_bytes: int,
    allowed_domains: Sequence[str],
) -> Tuple[bytes, str]:
    """Download ``url`` and return ``(body, mime_type)``.

    Raises :class:`FetchError` (or an ``OSError``/``urllib`` error) on failure.
    """
    if not host_allowed(url, allowed_domains):
        raise FetchError("Requested host is not allow-listed")

    opener = urllib.request.build_opener(_AllowListRedirectHandler(allowed_domains))
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    with opener.open(request, timeout=timeout) as response:
        declared_length = response.headers.get("Content-Length")
        if declared_length and declared_length.isdigit() and int(declared_length) > max_bytes:
            raise FetchError("Response is larger than the allowed size")

        # Read one byte past the limit so an oversized body is detected without
        # buffering it entirely.
        body = response.read(max_bytes + 1)
        if len(body) > max_bytes:
            raise FetchError("Response is larger than the allowed size")

        content_type: Optional[str] = response.headers.get("Content-Type") or ""
        mime_type = content_type.split(";", 1)[0].strip().lower()
        return body, mime_type
