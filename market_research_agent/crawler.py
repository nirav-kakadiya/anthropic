"""
Fetcher/Crawler module - Handles sitemap parsing, robots.txt, and page crawling.
"""

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse
import json


@dataclass
class RobotsRules:
    """Parsed robots.txt rules."""
    allowed_paths: list[str] = field(default_factory=list)
    disallowed_paths: list[str] = field(default_factory=list)
    sitemaps: list[str] = field(default_factory=list)
    crawl_delay: float = 0.0


@dataclass
class CrawledPage:
    """Result of crawling a single page."""
    url: str
    status: int = 200
    html: str = ""
    headers: dict = field(default_factory=dict)
    error: str = ""
    load_time: float = 0.0


class Crawler:
    """
    Website crawler that respects robots.txt and rate limits.

    Usage:
        crawler = Crawler(base_url="https://example.com", max_depth=2)
        pages = crawler.crawl()
    """

    # Key pages to prioritize
    PRIORITY_PATHS = [
        "/",
        "/pricing",
        "/features",
        "/docs",
        "/blog",
        "/changelog",
        "/about",
        "/careers",
        "/api",
        "/integrations",
        "/customers",
        "/case-studies",
        "/security",
        "/enterprise",
        "/contact",
        "/demo",
        "/signup",
        "/login",
    ]

    def __init__(
        self,
        base_url: str,
        max_depth: int = 2,
        max_pages: int = 50,
        rate_limit: float = 1.0,
        timeout: int = 30,
        respect_robots: bool = True
    ):
        self.base_url = base_url.rstrip("/")
        self.base_domain = urlparse(base_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.respect_robots = respect_robots

        self.visited: set[str] = set()
        self.robots_rules: Optional[RobotsRules] = None
        self.pages: list[CrawledPage] = []

    def normalize_url(self, url: str) -> str:
        """Normalize URL to prevent duplicates."""
        parsed = urlparse(url)
        # Remove fragments
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        # Remove trailing slash except for root
        if normalized != self.base_url and normalized.endswith("/"):
            normalized = normalized.rstrip("/")
        return normalized

    def is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to same domain."""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc == ""

    def is_allowed(self, path: str) -> bool:
        """Check if path is allowed by robots.txt."""
        if not self.respect_robots or not self.robots_rules:
            return True

        for disallowed in self.robots_rules.disallowed_paths:
            if path.startswith(disallowed):
                return False
        return True

    def parse_robots_txt(self, content: str) -> RobotsRules:
        """Parse robots.txt content into rules."""
        rules = RobotsRules()
        current_agent = None

        for line in content.split("\n"):
            line = line.strip().lower()

            if line.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                current_agent = agent
            elif current_agent in ("*", "claudebot", "anthropic"):
                if line.startswith("allow:"):
                    path = line.split(":", 1)[1].strip()
                    rules.allowed_paths.append(path)
                elif line.startswith("disallow:"):
                    path = line.split(":", 1)[1].strip()
                    if path:
                        rules.disallowed_paths.append(path)
                elif line.startswith("crawl-delay:"):
                    try:
                        rules.crawl_delay = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass

            if line.startswith("sitemap:"):
                sitemap = line.split(":", 1)[1].strip()
                # Handle case where sitemap: http://... splits incorrectly
                if not sitemap.startswith("http"):
                    sitemap = "http" + sitemap
                rules.sitemaps.append(sitemap)

        return rules

    def parse_sitemap(self, content: str) -> list[str]:
        """Parse sitemap.xml and extract URLs."""
        urls = []

        try:
            # Remove namespaces for easier parsing
            content = re.sub(r'\sxmlns[^"]+\"[^\"]+\"', '', content)
            root = ET.fromstring(content)

            # Handle sitemap index
            for sitemap in root.findall(".//sitemap"):
                loc = sitemap.find("loc")
                if loc is not None and loc.text:
                    urls.append(loc.text.strip())

            # Handle regular sitemap URLs
            for url in root.findall(".//url"):
                loc = url.find("loc")
                if loc is not None and loc.text:
                    urls.append(loc.text.strip())

        except ET.ParseError:
            # Try simple regex extraction as fallback
            urls = re.findall(r'<loc>([^<]+)</loc>', content)

        return urls

    def extract_links(self, html: str, base_url: str) -> list[str]:
        """Extract all links from HTML content."""
        links = []

        # Find all href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        matches = re.findall(href_pattern, html, re.IGNORECASE)

        for href in matches:
            # Skip non-page links
            if any(href.startswith(p) for p in ["#", "javascript:", "mailto:", "tel:"]):
                continue

            # Skip static assets
            if any(href.endswith(ext) for ext in [".css", ".js", ".png", ".jpg", ".gif", ".svg", ".pdf", ".zip"]):
                continue

            # Convert relative to absolute URLs
            absolute_url = urljoin(base_url, href)

            # Only include same-domain links
            if self.is_same_domain(absolute_url):
                normalized = self.normalize_url(absolute_url)
                if normalized not in links:
                    links.append(normalized)

        return links

    def fetch_page(self, url: str) -> CrawledPage:
        """
        Fetch a single page. Returns CrawledPage with content or error.

        Note: This is a stub that should be called with actual HTTP client.
        In production, use requests or aiohttp.
        """
        # This is a placeholder - actual fetching happens via HTTP client
        return CrawledPage(
            url=url,
            status=0,
            html="",
            error="fetch_page must be implemented with HTTP client"
        )

    def get_priority_urls(self) -> list[str]:
        """Get list of priority URLs to crawl first."""
        urls = []
        for path in self.PRIORITY_PATHS:
            url = self.base_url + path
            if self.is_allowed(path):
                urls.append(url)
        return urls

    def get_crawl_plan(self) -> dict:
        """
        Generate a crawl plan without actually fetching.
        Useful for showing what will be crawled.
        """
        return {
            "base_url": self.base_url,
            "priority_urls": self.get_priority_urls(),
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
            "rate_limit_seconds": self.rate_limit,
            "urls_to_check": [
                f"{self.base_url}/robots.txt",
                f"{self.base_url}/sitemap.xml",
            ]
        }


class CrawlResult:
    """
    Aggregated crawl results with helper methods.
    """

    def __init__(self):
        self.robots_rules: Optional[RobotsRules] = None
        self.sitemap_urls: list[str] = []
        self.pages: list[CrawledPage] = []
        self.errors: list[str] = []

    def add_page(self, page: CrawledPage):
        """Add a crawled page to results."""
        self.pages.append(page)
        if page.error:
            self.errors.append(f"{page.url}: {page.error}")

    def get_successful_pages(self) -> list[CrawledPage]:
        """Get only successfully crawled pages."""
        return [p for p in self.pages if p.status == 200 and not p.error]

    def get_all_html(self) -> str:
        """Concatenate all successful page HTML."""
        return "\n".join(p.html for p in self.get_successful_pages())

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "robots_rules": {
                "allowed": self.robots_rules.allowed_paths if self.robots_rules else [],
                "disallowed": self.robots_rules.disallowed_paths if self.robots_rules else [],
                "sitemaps": self.robots_rules.sitemaps if self.robots_rules else [],
            },
            "sitemap_urls_count": len(self.sitemap_urls),
            "pages_crawled": len(self.pages),
            "successful_pages": len(self.get_successful_pages()),
            "errors": self.errors[:10],  # First 10 errors
        }


def create_crawler(
    url: str,
    max_depth: int = 2,
    max_pages: int = 50
) -> Crawler:
    """Factory function to create a configured crawler."""
    return Crawler(
        base_url=url,
        max_depth=max_depth,
        max_pages=max_pages,
        rate_limit=1.0,
        respect_robots=True
    )
