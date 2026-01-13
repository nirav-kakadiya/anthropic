"""
Trend Gatherer module - Gathers trend signals from various sources.

Sources:
- Google Trends (via search queries)
- Twitter/X
- Reddit
- Product Hunt
- Hacker News
- YouTube

Calculates trend scores based on time windows (7d, 30d, 90d).
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
from .models import Keyword, SocialMetrics


class TimeWindow(Enum):
    """Time windows for trend analysis."""
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"


@dataclass
class TrendDataPoint:
    """A single trend data point."""
    keyword: str
    platform: str
    value: float  # Normalized 0-100
    timestamp: str
    raw_data: dict = field(default_factory=dict)


@dataclass
class TrendResult:
    """Aggregated trend results for a keyword."""
    keyword: str
    trend_7d: float = 0.0  # Slope/growth rate
    trend_30d: float = 0.0
    trend_90d: float = 0.0
    current_interest: float = 0.0  # Current normalized value
    peak_interest: float = 0.0
    data_points: list[TrendDataPoint] = field(default_factory=list)


class TrendGatherer:
    """
    Gathers and aggregates trend signals from multiple sources.

    Note: This provides the structure and query generation.
    Actual API calls should be made by the orchestrator using
    web search or specific API clients.

    Usage:
        gatherer = TrendGatherer()
        queries = gatherer.generate_trend_queries(keywords)
    """

    # Platform-specific search templates
    SEARCH_TEMPLATES = {
        "google_trends": [
            "{keyword} trend",
            "{keyword} interest over time",
        ],
        "twitter": [
            "site:twitter.com {keyword}",
            "{keyword} twitter mentions",
            "#{keyword} twitter",
        ],
        "reddit": [
            "site:reddit.com {keyword}",
            "{keyword} reddit discussion",
            "{keyword} subreddit",
        ],
        "producthunt": [
            "site:producthunt.com {keyword}",
            "{keyword} product hunt launch",
        ],
        "hackernews": [
            "site:news.ycombinator.com {keyword}",
            "{keyword} hacker news",
        ],
        "youtube": [
            "site:youtube.com {keyword}",
            "{keyword} youtube tutorial",
        ],
    }

    # Reddit API endpoints (for reference)
    REDDIT_SEARCH_URL = "https://old.reddit.com/search/?q={query}&sort=new&t=month"
    REDDIT_SUBREDDIT_URL = "https://old.reddit.com/r/{subreddit}/search/?q={query}&sort=new&t=month"

    def __init__(self, time_window: TimeWindow = TimeWindow.LAST_90_DAYS):
        self.time_window = time_window

    def generate_trend_queries(self, keywords: list[str], platforms: Optional[list[str]] = None) -> dict[str, list[str]]:
        """
        Generate search queries for trend research.

        Args:
            keywords: List of keywords to research
            platforms: Specific platforms to query (default: all)

        Returns:
            Dictionary mapping platform -> list of queries
        """
        if platforms is None:
            platforms = list(self.SEARCH_TEMPLATES.keys())

        queries: dict[str, list[str]] = {p: [] for p in platforms}

        for keyword in keywords[:50]:  # Limit to top 50
            for platform in platforms:
                templates = self.SEARCH_TEMPLATES.get(platform, [])
                for template in templates[:1]:  # One query per platform per keyword
                    query = template.format(keyword=keyword)
                    queries[platform].append(query)

        return queries

    def generate_social_queries(self, keywords: list[str]) -> dict:
        """
        Generate specific queries for social listening.

        Returns structured queries for each platform.
        """
        return {
            "twitter": {
                "search_queries": [
                    f'"{kw}" -is:retweet lang:en' for kw in keywords[:30]
                ],
                "hashtag_queries": [
                    f'#{kw.replace(" ", "")}' for kw in keywords[:30]
                ],
                "time_filter": f"last {self.time_window.value}",
            },
            "reddit": {
                "search_queries": [
                    {"query": kw, "subreddits": ["all"], "sort": "new", "time": "month"}
                    for kw in keywords[:30]
                ],
                "subreddit_discovery": [
                    f"subreddit for {kw}" for kw in keywords[:10]
                ],
            },
            "producthunt": {
                "search_queries": keywords[:20],
                "category_filters": ["saas", "developer-tools", "productivity"],
            },
            "hackernews": {
                "search_queries": keywords[:20],
                "endpoints": [
                    "https://hn.algolia.com/api/v1/search?query={query}&tags=story"
                ],
            },
        }

    def calculate_trend_slope(self, data_points: list[float]) -> float:
        """
        Calculate trend slope from time series data.

        Simple linear regression slope normalized to -1 to 1.
        Positive = growing, Negative = declining.
        """
        if len(data_points) < 2:
            return 0.0

        n = len(data_points)
        x = list(range(n))

        x_mean = sum(x) / n
        y_mean = sum(data_points) / n

        numerator = sum((x[i] - x_mean) * (data_points[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0

        slope = numerator / denominator

        # Normalize to -1 to 1 range
        max_change = max(data_points) - min(data_points) if data_points else 1
        if max_change > 0:
            normalized = slope / max_change
            return max(-1.0, min(1.0, normalized))

        return 0.0

    def parse_google_trends_data(self, raw_response: str) -> list[float]:
        """
        Parse Google Trends data from search results.

        Note: This is a heuristic parser for search result snippets.
        For production, use the official pytrends library.
        """
        data_points = []

        # Look for percentage patterns
        percentages = re.findall(r'(\d+)%', raw_response)
        for p in percentages:
            data_points.append(float(p))

        # Look for "interest" scores
        interests = re.findall(r'interest[:\s]+(\d+)', raw_response, re.IGNORECASE)
        for i in interests:
            data_points.append(float(i))

        return data_points

    def aggregate_social_metrics(
        self,
        keyword: str,
        twitter_data: Optional[dict] = None,
        reddit_data: Optional[dict] = None,
        ph_data: Optional[dict] = None,
        hn_data: Optional[dict] = None
    ) -> SocialMetrics:
        """
        Aggregate social metrics from various sources.

        Args:
            keyword: The keyword being tracked
            twitter_data: Twitter/X metrics
            reddit_data: Reddit metrics
            ph_data: Product Hunt metrics
            hn_data: Hacker News metrics

        Returns:
            Aggregated SocialMetrics
        """
        metrics = SocialMetrics(keyword=keyword)

        if twitter_data:
            metrics.twitter_mentions = twitter_data.get("mention_count", 0)
            metrics.twitter_hashtags = twitter_data.get("hashtags", [])[:5]
            metrics.twitter_influencers = twitter_data.get("top_accounts", [])[:5]

        if reddit_data:
            metrics.reddit_subreddits = reddit_data.get("subreddits", [])[:10]
            metrics.reddit_posts = reddit_data.get("post_count", 0)
            metrics.reddit_avg_upvotes = reddit_data.get("avg_upvotes", 0.0)
            metrics.reddit_top_posts = reddit_data.get("top_posts", [])[:5]

        if ph_data:
            metrics.producthunt_launches = ph_data.get("launches", [])[:5]

        if hn_data:
            metrics.hackernews_threads = hn_data.get("thread_count", 0)
            metrics.hackernews_titles = hn_data.get("titles", [])[:5]

        return metrics

    def extract_pain_points(self, discussions: list[str]) -> list[str]:
        """
        Extract pain points and complaints from discussion text.

        Looks for common complaint patterns.
        """
        pain_points = []

        pain_patterns = [
            r"(?:i\s+)?hate\s+(?:that|when|how)\s+([^.!?]+)",
            r"(?:so\s+)?frustrat(?:ing|ed)\s+(?:that|when|with)\s+([^.!?]+)",
            r"wish\s+(?:there\s+was|i\s+could)\s+([^.!?]+)",
            r"(?:the\s+)?problem\s+(?:is|with)\s+([^.!?]+)",
            r"(?:it's|its)\s+(?:so\s+)?hard\s+to\s+([^.!?]+)",
            r"why\s+(?:can't|doesn't|isn't)\s+([^.!?]+)",
            r"need\s+(?:a\s+)?better\s+([^.!?]+)",
            r"looking\s+for\s+(?:a|an)?\s*([^.!?]+)\s+alternative",
            r"([^.!?]+)\s+(?:sucks|is\s+terrible|doesn't\s+work)",
        ]

        for text in discussions:
            text_lower = text.lower()
            for pattern in pain_patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    cleaned = match.strip()
                    if 10 < len(cleaned) < 200:
                        pain_points.append(cleaned)

        # Deduplicate and limit
        seen = set()
        unique = []
        for pp in pain_points:
            normalized = pp.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique.append(pp)

        return unique[:10]


def create_trend_search_plan(keywords: list[Keyword], site_type: str) -> dict:
    """
    Create a comprehensive trend search plan.

    Returns a structured plan with all queries needed.
    """
    gatherer = TrendGatherer()

    keyword_strings = [k.keyword for k in keywords[:50]]

    plan = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "site_type": site_type,
            "keyword_count": len(keyword_strings),
            "time_window": "90d",
        },
        "google_trends": {
            "queries": keyword_strings[:20],
            "comparison_groups": [
                keyword_strings[i:i+5] for i in range(0, min(20, len(keyword_strings)), 5)
            ],
        },
        "social_listening": gatherer.generate_social_queries(keyword_strings),
        "web_searches": gatherer.generate_trend_queries(keyword_strings),
        "direct_urls": {
            "reddit_searches": [
                f"https://old.reddit.com/search/?q={kw.replace(' ', '+')}&sort=new&t=month"
                for kw in keyword_strings[:20]
            ],
            "producthunt_searches": [
                f"https://www.producthunt.com/search?q={kw.replace(' ', '+')}"
                for kw in keyword_strings[:10]
            ],
            "hackernews_searches": [
                f"https://hn.algolia.com/api/v1/search?query={kw.replace(' ', '+')}&tags=story"
                for kw in keyword_strings[:10]
            ],
        },
    }

    return plan
