from urllib.parse import urlparse, urlunparse


def normalize_url(url):
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    netloc = parsed.netloc or parsed.path
    if not netloc:
        return None
    normalized = urlunparse((scheme, netloc, "", "", "", ""))
    return normalized
