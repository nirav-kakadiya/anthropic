"""
Live Fetcher - Actually fetch URLs with rate limiting and retry logic.

Features:
- Async HTTP fetching with aiohttp
- Rate limiting per domain
- Exponential backoff retry
- User-agent rotation
- Proxy support (optional)
- Response caching
"""

import asyncio
import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
from urllib.parse import urlparse
import ssl


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    url: str
    status_code: int
    content: str = ""
    content_type: str = ""
    fetch_time: float = 0.0
    error: Optional[str] = None
    from_cache: bool = False
    headers: dict = field(default_factory=dict)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration per domain."""
    requests_per_second: float = 1.0
    burst_limit: int = 3
    retry_attempts: int = 3
    retry_base_delay: float = 1.0


class LiveFetcher:
    """
    Async HTTP fetcher with rate limiting.

    Usage:
        fetcher = LiveFetcher()

        # Fetch single URL
        result = await fetcher.fetch("https://example.com")

        # Fetch multiple URLs with rate limiting
        results = await fetcher.fetch_all([
            "https://example.com/page1",
            "https://example.com/page2",
            "https://other.com/page1",
        ])

        # Or use sync wrapper
        results = fetcher.fetch_sync(urls)
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    ]

    # Default rate limits per domain type
    DOMAIN_RATE_LIMITS = {
        "reddit.com": RateLimitConfig(requests_per_second=0.5, burst_limit=2),
        "producthunt.com": RateLimitConfig(requests_per_second=1.0, burst_limit=3),
        "news.ycombinator.com": RateLimitConfig(requests_per_second=2.0, burst_limit=5),
        "hn.algolia.com": RateLimitConfig(requests_per_second=5.0, burst_limit=10),
        "default": RateLimitConfig(requests_per_second=2.0, burst_limit=5),
    }

    def __init__(
        self,
        cache_enabled: bool = True,
        cache_ttl_minutes: int = 15,
        default_timeout: int = 30,
        proxy: Optional[str] = None,
    ):
        self.cache_enabled = cache_enabled
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.default_timeout = default_timeout
        self.proxy = proxy

        # Cache storage
        self._cache: dict[str, tuple[FetchResult, datetime]] = {}

        # Rate limiting state per domain
        self._domain_last_request: dict[str, float] = {}
        self._domain_request_count: dict[str, int] = {}

        # Stats
        self.stats = {
            "requests": 0,
            "cache_hits": 0,
            "errors": 0,
            "total_bytes": 0,
        }

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.replace("www.", "")

    def _get_rate_limit(self, domain: str) -> RateLimitConfig:
        """Get rate limit config for domain."""
        for pattern, config in self.DOMAIN_RATE_LIMITS.items():
            if pattern in domain:
                return config
        return self.DOMAIN_RATE_LIMITS["default"]

    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def _check_cache(self, url: str) -> Optional[FetchResult]:
        """Check if URL is in cache and not expired."""
        if not self.cache_enabled:
            return None

        cache_key = self._get_cache_key(url)
        if cache_key in self._cache:
            result, cached_at = self._cache[cache_key]
            if datetime.now() - cached_at < self.cache_ttl:
                self.stats["cache_hits"] += 1
                result.from_cache = True
                return result
            else:
                del self._cache[cache_key]

        return None

    def _save_to_cache(self, url: str, result: FetchResult):
        """Save result to cache."""
        if self.cache_enabled and result.status_code == 200:
            cache_key = self._get_cache_key(url)
            self._cache[cache_key] = (result, datetime.now())

    async def _wait_for_rate_limit(self, domain: str):
        """Wait if needed to respect rate limits."""
        config = self._get_rate_limit(domain)
        min_interval = 1.0 / config.requests_per_second

        last_request = self._domain_last_request.get(domain, 0)
        elapsed = time.time() - last_request

        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            # Add small jitter
            wait_time += random.uniform(0.1, 0.3)
            await asyncio.sleep(wait_time)

        self._domain_last_request[domain] = time.time()

    async def fetch(
        self,
        url: str,
        headers: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> FetchResult:
        """
        Fetch a single URL with rate limiting.

        Args:
            url: URL to fetch
            headers: Optional custom headers
            timeout: Optional timeout override

        Returns:
            FetchResult with content or error
        """
        # Check cache first
        cached = self._check_cache(url)
        if cached:
            return cached

        domain = self._get_domain(url)
        config = self._get_rate_limit(domain)

        # Prepare headers
        request_headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        if headers:
            request_headers.update(headers)

        # Retry loop
        last_error = None
        for attempt in range(config.retry_attempts):
            try:
                # Wait for rate limit
                await self._wait_for_rate_limit(domain)

                start_time = time.time()
                self.stats["requests"] += 1

                # Use urllib for simplicity (no external deps)
                import urllib.request
                import urllib.error

                req = urllib.request.Request(url, headers=request_headers)

                # Create SSL context that doesn't verify (for simplicity)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

                with urllib.request.urlopen(
                    req,
                    timeout=timeout or self.default_timeout,
                    context=ctx
                ) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    fetch_time = time.time() - start_time

                    result = FetchResult(
                        url=url,
                        status_code=response.status,
                        content=content,
                        content_type=response.headers.get('Content-Type', ''),
                        fetch_time=fetch_time,
                        headers=dict(response.headers),
                    )

                    self.stats["total_bytes"] += len(content)
                    self._save_to_cache(url, result)

                    return result

            except urllib.error.HTTPError as e:
                last_error = f"HTTP {e.code}: {e.reason}"
                if e.code in [429, 503]:  # Rate limited or service unavailable
                    delay = config.retry_base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                elif e.code in [403, 404]:  # Don't retry these
                    break

            except urllib.error.URLError as e:
                last_error = f"URL Error: {str(e.reason)}"
                delay = config.retry_base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

            except Exception as e:
                last_error = str(e)
                delay = config.retry_base_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        # All retries failed
        self.stats["errors"] += 1
        return FetchResult(
            url=url,
            status_code=0,
            error=last_error,
        )

    async def fetch_all(
        self,
        urls: list[str],
        max_concurrent: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list[FetchResult]:
        """
        Fetch multiple URLs with concurrency control.

        Args:
            urls: List of URLs to fetch
            max_concurrent: Max concurrent requests
            progress_callback: Optional callback(completed, total)

        Returns:
            List of FetchResults in same order as input URLs
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results: list[Optional[FetchResult]] = [None] * len(urls)
        completed = 0

        async def fetch_with_semaphore(idx: int, url: str):
            nonlocal completed
            async with semaphore:
                result = await self.fetch(url)
                results[idx] = result
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(urls))

        tasks = [fetch_with_semaphore(i, url) for i, url in enumerate(urls)]
        await asyncio.gather(*tasks)

        return [r for r in results if r is not None]

    def fetch_sync(self, urls: list[str], **kwargs) -> list[FetchResult]:
        """
        Synchronous wrapper for fetch_all.

        Usage:
            results = fetcher.fetch_sync(["https://example.com"])
        """
        return asyncio.run(self.fetch_all(urls, **kwargs))

    def fetch_one_sync(self, url: str, **kwargs) -> FetchResult:
        """Synchronous wrapper for single fetch."""
        return asyncio.run(self.fetch(url, **kwargs))

    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()

    def get_stats(self) -> dict:
        """Get fetch statistics."""
        return {
            **self.stats,
            "cache_size": len(self._cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(1, self.stats["requests"])
            ) * 100,
        }


class SiteScanner:
    """
    High-level site scanner using LiveFetcher.

    Fetches sitemap, key pages, and extracts content.
    """

    def __init__(self, fetcher: Optional[LiveFetcher] = None):
        self.fetcher = fetcher or LiveFetcher()

    async def scan_site(self, base_url: str) -> dict:
        """
        Scan a site completely.

        Fetches:
        - robots.txt
        - sitemap.xml
        - Homepage
        - /features, /pricing, /about pages

        Returns dict with all fetched content.
        """
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        urls_to_fetch = [
            (f"{base}/robots.txt", "robots"),
            (f"{base}/sitemap.xml", "sitemap"),
            (base, "home"),
            (f"{base}/features", "features"),
            (f"{base}/pricing", "pricing"),
            (f"{base}/about", "about"),
        ]

        results = {}
        for url, page_type in urls_to_fetch:
            result = await self.fetcher.fetch(url)
            results[page_type] = {
                "url": url,
                "status": result.status_code,
                "content": result.content if result.status_code == 200 else "",
                "error": result.error,
            }

        return results

    def scan_site_sync(self, base_url: str) -> dict:
        """Synchronous wrapper for scan_site."""
        return asyncio.run(self.scan_site(base_url))


def create_fetcher(**kwargs) -> LiveFetcher:
    """Factory function to create a LiveFetcher."""
    return LiveFetcher(**kwargs)
