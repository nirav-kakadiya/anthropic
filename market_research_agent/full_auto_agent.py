"""
Full Auto Agent - One URL, complete market research.

ZERO MANUAL INPUT REQUIRED!

Just provide a URL and get:
1. Auto-detected features from your site
2. Auto-detected niche/industry
3. Live Reddit/PH/HN keyword scraping
4. Keyword ranking with trend scores
5. Gap analysis
6. Instant action plan with priorities

Usage:
    agent = FullAutoAgent("https://your-site.com")
    result = await agent.run()  # Does EVERYTHING
    print(result.action_plan)
"""

import asyncio
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


@dataclass
class RankedKeyword:
    """A keyword with ranking data."""
    keyword: str
    rank_score: float  # 0-100, higher = more important
    trend_direction: str  # "rising", "stable", "falling"
    sources: list[str] = field(default_factory=list)
    mention_count: int = 0
    first_seen: str = ""
    is_gap: bool = False  # You don't have this
    priority: str = "medium"  # "critical", "high", "medium", "low"
    action: str = ""  # Recommended action


@dataclass
class ActionItem:
    """Single action to take."""
    priority: int  # 1 = highest
    action: str
    keyword: str
    reason: str
    effort: str  # "low", "medium", "high"
    impact: str  # "low", "medium", "high"
    timeline: str  # "immediate", "this_week", "this_month"


@dataclass
class FullAutoResult:
    """Complete auto-scan result."""
    scan_id: str
    scan_time: str
    url: str

    # Auto-detected
    detected_niche: str = ""
    detected_features: list[str] = field(default_factory=list)

    # Keywords with rankings
    all_keywords: list[RankedKeyword] = field(default_factory=list)
    trending_keywords: list[RankedKeyword] = field(default_factory=list)
    gap_keywords: list[RankedKeyword] = field(default_factory=list)

    # Action plan
    action_items: list[ActionItem] = field(default_factory=list)
    action_plan_text: str = ""

    # Stats
    total_keywords: int = 0
    total_gaps: int = 0
    pages_crawled: int = 0
    sources_scraped: list[str] = field(default_factory=list)


class FullAutoAgent:
    """
    Fully automatic market research agent.

    Just give URL → get complete analysis + action plan.

    Usage:
        # Async
        agent = FullAutoAgent("https://your-site.com")
        result = await agent.run()

        # Sync
        result = agent.run_sync()

        # Get action plan
        print(result.action_plan_text)
    """

    # Subreddits to scrape based on detected niche
    NICHE_SUBREDDITS = {
        "ai_image": [
            "StableDiffusion", "comfyui", "midjourney", "dalle",
            "AIArt", "generativeAI", "sdforall"
        ],
        "ai_video": [
            "aivideo", "runwayml", "generativeAI", "StableDiffusion",
            "videography", "AfterEffects"
        ],
        "ai_audio": [
            "elevenlabs", "AI_VoiceActing", "audioengineering",
            "podcasting", "musicproduction"
        ],
        "ai_writing": [
            "ChatGPT", "ClaudeAI", "LocalLLaMA", "artificial",
            "OpenAI", "PromptEngineering"
        ],
        "saas": [
            "SaaS", "startups", "EntrepreneurRideAlong", "indiehackers",
            "Entrepreneur", "microsaas"
        ],
        "default": [
            "startups", "SaaS", "technology", "programming",
            "webdev", "artificial"
        ]
    }

    # Keywords that indicate high priority
    PRIORITY_SIGNALS = {
        "critical": ["launch", "new", "just released", "breaking", "announced"],
        "high": ["trending", "popular", "viral", "everyone", "best"],
        "medium": ["update", "version", "feature", "improved"],
    }

    def __init__(self, url: str, niche_hint: str = ""):
        self.url = url
        self.niche_hint = niche_hint
        self.base_url = self._get_base_url(url)

        # Import dependencies
        from .live_fetcher import LiveFetcher
        from .site_analyzer import SiteAnalyzer
        from .feature_extractor import FeatureExtractor
        from .niche_detector import NicheDetector
        from .ai_detector import AIDetector
        from .gap_analyzer import GapAnalyzer

        self.fetcher = LiveFetcher(cache_ttl_minutes=30)
        self.site_analyzer = SiteAnalyzer(url)
        self.feature_extractor = FeatureExtractor()
        self.niche_detector = NicheDetector()
        self.ai_detector = AIDetector()

        # Results
        self.result: Optional[FullAutoResult] = None
        self._detected_niche_key = "default"

    def _get_base_url(self, url: str) -> str:
        """Extract base URL."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def run(self) -> FullAutoResult:
        """
        Run complete auto analysis.

        1. Crawl your site
        2. Detect features & niche
        3. Scrape Reddit/PH/HN
        4. Extract & rank keywords
        5. Find gaps
        6. Generate action plan
        """
        scan_id = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.result = FullAutoResult(
            scan_id=scan_id,
            scan_time=datetime.now().isoformat(),
            url=self.url,
        )

        # Step 1: Crawl your site
        print("🔍 Step 1/5: Analyzing your site...")
        await self._analyze_site()

        # Step 2: Detect niche and features
        print("🎯 Step 2/5: Detecting niche & features...")
        self._detect_niche_and_features()

        # Step 3: Scrape trend sources
        print("📡 Step 3/5: Scraping Reddit, Product Hunt, Hacker News...")
        await self._scrape_trend_sources()

        # Step 4: Rank keywords
        print("📊 Step 4/5: Ranking keywords...")
        self._rank_keywords()

        # Step 5: Generate action plan
        print("📋 Step 5/5: Generating action plan...")
        self._generate_action_plan()

        print("✅ Complete!")

        return self.result

    async def _analyze_site(self):
        """Crawl and analyze the target site."""
        pages_to_fetch = [
            (self.base_url, "home"),
            (f"{self.base_url}/features", "features"),
            (f"{self.base_url}/pricing", "pricing"),
            (f"{self.base_url}/about", "about"),
            (f"{self.base_url}/products", "products"),
            (f"{self.base_url}/solutions", "solutions"),
        ]

        for url, page_type in pages_to_fetch:
            result = await self.fetcher.fetch(url)
            if result.status_code == 200:
                self.site_analyzer.process_page_html(page_type, result.content)
                self.feature_extractor.extract_from_html(result.content, page_type)
                self.result.pages_crawled += 1

    def _detect_niche_and_features(self):
        """Detect niche and extract features."""
        # Get features
        feature_result = self.feature_extractor.get_result()
        self.result.detected_features = feature_result.feature_names[:100]

        # Get niche
        structure = self.site_analyzer.get_structure()
        niche_result = self.niche_detector.detect(
            homepage_text=structure.homepage_content,
            features_text=structure.features_content,
            site_title=structure.site_title,
            site_description=structure.site_description,
        )
        self.result.detected_niche = niche_result.primary_niche

        # Map to subreddit category
        niche_lower = niche_result.primary_niche.lower()
        if "image" in niche_lower or "photo" in niche_lower:
            self._detected_niche_key = "ai_image"
        elif "video" in niche_lower:
            self._detected_niche_key = "ai_video"
        elif "audio" in niche_lower or "voice" in niche_lower:
            self._detected_niche_key = "ai_audio"
        elif "writing" in niche_lower or "text" in niche_lower:
            self._detected_niche_key = "ai_writing"
        elif "saas" in niche_lower:
            self._detected_niche_key = "saas"
        else:
            self._detected_niche_key = "default"

    async def _scrape_trend_sources(self):
        """Scrape Reddit, Product Hunt, Hacker News for trends."""
        all_keywords = {}

        # Get relevant subreddits
        subreddits = self.NICHE_SUBREDDITS.get(
            self._detected_niche_key,
            self.NICHE_SUBREDDITS["default"]
        )

        # Scrape Reddit
        for subreddit in subreddits[:5]:  # Limit to 5 subreddits
            url = f"https://old.reddit.com/r/{subreddit}/hot/.json"
            result = await self.fetcher.fetch(url)

            if result.status_code == 200:
                self.result.sources_scraped.append(f"r/{subreddit}")
                keywords = self._extract_keywords_from_reddit(result.content, subreddit)
                for kw, data in keywords.items():
                    if kw in all_keywords:
                        all_keywords[kw]["count"] += data["count"]
                        all_keywords[kw]["sources"].append(data["source"])
                    else:
                        all_keywords[kw] = data

        # Scrape Hacker News (Algolia API)
        hn_queries = ["AI", "startup", "saas", "machine learning"]
        for query in hn_queries[:2]:
            url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&hitsPerPage=30"
            result = await self.fetcher.fetch(url)

            if result.status_code == 200:
                self.result.sources_scraped.append("Hacker News")
                keywords = self._extract_keywords_from_hn(result.content)
                for kw, data in keywords.items():
                    if kw in all_keywords:
                        all_keywords[kw]["count"] += data["count"]
                        all_keywords[kw]["sources"].append(data["source"])
                    else:
                        all_keywords[kw] = data

        # Convert to RankedKeyword objects
        for kw, data in all_keywords.items():
            ranked = RankedKeyword(
                keyword=kw,
                rank_score=0,  # Will be calculated
                trend_direction="stable",
                sources=list(set(data.get("sources", []))),
                mention_count=data.get("count", 1),
                first_seen=datetime.now().isoformat(),
            )
            self.result.all_keywords.append(ranked)

        self.result.total_keywords = len(self.result.all_keywords)

    def _extract_keywords_from_reddit(self, json_content: str, subreddit: str) -> dict:
        """Extract keywords from Reddit JSON."""
        keywords = {}

        try:
            import json
            data = json.loads(json_content)
            posts = data.get("data", {}).get("children", [])

            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "")

                # Use AI detector
                detected = self.ai_detector.detect(title)
                for item in detected:
                    kw = item.name.lower()
                    if kw not in keywords:
                        keywords[kw] = {"count": 0, "sources": [], "source": f"r/{subreddit}"}
                    keywords[kw]["count"] += 1
                    keywords[kw]["sources"].append(f"r/{subreddit}")

                # Extract other significant words
                words = self._extract_significant_words(title)
                for word in words:
                    if word not in keywords:
                        keywords[word] = {"count": 0, "sources": [], "source": f"r/{subreddit}"}
                    keywords[word]["count"] += 1
                    keywords[word]["sources"].append(f"r/{subreddit}")

        except Exception:
            pass

        return keywords

    def _extract_keywords_from_hn(self, json_content: str) -> dict:
        """Extract keywords from Hacker News Algolia API."""
        keywords = {}

        try:
            import json
            data = json.loads(json_content)
            hits = data.get("hits", [])

            for hit in hits:
                title = hit.get("title", "")

                # Use AI detector
                detected = self.ai_detector.detect(title)
                for item in detected:
                    kw = item.name.lower()
                    if kw not in keywords:
                        keywords[kw] = {"count": 0, "sources": [], "source": "Hacker News"}
                    keywords[kw]["count"] += 1
                    keywords[kw]["sources"].append("Hacker News")

                # Extract significant words
                words = self._extract_significant_words(title)
                for word in words:
                    if word not in keywords:
                        keywords[word] = {"count": 0, "sources": [], "source": "Hacker News"}
                    keywords[word]["count"] += 1
                    keywords[word]["sources"].append("Hacker News")

        except Exception:
            pass

        return keywords

    def _extract_significant_words(self, text: str) -> list[str]:
        """Extract significant words/phrases from text."""
        # Common words to skip
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "be", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "shall", "can", "need",
            "this", "that", "these", "those", "i", "you", "he", "she", "it",
            "we", "they", "what", "which", "who", "whom", "whose", "where",
            "when", "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "not", "only", "own", "same",
            "so", "than", "too", "very", "just", "also", "now", "here", "there",
            "about", "after", "before", "between", "into", "through", "during",
            "my", "your", "his", "her", "its", "our", "their", "any", "new"
        }

        # Extract words (2+ chars)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter and return significant words
        significant = []
        for word in words:
            if word not in stop_words and len(word) >= 4:
                significant.append(word)

        # Also look for compound terms
        compounds = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        significant.extend([c.lower() for c in compounds])

        return significant[:10]  # Limit per text

    def _rank_keywords(self):
        """Rank keywords by importance and identify gaps."""
        features_lower = [f.lower() for f in self.result.detected_features]

        for kw in self.result.all_keywords:
            # Base score from mention count
            base_score = min(100, kw.mention_count * 15)

            # Boost for multiple sources
            source_boost = len(set(kw.sources)) * 10

            # Check if it's a gap (not in your features)
            kw.is_gap = not any(
                kw.keyword in f or f in kw.keyword
                for f in features_lower
            )

            # Gap boost (opportunities are more valuable)
            gap_boost = 20 if kw.is_gap else 0

            # Calculate final score
            kw.rank_score = min(100, base_score + source_boost + gap_boost)

            # Determine priority
            if kw.rank_score >= 80:
                kw.priority = "critical"
            elif kw.rank_score >= 60:
                kw.priority = "high"
            elif kw.rank_score >= 40:
                kw.priority = "medium"
            else:
                kw.priority = "low"

            # Determine trend direction (simplified)
            if kw.mention_count >= 5:
                kw.trend_direction = "rising"
            elif kw.mention_count >= 2:
                kw.trend_direction = "stable"
            else:
                kw.trend_direction = "emerging"

        # Sort by rank score
        self.result.all_keywords.sort(key=lambda x: x.rank_score, reverse=True)

        # Separate trending and gaps
        self.result.trending_keywords = [
            kw for kw in self.result.all_keywords
            if kw.rank_score >= 50
        ][:20]

        self.result.gap_keywords = [
            kw for kw in self.result.all_keywords
            if kw.is_gap and kw.rank_score >= 30
        ][:30]

        self.result.total_gaps = len(self.result.gap_keywords)

    def _generate_action_plan(self):
        """Generate prioritized action plan."""
        actions = []
        priority_counter = 1

        # Critical gaps (high score + is gap)
        for kw in self.result.gap_keywords[:5]:
            if kw.priority in ["critical", "high"]:
                actions.append(ActionItem(
                    priority=priority_counter,
                    action=f"Add {kw.keyword} support",
                    keyword=kw.keyword,
                    reason=f"Trending ({kw.rank_score:.0f}% score) across {len(set(kw.sources))} sources, you don't have it",
                    effort="medium",
                    impact="high",
                    timeline="this_week"
                ))
                priority_counter += 1

        # Quick wins (high trend, low effort features)
        for kw in self.result.gap_keywords[5:15]:
            if kw.rank_score >= 40:
                actions.append(ActionItem(
                    priority=priority_counter,
                    action=f"Consider adding {kw.keyword}",
                    keyword=kw.keyword,
                    reason=f"Growing demand ({kw.mention_count} mentions)",
                    effort="low" if len(kw.keyword) < 15 else "medium",
                    impact="medium",
                    timeline="this_month"
                ))
                priority_counter += 1

        # Monitor list
        for kw in self.result.trending_keywords[:10]:
            if not kw.is_gap:
                actions.append(ActionItem(
                    priority=priority_counter,
                    action=f"Monitor {kw.keyword} trends",
                    keyword=kw.keyword,
                    reason=f"You have this, staying competitive",
                    effort="low",
                    impact="medium",
                    timeline="ongoing"
                ))
                priority_counter += 1

        self.result.action_items = actions[:20]

        # Generate text summary
        self.result.action_plan_text = self._format_action_plan()

    def _format_action_plan(self) -> str:
        """Format action plan as readable text."""
        lines = [
            "=" * 70,
            "🚀 INSTANT ACTION PLAN",
            "=" * 70,
            f"Site: {self.url}",
            f"Niche: {self.result.detected_niche}",
            f"Generated: {self.result.scan_time}",
            "",
            f"📊 Found {self.result.total_keywords} keywords, {self.result.total_gaps} gaps",
            f"📡 Scraped: {', '.join(self.result.sources_scraped[:5])}",
            "",
            "-" * 40,
            "🔥 IMMEDIATE ACTIONS (This Week)",
            "-" * 40,
        ]

        immediate = [a for a in self.result.action_items if a.timeline == "this_week"]
        for i, action in enumerate(immediate[:5], 1):
            lines.append(f"\n{i}. {action.action}")
            lines.append(f"   Why: {action.reason}")
            lines.append(f"   Impact: {action.impact.upper()} | Effort: {action.effort}")

        lines.append("")
        lines.append("-" * 40)
        lines.append("📅 PLAN THIS MONTH")
        lines.append("-" * 40)

        monthly = [a for a in self.result.action_items if a.timeline == "this_month"]
        for i, action in enumerate(monthly[:5], 1):
            lines.append(f"\n{i}. {action.action}")
            lines.append(f"   Why: {action.reason}")

        lines.append("")
        lines.append("-" * 40)
        lines.append("👀 TOP TRENDING KEYWORDS")
        lines.append("-" * 40)

        for kw in self.result.trending_keywords[:10]:
            status = "✅ You have" if not kw.is_gap else "❌ GAP"
            lines.append(f"  • {kw.keyword} ({kw.rank_score:.0f}%) {kw.trend_direction} {status}")

        lines.append("")
        lines.append("-" * 40)
        lines.append("🎯 TOP GAPS TO FILL")
        lines.append("-" * 40)

        for kw in self.result.gap_keywords[:10]:
            lines.append(f"  • {kw.keyword} - {kw.rank_score:.0f}% priority")
            lines.append(f"    Sources: {', '.join(set(kw.sources))[:50]}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def run_sync(self) -> FullAutoResult:
        """Synchronous wrapper for run()."""
        return asyncio.run(self.run())

    def get_action_plan(self) -> str:
        """Get the action plan text."""
        if self.result:
            return self.result.action_plan_text
        return "Run the agent first with run() or run_sync()"

    def export_keywords_csv(self) -> str:
        """Export keywords as CSV."""
        if not self.result:
            return ""

        lines = ["keyword,rank_score,trend,is_gap,priority,sources"]
        for kw in self.result.all_keywords:
            sources = "|".join(set(kw.sources))[:50]
            lines.append(f'"{kw.keyword}",{kw.rank_score:.1f},{kw.trend_direction},{kw.is_gap},{kw.priority},"{sources}"')

        return "\n".join(lines)


def create_full_auto_agent(url: str) -> FullAutoAgent:
    """Create a FullAutoAgent."""
    return FullAutoAgent(url)


async def quick_scan(url: str) -> FullAutoResult:
    """Quick scan - one line to get everything."""
    agent = FullAutoAgent(url)
    return await agent.run()


def quick_scan_sync(url: str) -> FullAutoResult:
    """Quick scan synchronous version."""
    return asyncio.run(quick_scan(url))
