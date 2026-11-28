"""Shared evidence URL validation (no network access)."""
from urllib.parse import urlparse

def is_https_url(value) -> bool:
    if not isinstance(value, str) or value != value.strip():
        return False
    try:
        parsed = urlparse(value)
        return parsed.scheme == "https" and bool(parsed.hostname)
    except ValueError:
        return False
