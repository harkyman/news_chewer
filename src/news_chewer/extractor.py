from typing import Optional


def extract_text(html: str, url: Optional[str] = None) -> str:
    """Try to extract visible article text from HTML.

    Prefers `trafilatura` if available, falls back to BeautifulSoup text extraction.
    """
    try:
        import trafilatura

        result = trafilatura.extract(html, url=url)
        if result:
            return result.strip()
    except Exception:
        pass

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def extract_urls_from_rss(rss_xml: str) -> list[tuple[str, str, str, str]]:
    """Extract article titles, URLs, publication date and source from an RSS feed XML string."""
    from xml.etree import ElementTree as ET

    root = ET.fromstring(rss_xml)
    articles = []
    
    for item in root.findall(".//item"):
        title = item.find("title")
        link = item.find("link")
        pubDate = item.find("pubDate")
        source = item.find("source")
        
        if title is not None and title.text and link is not None and link.text:
            articles.append((title.text.strip(), link.text.strip(), pubDate.text.strip(), source.text.strip()))
            
    return articles
