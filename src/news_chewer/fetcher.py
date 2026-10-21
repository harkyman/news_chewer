import httpx
from googlenewsdecoder import gnewsdecoder
from curl_cffi import requests as curl_requests
from googlenewsdecoder import gnewsdecoder


def fetch_url(url: str, timeout: int = 15) -> str:
    """Fetch a URL and return the raw HTML text.

    Raises httpx.HTTPError on non-2xx responses or transport errors.
    """
    resp = httpx.get(url, timeout=timeout, follow_redirects=True)
    resp.raise_for_status()
    return resp.text

def fetch_news_url(google_rss_url: str, timeout: int = 15) -> tuple[str, str]:
    """Decodes Google News URLs and fetches content using browser TLS impersonation."""
    # 1. Decode Google News URL to target publisher URL
    res = gnewsdecoder(google_rss_url)
    if not res.get("status"):
        return "Failed to fetch URL: Could not decode Google News URL", None
    
    final_url = res["decoded_url"]

    # 2. Fetch using Chrome TLS fingerprinting
    try:
        resp = curl_requests.get(
            final_url,
            impersonate="chrome120",
            allow_redirects=True,
            timeout=timeout
        )
        resp.raise_for_status()
        return resp.text, final_url
    except Exception as e:
        status = getattr(e.response, "status_code", "N/A") if hasattr(e, "response") and e.response else "N/A"
        return f"Failed to fetch URL: {final_url} with status code {status}", None