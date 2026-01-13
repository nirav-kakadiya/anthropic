"""
Site Analyzer - Automatically crawl and analyze a website.

Fetches:
- robots.txt for sitemap locations
- sitemap.xml for all pages
- Key pages (home, features, pricing, about, products)

Extracts site structure and content for feature/niche detection.
"""

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import re
import xml.etree.ElementTree as ET
from typing import Optional


@dataclass
class SitemapEntry:
    """Single URL from sitemap."""
    url: str
    lastmod: Optional[str] = None
    priority: Optional[float] = None
    changefreq: Optional[str] = None


@dataclass
class SiteStructure:
    """Analyzed site structure."""
    base_url: str
    domain: str

    # Discovered pages
    sitemap_urls: list[SitemapEntry] = field(default_factory=list)
    key_pages: dict[str, str] = field(default_factory=dict)  # type -> url

    # Content
    homepage_content: str = ""
    features_content: str = ""
    pricing_content: str = ""
    about_content: str = ""

    # Extracted info
    site_title: str = ""
    site_description: str = ""
    detected_products: list[str] = field(default_factory=list)


class SiteAnalyzer:
    """
    Analyze a website to extract structure, features, and niche.

    Usage:
        analyzer = SiteAnalyzer("https://example.com")

        # Get URLs to fetch
        urls = analyzer.get_urls_to_fetch()

        # After fetching, process responses
        analyzer.process_robots_txt(content)
        analyzer.process_sitemap(xml_content)
        analyzer.process_page("home", html_content)

        # Get site structure
        structure = analyzer.get_structure()
    """

    # Common page patterns to look for
    KEY_PAGE_PATTERNS = {
        "features": [
            r"/features",
            r"/product",
            r"/solutions",
            r"/capabilities",
            r"/what-we-do",
            r"/tools",
        ],
        "pricing": [
            r"/pricing",
            r"/plans",
            r"/subscribe",
            r"/upgrade",
            r"/pro",
        ],
        "about": [
            r"/about",
            r"/company",
            r"/team",
            r"/who-we-are",
        ],
        "docs": [
            r"/docs",
            r"/documentation",
            r"/help",
            r"/guide",
            r"/api",
        ],
        "blog": [
            r"/blog",
            r"/news",
            r"/updates",
            r"/changelog",
        ],
        "integrations": [
            r"/integrations",
            r"/apps",
            r"/marketplace",
            r"/plugins",
            r"/extensions",
        ],
    }

    def __init__(self, url: str):
        """Initialize with target URL."""
        parsed = urlparse(url)
        self.base_url = f"{parsed.scheme}://{parsed.netloc}"
        self.domain = parsed.netloc.replace("www.", "")

        self.structure = SiteStructure(
            base_url=self.base_url,
            domain=self.domain
        )

        self._sitemap_locations: list[str] = []

    def get_urls_to_fetch(self) -> dict:
        """
        Get all URLs that should be fetched for analysis.

        Returns dict with categorized URLs.
        """
        urls = {
            "robots_txt": f"{self.base_url}/robots.txt",
            "sitemap": f"{self.base_url}/sitemap.xml",
            "homepage": self.base_url,
            "key_pages": {
                "features": f"{self.base_url}/features",
                "pricing": f"{self.base_url}/pricing",
                "about": f"{self.base_url}/about",
            },
            "additional_sitemaps": [],  # Populated after robots.txt
        }
        return urls

    def parse_robots_txt(self, content: str) -> list[str]:
        """
        Parse robots.txt to find sitemap locations.

        Returns list of sitemap URLs found.
        """
        sitemaps = []

        for line in content.split("\n"):
            line = line.strip().lower()
            if line.startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                # Handle case sensitivity in actual URL
                for orig_line in content.split("\n"):
                    if orig_line.strip().lower() == f"sitemap: {sitemap_url}" or \
                       orig_line.strip().lower().startswith("sitemap:"):
                        parts = orig_line.split(":", 1)
                        if len(parts) > 1:
                            sitemaps.append(parts[1].strip())
                            break

        # Deduplicate
        self._sitemap_locations = list(set(sitemaps))
        return self._sitemap_locations

    def parse_sitemap_xml(self, xml_content: str) -> list[SitemapEntry]:
        """
        Parse sitemap.xml content.

        Handles both sitemap index and regular sitemaps.
        """
        entries = []

        try:
            # Remove namespace for easier parsing
            xml_content = re.sub(r'\sxmlns="[^"]+"', '', xml_content)
            root = ET.fromstring(xml_content)

            # Check if this is a sitemap index
            if root.tag == "sitemapindex" or root.find(".//sitemap") is not None:
                # Sitemap index - extract sitemap locations
                for sitemap in root.findall(".//sitemap"):
                    loc = sitemap.find("loc")
                    if loc is not None and loc.text:
                        self._sitemap_locations.append(loc.text)
            else:
                # Regular sitemap - extract URLs
                for url_elem in root.findall(".//url"):
                    loc = url_elem.find("loc")
                    if loc is not None and loc.text:
                        entry = SitemapEntry(url=loc.text)

                        lastmod = url_elem.find("lastmod")
                        if lastmod is not None:
                            entry.lastmod = lastmod.text

                        priority = url_elem.find("priority")
                        if priority is not None:
                            try:
                                entry.priority = float(priority.text)
                            except ValueError:
                                pass

                        changefreq = url_elem.find("changefreq")
                        if changefreq is not None:
                            entry.changefreq = changefreq.text

                        entries.append(entry)

        except ET.ParseError:
            # Invalid XML, try basic regex extraction
            urls = re.findall(r'<loc>([^<]+)</loc>', xml_content)
            entries = [SitemapEntry(url=url) for url in urls]

        self.structure.sitemap_urls = entries

        # Identify key pages from sitemap
        self._identify_key_pages(entries)

        return entries

    def _identify_key_pages(self, entries: list[SitemapEntry]):
        """Identify key pages from sitemap URLs."""
        for entry in entries:
            url_path = urlparse(entry.url).path.lower()

            for page_type, patterns in self.KEY_PAGE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, url_path):
                        # Prefer shorter/simpler URLs
                        current = self.structure.key_pages.get(page_type)
                        if current is None or len(entry.url) < len(current):
                            self.structure.key_pages[page_type] = entry.url
                        break

    def process_page_html(self, page_type: str, html: str):
        """
        Process HTML content from a page.

        Args:
            page_type: "home", "features", "pricing", "about", etc.
            html: Raw HTML content
        """
        # Extract text content
        text = self._html_to_text(html)

        if page_type == "home":
            self.structure.homepage_content = text
            self._extract_site_meta(html)
        elif page_type == "features":
            self.structure.features_content = text
        elif page_type == "pricing":
            self.structure.pricing_content = text
        elif page_type == "about":
            self.structure.about_content = text

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        # Remove script and style
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Decode entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')

        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _extract_site_meta(self, html: str):
        """Extract site title and description from HTML."""
        # Title
        title_match = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            self.structure.site_title = title_match.group(1).strip()

        # Meta description
        desc_match = re.search(
            r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not desc_match:
            desc_match = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']',
                html, re.IGNORECASE
            )
        if desc_match:
            self.structure.site_description = desc_match.group(1).strip()

    def get_structure(self) -> SiteStructure:
        """Get the analyzed site structure."""
        return self.structure

    def get_additional_sitemaps(self) -> list[str]:
        """Get additional sitemap URLs discovered."""
        return self._sitemap_locations

    def get_pages_to_fetch(self) -> list[dict]:
        """
        Get prioritized list of pages to fetch for feature extraction.

        Returns list of {url, type, priority} dicts.
        """
        pages = []

        # Always fetch homepage
        pages.append({
            "url": self.base_url,
            "type": "home",
            "priority": 1.0
        })

        # Key pages from sitemap or defaults
        for page_type in ["features", "pricing", "about", "docs", "integrations"]:
            url = self.structure.key_pages.get(page_type)
            if url:
                pages.append({
                    "url": url,
                    "type": page_type,
                    "priority": 0.9 if page_type == "features" else 0.7
                })
            else:
                # Try default URL
                pages.append({
                    "url": f"{self.base_url}/{page_type}",
                    "type": page_type,
                    "priority": 0.5
                })

        # High-priority sitemap URLs
        for entry in self.structure.sitemap_urls:
            if entry.priority and entry.priority >= 0.8:
                if entry.url not in [p["url"] for p in pages]:
                    pages.append({
                        "url": entry.url,
                        "type": "high_priority",
                        "priority": entry.priority
                    })

        return sorted(pages, key=lambda x: x["priority"], reverse=True)[:20]


def create_site_analyzer(url: str) -> SiteAnalyzer:
    """Factory function to create a SiteAnalyzer."""
    return SiteAnalyzer(url)
