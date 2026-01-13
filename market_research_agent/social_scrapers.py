"""
Social Platform Scrapers - Product Hunt, Hacker News, Twitter/X integration.

Provides:
- URL generation for scraping
- Result parsing
- Keyword extraction from posts/launches
- Trend signal creation
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ProductHuntLaunch:
    """A Product Hunt launch/product."""
    name: str
    tagline: str = ""
    url: str = ""
    votes: int = 0
    comments: int = 0
    launch_date: str = ""
    topics: list[str] = field(default_factory=list)
    keywords_found: list[str] = field(default_factory=list)


@dataclass
class HackerNewsPost:
    """A Hacker News post/discussion."""
    title: str
    url: str = ""
    points: int = 0
    comments: int = 0
    author: str = ""
    created_at: str = ""
    keywords_found: list[str] = field(default_factory=list)


@dataclass
class TwitterMention:
    """A Twitter/X mention."""
    text: str
    author: str = ""
    likes: int = 0
    retweets: int = 0
    url: str = ""
    created_at: str = ""
    hashtags: list[str] = field(default_factory=list)
    keywords_found: list[str] = field(default_factory=list)


class ProductHuntScanner:
    """
    Scans Product Hunt for AI tool launches.

    Usage:
        scanner = ProductHuntScanner()
        urls = scanner.get_search_urls(["ai image", "video generator"])
    """

    BASE_URL = "https://www.producthunt.com"

    # AI-related topics on Product Hunt
    AI_TOPICS = [
        "artificial-intelligence",
        "machine-learning",
        "generative-ai",
        "ai-tools",
        "image-generation",
        "video-generation",
        "text-to-image",
        "text-to-video",
        "ai-assistants",
        "developer-tools",
    ]

    def __init__(self):
        pass

    def get_topic_urls(self) -> list[dict]:
        """Get URLs for AI-related topic pages."""
        urls = []
        for topic in self.AI_TOPICS:
            urls.append({
                "topic": topic,
                "url": f"{self.BASE_URL}/topics/{topic}",
                "type": "topic_page"
            })
        return urls

    def get_search_urls(self, keywords: list[str]) -> list[dict]:
        """Get search URLs for specific keywords."""
        urls = []
        for keyword in keywords[:20]:
            query = keyword.replace(" ", "+")
            urls.append({
                "keyword": keyword,
                "url": f"{self.BASE_URL}/search?q={query}",
                "type": "search"
            })
        return urls

    def get_daily_urls(self, days: int = 7) -> list[dict]:
        """Get URLs for recent daily launches."""
        urls = []
        for i in range(days):
            date = datetime.now() - __import__('datetime').timedelta(days=i)
            date_str = date.strftime("%Y/%m/%d")
            urls.append({
                "date": date_str,
                "url": f"{self.BASE_URL}/time-travel/{date_str}",
                "type": "daily"
            })
        return urls

    def extract_launch_keywords(self, title: str, tagline: str) -> list[str]:
        """Extract AI-related keywords from launch title/tagline."""
        text = f"{title} {tagline}".lower()
        keywords = []

        # AI model patterns
        patterns = [
            r"\bai\b", r"\bgpt\b", r"\bllm\b", r"\bchatbot\b",
            r"\bimage\s*generat", r"\bvideo\s*generat", r"\btext-to-",
            r"\bupscal", r"\bremov", r"\benhance", r"\bautomat",
            r"\bflux\b", r"\bstable\s*diffusion\b", r"\bmidjourney\b",
        ]

        for pattern in patterns:
            if re.search(pattern, text):
                # Extract the matched term
                match = re.search(pattern, text)
                if match:
                    keywords.append(match.group().strip())

        return list(set(keywords))


class HackerNewsScanner:
    """
    Scans Hacker News for AI discussions.

    Uses Algolia's free HN Search API.

    Usage:
        scanner = HackerNewsScanner()
        urls = scanner.get_search_urls(["comfyui", "stable diffusion"])
    """

    # Algolia HN Search API
    API_BASE = "https://hn.algolia.com/api/v1"

    def __init__(self):
        pass

    def get_search_urls(
        self,
        keywords: list[str],
        tags: str = "story",
        time_range: str = "month"
    ) -> list[dict]:
        """
        Get Algolia API URLs for keyword searches.

        Args:
            keywords: Keywords to search
            tags: Filter by type (story, comment, poll, etc.)
            time_range: Time filter (day, week, month, year)
        """
        urls = []

        # Calculate timestamp for time range
        time_seconds = {
            "day": 86400,
            "week": 604800,
            "month": 2592000,
            "year": 31536000,
        }
        seconds = time_seconds.get(time_range, 2592000)

        for keyword in keywords[:30]:
            query = keyword.replace(" ", "%20")
            url = (
                f"{self.API_BASE}/search?"
                f"query={query}&"
                f"tags={tags}&"
                f"numericFilters=created_at_i>{int(datetime.now().timestamp()) - seconds}"
            )
            urls.append({
                "keyword": keyword,
                "url": url,
                "type": "api",
                "api": "algolia"
            })

        return urls

    def get_front_page_url(self) -> dict:
        """Get URL for current front page stories."""
        return {
            "type": "front_page",
            "url": f"{self.API_BASE}/search?tags=front_page",
            "api": "algolia"
        }

    def get_popular_urls(self, time_range: str = "week") -> list[dict]:
        """Get URLs for popular AI-related stories."""
        ai_queries = [
            "AI", "GPT", "LLM", "Stable Diffusion", "image generation",
            "video generation", "ComfyUI", "machine learning", "neural network"
        ]

        return self.get_search_urls(ai_queries, time_range=time_range)

    def parse_algolia_response(self, json_data: dict) -> list[HackerNewsPost]:
        """Parse Algolia API response into HackerNewsPost objects."""
        posts = []

        for hit in json_data.get("hits", []):
            post = HackerNewsPost(
                title=hit.get("title", ""),
                url=hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                points=hit.get("points", 0),
                comments=hit.get("num_comments", 0),
                author=hit.get("author", ""),
                created_at=hit.get("created_at", ""),
            )
            posts.append(post)

        return posts


class TwitterScanner:
    """
    Generates Twitter/X search queries for AI trends.

    Note: Actual API access requires Twitter API credentials.
    This generates search URLs and queries for manual or API use.
    """

    SEARCH_BASE = "https://twitter.com/search"

    # AI-related accounts to monitor
    AI_ACCOUNTS = [
        "StabilityAI", "OpenAI", "AnthropicAI", "midaborney",
        "EMostaque", "DrJimFan", "kaborine", "8co28",
        "hardmaru", "_akhaliq", "ylecun", "AndrewYNg",
    ]

    def __init__(self):
        pass

    def get_search_urls(self, keywords: list[str], time_filter: str = "week") -> list[dict]:
        """
        Get Twitter search URLs.

        Args:
            keywords: Keywords to search
            time_filter: Not directly supported in URL, for reference
        """
        urls = []

        for keyword in keywords[:20]:
            query = keyword.replace(" ", "%20")
            # Twitter advanced search URL
            url = f"{self.SEARCH_BASE}?q={query}&f=live"
            urls.append({
                "keyword": keyword,
                "url": url,
                "type": "search",
                "platform": "twitter"
            })

        return urls

    def get_hashtag_urls(self, hashtags: list[str]) -> list[dict]:
        """Get URLs for hashtag searches."""
        urls = []

        for tag in hashtags[:15]:
            # Remove # if present
            tag_clean = tag.lstrip("#").replace(" ", "")
            url = f"{self.SEARCH_BASE}?q=%23{tag_clean}&f=live"
            urls.append({
                "hashtag": f"#{tag_clean}",
                "url": url,
                "type": "hashtag"
            })

        return urls

    def generate_search_queries(self, keywords: list[str]) -> list[str]:
        """Generate Twitter advanced search queries."""
        queries = []

        for keyword in keywords[:20]:
            # Basic search
            queries.append(keyword)

            # With engagement filter
            queries.append(f"{keyword} min_faves:10")

            # Recent only
            queries.append(f"{keyword} -is:retweet")

        return queries

    def get_account_urls(self) -> list[dict]:
        """Get URLs for AI-related accounts to monitor."""
        return [
            {"account": acc, "url": f"https://twitter.com/{acc}"}
            for acc in self.AI_ACCOUNTS
        ]


class SocialAggregator:
    """
    Aggregates results from all social platforms.

    Usage:
        agg = SocialAggregator()
        all_urls = agg.get_all_urls(keywords)
    """

    def __init__(self):
        self.ph_scanner = ProductHuntScanner()
        self.hn_scanner = HackerNewsScanner()
        self.twitter_scanner = TwitterScanner()

    def get_all_urls(self, keywords: list[str]) -> dict[str, list[dict]]:
        """Get URLs from all platforms for given keywords."""
        return {
            "producthunt": (
                self.ph_scanner.get_search_urls(keywords) +
                self.ph_scanner.get_topic_urls()
            ),
            "hackernews": self.hn_scanner.get_search_urls(keywords),
            "twitter": self.twitter_scanner.get_search_urls(keywords),
        }

    def get_trend_monitoring_urls(self) -> dict[str, list[dict]]:
        """Get URLs for general trend monitoring (no specific keywords)."""
        return {
            "producthunt": (
                self.ph_scanner.get_topic_urls() +
                self.ph_scanner.get_daily_urls(7)
            ),
            "hackernews": self.hn_scanner.get_popular_urls(),
            "twitter": self.twitter_scanner.get_account_urls(),
        }


# Convenience functions

def get_producthunt_urls(keywords: list[str]) -> list[str]:
    """Quick function to get Product Hunt search URLs."""
    scanner = ProductHuntScanner()
    return [u["url"] for u in scanner.get_search_urls(keywords)]


def get_hackernews_api_urls(keywords: list[str]) -> list[str]:
    """Quick function to get Hacker News API URLs."""
    scanner = HackerNewsScanner()
    return [u["url"] for u in scanner.get_search_urls(keywords)]


def get_twitter_search_queries(keywords: list[str]) -> list[str]:
    """Quick function to get Twitter search queries."""
    scanner = TwitterScanner()
    return scanner.generate_search_queries(keywords)
