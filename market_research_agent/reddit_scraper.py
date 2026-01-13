"""
Reddit Scraper module - Targets specific subreddits for AI tool/model mentions.

Focuses on AI-related subreddits:
- r/StableDiffusion
- r/comfyui
- r/generativeAI
- r/aiArt
- r/LocalLLaMA
- r/MachineLearning

Uses old.reddit.com for better scraping compatibility.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RedditPost:
    """A Reddit post with extracted information."""
    title: str
    url: str
    subreddit: str
    score: int = 0
    num_comments: int = 0
    created_utc: str = ""
    keywords_found: list[str] = field(default_factory=list)


@dataclass
class SubredditScan:
    """Results from scanning a subreddit."""
    subreddit: str
    posts_scanned: int = 0
    keywords_found: list[str] = field(default_factory=list)
    posts: list[RedditPost] = field(default_factory=list)
    scan_time: str = field(default_factory=lambda: datetime.now().isoformat())


class RedditScanner:
    """
    Scans Reddit for AI tool/model mentions.

    Usage:
        scanner = RedditScanner()
        urls = scanner.get_search_urls(["comfyui", "stable diffusion"])
    """

    # Target subreddits for AI tools/models
    AI_SUBREDDITS = [
        "StableDiffusion",
        "comfyui",
        "generativeAI",
        "aiArt",
        "LocalLLaMA",
        "MachineLearning",
        "artificial",
        "midjourney",
        "dalle2",
        "DefiantAI",
    ]

    # AI model/tool patterns to detect
    AI_PATTERNS = {
        # Image generation models
        "models": [
            r"\bflux\s*(?:ai|dev|schnell|pro|1\.1|kontext)?\b",
            r"\bstable\s*diffusion\s*(?:xl|3|2\.1|1\.5)?\b",
            r"\bsdxl\b",
            r"\bmidjourney\s*(?:v[456])?\b",
            r"\bdall-?e\s*[23]?\b",
            r"\bkling\s*(?:ai|1\.5|1\.6|2\.0|2\.1|2\.5|o1)?\b",
            r"\bwan\s*(?:ai|2\.2|2\.5)?\b",
            r"\bsora\s*(?:ai)?\b",
            r"\bveo\s*(?:3\.1)?\b",
            r"\bqwen\s*(?:image|edit|2512)?\b",
            r"\bnano\s*banana\s*(?:ai|pro)?\b",
            r"\bz-?image\s*(?:turbo)?\b",
            r"\bltx-?(?:2|v2)?\b",
            r"\bfooocus\b",
            r"\byume-?1\.5\b",
            r"\breve\s*ai\b",
            r"\bseedream\b",
        ],
        # Tools and workflows
        "tools": [
            r"\bcomfyui\s*(?:0\.\d+\.\d+|manager|workflow)?\b",
            r"\blora\s*(?:training)?\b",
            r"\bcontrolnet\b",
            r"\bipadapter[s]?\b",
            r"\brife\s*(?:vfi|\d+)?\b",
            r"\bgimm\s*vfi\b",
            r"\breactor\b",
            r"\bfaceswap\b",
            r"\bupscaler\b",
            r"\bframe\s*interpolation\b",
            r"\bvideo\s*helper\s*suite\b",
            r"\bttp\s*toolset\b",
            r"\bsage\s*attention\b",
            r"\bollama\b",
            r"\blm\s*studio\b",
            r"\binvokeai\b",
            r"\bforge\s*(?:webui)?\b",
            r"\ba1111\b",
            r"\bautomatic1111\b",
        ],
        # Techniques
        "techniques": [
            r"\blora\s*training\b",
            r"\bfine-?tuning\b",
            r"\bquantization\b",
            r"\bfp[48]\b",
            r"\bnvfp4\b",
            r"\bdistilled?\b",
            r"\bframe\s*injection\b",
            r"\bmulti-?frame\b",
            r"\bcharacter\s*consistency\b",
            r"\bimg2img\b",
            r"\btxt2img\b",
            r"\binpainting\b",
            r"\boutpainting\b",
        ],
        # Specific effects/filters
        "effects": [
            r"\bghibli\s*(?:filter|style|ai)?\b",
            r"\banime\s*(?:filter|style)?\b",
            r"\bcartoon\s*(?:filter|style)?\b",
            r"\bpixel\s*art\b",
            r"\bwimmelbilder?\b",
            r"\bpsychedelic\b",
            r"\bbeauty\s*filter\b",
            r"\bskin\s*smooth\b",
        ],
    }

    def __init__(self, subreddits: Optional[list[str]] = None):
        """
        Initialize scanner with target subreddits.

        Args:
            subreddits: List of subreddit names (without r/ prefix)
        """
        self.subreddits = subreddits or self.AI_SUBREDDITS
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict[str, list[re.Pattern]]:
        """Compile regex patterns for efficiency."""
        compiled = {}
        for category, patterns in self.AI_PATTERNS.items():
            compiled[category] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
        return compiled

    def get_subreddit_urls(self, sort: str = "new", time: str = "month") -> list[dict]:
        """
        Get URLs to scan for each subreddit.

        Args:
            sort: Sort method (new, hot, top, rising)
            time: Time filter for top (hour, day, week, month, year, all)

        Returns:
            List of dicts with subreddit and URL
        """
        urls = []
        for sub in self.subreddits:
            base_url = f"https://old.reddit.com/r/{sub}"

            urls.append({
                "subreddit": sub,
                "type": sort,
                "url": f"{base_url}/{sort}/?t={time}",
            })

        return urls

    def get_search_urls(self, keywords: list[str], time: str = "month") -> list[dict]:
        """
        Get Reddit search URLs for specific keywords.

        Args:
            keywords: Keywords to search for
            time: Time filter (hour, day, week, month, year, all)

        Returns:
            List of search URLs
        """
        urls = []

        for keyword in keywords[:30]:  # Limit to 30 keywords
            # Clean keyword for URL
            query = keyword.replace(" ", "+")

            # Search across all target subreddits
            for sub in self.subreddits[:5]:  # Top 5 subreddits
                urls.append({
                    "keyword": keyword,
                    "subreddit": sub,
                    "url": f"https://old.reddit.com/r/{sub}/search/?q={query}&sort=new&t={time}",
                })

            # Also search all of Reddit
            urls.append({
                "keyword": keyword,
                "subreddit": "all",
                "url": f"https://old.reddit.com/search/?q={query}&sort=new&t={time}",
            })

        return urls

    def extract_keywords_from_text(self, text: str) -> list[dict]:
        """
        Extract AI-related keywords from text.

        Args:
            text: Text to analyze (post title, body, etc.)

        Returns:
            List of dicts with keyword and category
        """
        found = []
        seen = set()

        for category, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text)
                for match in matches:
                    # Normalize the match
                    if isinstance(match, tuple):
                        match = " ".join(m for m in match if m)
                    match = match.strip()

                    if match and match.lower() not in seen:
                        seen.add(match.lower())
                        found.append({
                            "keyword": match,
                            "category": category,
                        })

        return found

    def parse_reddit_html(self, html: str, subreddit: str) -> list[RedditPost]:
        """
        Parse Reddit HTML to extract posts (basic parsing).

        Note: This is a simple parser for old.reddit.com HTML.
        For production, use the Reddit API.
        """
        posts = []

        # Find post entries (simplified pattern)
        post_pattern = r'<a[^>]*class="[^"]*title[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(post_pattern, html, re.IGNORECASE)

        for url, title in matches[:50]:  # Limit to 50 posts
            # Extract keywords from title
            keywords = self.extract_keywords_from_text(title)

            post = RedditPost(
                title=title.strip(),
                url=url if url.startswith("http") else f"https://reddit.com{url}",
                subreddit=subreddit,
                keywords_found=[k["keyword"] for k in keywords],
            )
            posts.append(post)

        return posts

    def generate_scan_plan(self) -> dict:
        """
        Generate a complete scan plan for all subreddits.

        Returns a dict with URLs and instructions for external fetching.
        """
        plan = {
            "generated_at": datetime.now().isoformat(),
            "target_subreddits": self.subreddits,
            "subreddit_urls": self.get_subreddit_urls(),
            "pattern_categories": list(self.AI_PATTERNS.keys()),
            "instructions": {
                "fetch_method": "Use WebFetch or requests to fetch each URL",
                "parse_method": "Pass HTML to parse_reddit_html() or extract_keywords_from_text()",
                "rate_limit": "Wait 2 seconds between requests to avoid rate limiting",
            },
        }

        return plan


# Convenience functions

def get_ai_subreddit_urls() -> list[str]:
    """Get list of AI-related subreddit URLs to scan."""
    scanner = RedditScanner()
    return [item["url"] for item in scanner.get_subreddit_urls()]


def extract_ai_keywords(text: str) -> list[str]:
    """Extract AI-related keywords from text."""
    scanner = RedditScanner()
    found = scanner.extract_keywords_from_text(text)
    return [k["keyword"] for k in found]


def generate_reddit_search_queries(keywords: list[str]) -> list[dict]:
    """Generate Reddit search queries for keywords."""
    scanner = RedditScanner()
    return scanner.get_search_urls(keywords)
