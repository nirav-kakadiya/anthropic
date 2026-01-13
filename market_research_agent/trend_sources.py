"""
Trend Sources - Multiple trend sources with real-time scraping.

Inspired by NewsNow but focused on AI/Tech with keyword extraction.

Sources:
- GitHub Trending (daily/weekly)
- Hacker News (top/new)
- Product Hunt (top products)
- Reddit (AI subreddits)
- Dev.to (trending)
- Lobste.rs (hottest)
- Twitter/X (AI topics)
- ArXiv (AI papers)
"""

import asyncio
import re
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from urllib.parse import urljoin, quote


@dataclass
class TrendItem:
    """Single trending item."""
    id: str
    title: str
    url: str
    source: str
    source_type: Literal["hottest", "realtime", "rising"]
    score: int = 0  # upvotes/stars/points
    comments: int = 0
    category: str = "tech"  # tech, ai, startup, finance
    keywords: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SourceConfig:
    """Configuration for a trend source."""
    id: str
    name: str
    home_url: str
    fetch_url: str
    source_type: Literal["hottest", "realtime", "rising"]
    category: str
    interval_seconds: int = 600  # 10 min default
    requires_api_key: bool = False
    enabled: bool = True


class TrendSources:
    """
    Multi-source trend fetcher.

    Usage:
        sources = TrendSources()

        # Fetch all sources
        items = await sources.fetch_all()

        # Fetch specific source
        items = await sources.fetch("github-trending")

        # Get top keywords
        keywords = sources.extract_top_keywords(items)
    """

    # All available sources
    SOURCES = {
        # GitHub
        "github-trending": SourceConfig(
            id="github-trending",
            name="GitHub Trending",
            home_url="https://github.com",
            fetch_url="https://github.com/trending?spoken_language_code=en",
            source_type="hottest",
            category="tech",
            interval_seconds=3600,
        ),
        "github-trending-ai": SourceConfig(
            id="github-trending-ai",
            name="GitHub AI Trending",
            home_url="https://github.com",
            fetch_url="https://github.com/trending/python?since=daily",
            source_type="hottest",
            category="ai",
            interval_seconds=3600,
        ),

        # Hacker News
        "hackernews-top": SourceConfig(
            id="hackernews-top",
            name="Hacker News Top",
            home_url="https://news.ycombinator.com",
            fetch_url="https://hacker-news.firebaseio.com/v0/topstories.json",
            source_type="hottest",
            category="tech",
            interval_seconds=300,
        ),
        "hackernews-new": SourceConfig(
            id="hackernews-new",
            name="Hacker News New",
            home_url="https://news.ycombinator.com",
            fetch_url="https://hacker-news.firebaseio.com/v0/newstories.json",
            source_type="realtime",
            category="tech",
            interval_seconds=180,
        ),
        "hackernews-ai": SourceConfig(
            id="hackernews-ai",
            name="HN AI Search",
            home_url="https://news.ycombinator.com",
            fetch_url="https://hn.algolia.com/api/v1/search?query=AI&tags=story&hitsPerPage=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),

        # Reddit AI Subreddits
        "reddit-machinelearning": SourceConfig(
            id="reddit-machinelearning",
            name="r/MachineLearning",
            home_url="https://reddit.com/r/MachineLearning",
            fetch_url="https://old.reddit.com/r/MachineLearning/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-stablediffusion": SourceConfig(
            id="reddit-stablediffusion",
            name="r/StableDiffusion",
            home_url="https://reddit.com/r/StableDiffusion",
            fetch_url="https://old.reddit.com/r/StableDiffusion/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-comfyui": SourceConfig(
            id="reddit-comfyui",
            name="r/comfyui",
            home_url="https://reddit.com/r/comfyui",
            fetch_url="https://old.reddit.com/r/comfyui/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-localllama": SourceConfig(
            id="reddit-localllama",
            name="r/LocalLLaMA",
            home_url="https://reddit.com/r/LocalLLaMA",
            fetch_url="https://old.reddit.com/r/LocalLLaMA/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-chatgpt": SourceConfig(
            id="reddit-chatgpt",
            name="r/ChatGPT",
            home_url="https://reddit.com/r/ChatGPT",
            fetch_url="https://old.reddit.com/r/ChatGPT/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-artificial": SourceConfig(
            id="reddit-artificial",
            name="r/artificial",
            home_url="https://reddit.com/r/artificial",
            fetch_url="https://old.reddit.com/r/artificial/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-singularity": SourceConfig(
            id="reddit-singularity",
            name="r/singularity",
            home_url="https://reddit.com/r/singularity",
            fetch_url="https://old.reddit.com/r/singularity/hot/.json?limit=50",
            source_type="hottest",
            category="ai",
            interval_seconds=600,
        ),
        "reddit-saas": SourceConfig(
            id="reddit-saas",
            name="r/SaaS",
            home_url="https://reddit.com/r/SaaS",
            fetch_url="https://old.reddit.com/r/SaaS/hot/.json?limit=50",
            source_type="hottest",
            category="startup",
            interval_seconds=1800,
        ),
        "reddit-startups": SourceConfig(
            id="reddit-startups",
            name="r/startups",
            home_url="https://reddit.com/r/startups",
            fetch_url="https://old.reddit.com/r/startups/hot/.json?limit=50",
            source_type="hottest",
            category="startup",
            interval_seconds=1800,
        ),

        # Dev Communities
        "devto-top": SourceConfig(
            id="devto-top",
            name="Dev.to Top",
            home_url="https://dev.to",
            fetch_url="https://dev.to/api/articles?top=7&per_page=50",
            source_type="hottest",
            category="tech",
            interval_seconds=3600,
        ),
        "lobsters": SourceConfig(
            id="lobsters",
            name="Lobste.rs",
            home_url="https://lobste.rs",
            fetch_url="https://lobste.rs/hottest.json",
            source_type="hottest",
            category="tech",
            interval_seconds=1800,
        ),

        # AI Papers
        "arxiv-ai": SourceConfig(
            id="arxiv-ai",
            name="ArXiv AI",
            home_url="https://arxiv.org",
            fetch_url="https://export.arxiv.org/api/query?search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=30",
            source_type="realtime",
            category="ai",
            interval_seconds=3600,
        ),
        "arxiv-ml": SourceConfig(
            id="arxiv-ml",
            name="ArXiv ML",
            home_url="https://arxiv.org",
            fetch_url="https://export.arxiv.org/api/query?search_query=cat:cs.LG&sortBy=submittedDate&sortOrder=descending&max_results=30",
            source_type="realtime",
            category="ai",
            interval_seconds=3600,
        ),

        # Product Hunt
        "producthunt": SourceConfig(
            id="producthunt",
            name="Product Hunt",
            home_url="https://producthunt.com",
            fetch_url="https://www.producthunt.com/",  # Scrape homepage
            source_type="hottest",
            category="startup",
            interval_seconds=3600,
            requires_api_key=True,  # Better with API
        ),
    }

    # AI Keywords to detect
    AI_KEYWORDS = {
        # Image Models
        "flux", "sdxl", "stable diffusion", "midjourney", "dall-e", "dalle",
        "imagen", "ideogram", "leonardo", "playground",
        # Video Models
        "sora", "runway", "pika", "kling", "luma", "haiper", "minimax",
        "animate diff", "svd", "stable video",
        # LLMs
        "gpt-4", "gpt-5", "claude", "gemini", "llama", "mistral", "qwen",
        "deepseek", "phi", "command r", "dbrx",
        # Tools
        "comfyui", "automatic1111", "fooocus", "invoke ai", "kohya",
        "controlnet", "ipadapter", "lora", "dreambooth",
        # Techniques
        "fine-tune", "fine-tuning", "rag", "agent", "multi-modal",
        "diffusion", "transformer", "attention", "embedding",
        # Applications
        "text-to-image", "text-to-video", "image-to-video", "voice clone",
        "ai avatar", "ai headshot", "background removal", "upscale",
    }

    def __init__(self):
        from .live_fetcher import LiveFetcher
        self.fetcher = LiveFetcher(cache_ttl_minutes=5)
        self._items: list[TrendItem] = []

    async def fetch(self, source_id: str) -> list[TrendItem]:
        """Fetch items from a specific source."""
        if source_id not in self.SOURCES:
            return []

        config = self.SOURCES[source_id]
        if not config.enabled:
            return []

        result = await self.fetcher.fetch(config.fetch_url)
        if result.status_code != 200:
            return []

        # Parse based on source type
        if "github" in source_id:
            return self._parse_github(result.content, config)
        elif "hackernews" in source_id:
            return self._parse_hackernews(result.content, config)
        elif "reddit" in source_id:
            return self._parse_reddit(result.content, config)
        elif "devto" in source_id:
            return self._parse_devto(result.content, config)
        elif "lobsters" in source_id:
            return self._parse_lobsters(result.content, config)
        elif "arxiv" in source_id:
            return self._parse_arxiv(result.content, config)

        return []

    async def fetch_all(self, categories: list[str] = None) -> list[TrendItem]:
        """Fetch from all enabled sources."""
        tasks = []

        for source_id, config in self.SOURCES.items():
            if not config.enabled:
                continue
            if categories and config.category not in categories:
                continue
            if config.requires_api_key:
                continue  # Skip API-required sources

            tasks.append(self.fetch(source_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        items = []
        for result in results:
            if isinstance(result, list):
                items.extend(result)

        # Sort by score
        items.sort(key=lambda x: x.score, reverse=True)

        self._items = items
        return items

    def _parse_github(self, html: str, config: SourceConfig) -> list[TrendItem]:
        """Parse GitHub trending page."""
        items = []

        # Extract repo articles
        pattern = r'<article[^>]*>.*?<h2[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>\s*([^<]+)\s*/\s*<span[^>]*>([^<]+)</span>.*?</article>'
        matches = re.findall(pattern, html, re.DOTALL)

        for match in matches[:30]:
            url_path, owner, repo = match
            title = f"{owner.strip()}/{repo.strip()}"

            # Extract stars
            star_match = re.search(rf'{re.escape(url_path)}/stargazers[^>]*>([^<]+)', html)
            stars = 0
            if star_match:
                stars_text = star_match.group(1).strip().replace(",", "")
                try:
                    stars = int(stars_text)
                except ValueError:
                    pass

            keywords = self._extract_ai_keywords(title)

            items.append(TrendItem(
                id=url_path,
                title=title,
                url=f"https://github.com{url_path}",
                source=config.id,
                source_type=config.source_type,
                score=stars,
                category=config.category,
                keywords=keywords,
            ))

        return items

    def _parse_hackernews(self, content: str, config: SourceConfig) -> list[TrendItem]:
        """Parse Hacker News API response."""
        items = []

        try:
            data = json.loads(content)

            # Handle different API formats
            if isinstance(data, list):
                # topstories/newstories returns list of IDs
                # We'd need to fetch each story - skip for now
                return items

            # Algolia API format
            hits = data.get("hits", [])
            for hit in hits[:30]:
                title = hit.get("title", "")
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)

                keywords = self._extract_ai_keywords(title)

                items.append(TrendItem(
                    id=str(hit.get("objectID", "")),
                    title=title,
                    url=url,
                    source=config.id,
                    source_type=config.source_type,
                    score=points,
                    comments=comments,
                    category=config.category,
                    keywords=keywords,
                ))

        except json.JSONDecodeError:
            pass

        return items

    def _parse_reddit(self, content: str, config: SourceConfig) -> list[TrendItem]:
        """Parse Reddit JSON API response."""
        items = []

        try:
            data = json.loads(content)
            posts = data.get("data", {}).get("children", [])

            for post in posts[:30]:
                post_data = post.get("data", {})

                title = post_data.get("title", "")
                url = f"https://reddit.com{post_data.get('permalink', '')}"
                score = post_data.get("score", 0)
                comments = post_data.get("num_comments", 0)

                keywords = self._extract_ai_keywords(title)

                items.append(TrendItem(
                    id=post_data.get("id", ""),
                    title=title,
                    url=url,
                    source=config.id,
                    source_type=config.source_type,
                    score=score,
                    comments=comments,
                    category=config.category,
                    keywords=keywords,
                    extra={
                        "subreddit": post_data.get("subreddit", ""),
                        "author": post_data.get("author", ""),
                    }
                ))

        except json.JSONDecodeError:
            pass

        return items

    def _parse_devto(self, content: str, config: SourceConfig) -> list[TrendItem]:
        """Parse Dev.to API response."""
        items = []

        try:
            articles = json.loads(content)

            for article in articles[:30]:
                title = article.get("title", "")
                url = article.get("url", "")
                score = article.get("public_reactions_count", 0)
                comments = article.get("comments_count", 0)

                keywords = self._extract_ai_keywords(title)

                items.append(TrendItem(
                    id=str(article.get("id", "")),
                    title=title,
                    url=url,
                    source=config.id,
                    source_type=config.source_type,
                    score=score,
                    comments=comments,
                    category=config.category,
                    keywords=keywords,
                ))

        except json.JSONDecodeError:
            pass

        return items

    def _parse_lobsters(self, content: str, config: SourceConfig) -> list[TrendItem]:
        """Parse Lobste.rs JSON response."""
        items = []

        try:
            stories = json.loads(content)

            for story in stories[:30]:
                title = story.get("title", "")
                url = story.get("url") or story.get("comments_url", "")
                score = story.get("score", 0)
                comments = story.get("comment_count", 0)

                keywords = self._extract_ai_keywords(title)

                items.append(TrendItem(
                    id=story.get("short_id", ""),
                    title=title,
                    url=url,
                    source=config.id,
                    source_type=config.source_type,
                    score=score,
                    comments=comments,
                    category=config.category,
                    keywords=keywords,
                ))

        except json.JSONDecodeError:
            pass

        return items

    def _parse_arxiv(self, content: str, config: SourceConfig) -> list[TrendItem]:
        """Parse ArXiv Atom feed."""
        items = []

        # Simple XML parsing
        entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)

        for entry in entries[:30]:
            title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            link_match = re.search(r'<id>(.*?)</id>', entry)

            if title_match and link_match:
                title = re.sub(r'\s+', ' ', title_match.group(1)).strip()
                url = link_match.group(1).strip()

                keywords = self._extract_ai_keywords(title)

                items.append(TrendItem(
                    id=url,
                    title=title,
                    url=url,
                    source=config.id,
                    source_type=config.source_type,
                    score=0,  # ArXiv doesn't have upvotes
                    category=config.category,
                    keywords=keywords,
                ))

        return items

    def _extract_ai_keywords(self, text: str) -> list[str]:
        """Extract AI-related keywords from text."""
        text_lower = text.lower()
        found = []

        for keyword in self.AI_KEYWORDS:
            if keyword in text_lower:
                found.append(keyword)

        return found

    def get_top_keywords(self, items: list[TrendItem] = None, limit: int = 30) -> list[dict]:
        """Get top keywords from items, ranked by occurrence and score."""
        items = items or self._items

        keyword_stats = {}

        for item in items:
            for keyword in item.keywords:
                if keyword not in keyword_stats:
                    keyword_stats[keyword] = {
                        "keyword": keyword,
                        "count": 0,
                        "total_score": 0,
                        "sources": set(),
                    }
                keyword_stats[keyword]["count"] += 1
                keyword_stats[keyword]["total_score"] += item.score
                keyword_stats[keyword]["sources"].add(item.source)

        # Convert to list and calculate rank
        ranked = []
        for kw, stats in keyword_stats.items():
            rank_score = stats["count"] * 10 + len(stats["sources"]) * 20 + min(stats["total_score"], 1000) / 10
            ranked.append({
                "keyword": kw,
                "count": stats["count"],
                "sources": len(stats["sources"]),
                "total_score": stats["total_score"],
                "rank_score": rank_score,
            })

        ranked.sort(key=lambda x: x["rank_score"], reverse=True)
        return ranked[:limit]

    def get_items_by_category(self, category: str) -> list[TrendItem]:
        """Get items filtered by category."""
        return [i for i in self._items if i.category == category]

    def get_sources_list(self) -> list[dict]:
        """Get list of all available sources."""
        return [
            {
                "id": config.id,
                "name": config.name,
                "category": config.category,
                "type": config.source_type,
                "enabled": config.enabled,
            }
            for config in self.SOURCES.values()
        ]


def create_trend_sources() -> TrendSources:
    """Factory function."""
    return TrendSources()
