import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx


def has_path_after_host(url: str) -> bool:
    """Returns True if the URL has material after the host/domain."""
    parsed = urlparse(url)
    has_path = bool(parsed.path.strip("/ "))
    has_query_or_fragment = bool(parsed.query or parsed.fragment)
    return has_path or has_query_or_fragment


def extract_drudge_tt_urls(url: str = "https://www.drudgereport.com") -> list[str]:
    # 1. Fetch HTML using httpx
    with httpx.Client(headers={"User-Agent": "Mozilla/5.0"}) as client:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        html_content = response.text

    # 2. Cut off everything after the target comment (handling non-breaking spaces \xa0)
    # Matches 'LINK S', any whitespace/nbsp, 'A N D', etc.
    comment_pattern = re.compile(
        r"<!--\sLINK\s*S\s*A\s*N\s*D\s*SEARCHES\s*3\s*R\s*D\s*C\s*O\s*LUM\s*N\s*-->",
        re.IGNORECASE,
    )

    match = comment_pattern.search(html_content)
    if match:
        # Keep only the HTML up to the start of the comment
        html_content = html_content[: match.start()]

    # 3. Parse the truncated HTML
    soup = BeautifulSoup(html_content, "html.parser")
    urls = []

    # 4. Find tables outside iframes
    for table in soup.find_all("table"):
        if table.find_parent("iframe") is not None:
            continue

        # 5. Find <a> tags inside <tt> elements
        for tt in table.find_all("tt"):
            for a_tag in tt.find_all("a", href=True):
                href = a_tag["href"]

                # 6. Filter out top-level domain URLs
                if has_path_after_host(href):
                    urls.append(href)

    return urls