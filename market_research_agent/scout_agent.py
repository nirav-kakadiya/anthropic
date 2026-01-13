"""
Scout Agent - Unified orchestrator for complete market research.

Combines all modules:
- Reddit scanning (r/StableDiffusion, r/comfyui, r/generativeAI)
- Product Hunt launches
- Hacker News discussions
- AI model/tool detection
- Gap analysis vs your features
- Keyword clustering
- Trend scoring
- Scout V3-style output

Usage:
    agent = ScoutAgent(your_features=["flux ai", "kling ai", ...])
    report = agent.scan()
    print(report.format())
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json

from .reddit_scraper import RedditScanner, extract_ai_keywords
from .social_scrapers import ProductHuntScanner, HackerNewsScanner, SocialAggregator
from .ai_detector import AIDetector, detect_ai_items
from .gap_analyzer import GapAnalyzer, GapAnalysisReport
from .keyword_cluster import KeywordClusterer, KeywordCluster
from .trend_analyzer import TrendAnalyzer, TrendSignal, TrendScore
from .scout_formatter import ScoutFormatter


@dataclass
class ScanResult:
    """Complete scan result from all sources."""
    scan_id: str
    scan_time: str

    # Raw data
    reddit_posts: dict[str, list[dict]] = field(default_factory=dict)
    producthunt_launches: list[dict] = field(default_factory=list)
    hackernews_posts: list[dict] = field(default_factory=list)

    # Extracted keywords
    all_keywords: list[str] = field(default_factory=list)
    keyword_sources: dict[str, list[str]] = field(default_factory=dict)

    # Analysis results
    gap_report: Optional[GapAnalysisReport] = None
    clusters: list[KeywordCluster] = field(default_factory=list)
    trend_scores: list[TrendScore] = field(default_factory=list)

    # Summary
    total_keywords: int = 0
    total_gaps: int = 0
    total_covered: int = 0
    top_opportunities: list[dict] = field(default_factory=list)


class ScoutAgent:
    """
    Complete market research agent.

    Scans Reddit, Product Hunt, Hacker News for AI trends,
    compares against your features, and identifies gaps/opportunities.

    Usage:
        agent = ScoutAgent(
            your_features=["flux ai", "kling ai", "ai upscaler", ...],
            niche="AI image/video platform"
        )

        # Get scan plan (URLs to fetch)
        plan = agent.get_scan_plan()

        # After fetching, analyze results
        result = agent.analyze(fetched_data)

        # Or run full scan (generates URLs for external fetching)
        result = agent.scan()
    """

    def __init__(
        self,
        your_features: list[str],
        niche: str = "AI image/video/audio creation platform",
        subreddits: Optional[list[str]] = None
    ):
        self.your_features = [f.lower().strip() for f in your_features]
        self.niche = niche

        # Initialize components
        self.reddit_scanner = RedditScanner(subreddits=subreddits)
        self.ph_scanner = ProductHuntScanner()
        self.hn_scanner = HackerNewsScanner()
        self.ai_detector = AIDetector()
        self.gap_analyzer = GapAnalyzer(existing_features=your_features)
        self.clusterer = KeywordClusterer()
        self.trend_analyzer = TrendAnalyzer()
        self.formatter = ScoutFormatter(niche=niche)

        # State
        self.last_scan: Optional[ScanResult] = None

    def get_scan_plan(self) -> dict:
        """
        Get complete scan plan with all URLs to fetch.

        Returns dict with URLs organized by platform.
        """
        plan = {
            "generated_at": datetime.now().isoformat(),
            "niche": self.niche,
            "your_features_count": len(self.your_features),
            "platforms": {
                "reddit": {
                    "description": "AI-related subreddits",
                    "urls": self.reddit_scanner.get_subreddit_urls(),
                    "rate_limit": "2 seconds between requests",
                },
                "producthunt": {
                    "description": "AI tool launches",
                    "urls": (
                        self.ph_scanner.get_topic_urls() +
                        self.ph_scanner.get_daily_urls(7)
                    ),
                    "rate_limit": "1 second between requests",
                },
                "hackernews": {
                    "description": "Tech discussions (Algolia API)",
                    "urls": self.hn_scanner.get_popular_urls(),
                    "rate_limit": "No limit (API)",
                },
            },
            "instructions": """
            1. Fetch each URL using WebFetch or requests
            2. Pass HTML/JSON to agent.process_response(platform, data)
            3. After all fetches, call agent.analyze() for full report
            """
        }

        return plan

    def process_reddit_html(self, subreddit: str, html: str) -> list[dict]:
        """Process Reddit HTML and extract posts with keywords."""
        posts = self.reddit_scanner.parse_reddit_html(html, subreddit)

        result = []
        for post in posts:
            # Also run AI detector on title
            detected = detect_ai_items(post.title)
            all_keywords = list(set(post.keywords_found + detected))

            result.append({
                "title": post.title,
                "url": post.url,
                "subreddit": subreddit,
                "keywords_found": all_keywords,
            })

        return result

    def process_hn_json(self, json_data: dict) -> list[dict]:
        """Process Hacker News API response."""
        posts = self.hn_scanner.parse_algolia_response(json_data)

        result = []
        for post in posts:
            detected = detect_ai_items(post.title)
            result.append({
                "title": post.title,
                "url": post.url,
                "points": post.points,
                "comments": post.comments,
                "keywords_found": detected,
            })

        return result

    def analyze(
        self,
        reddit_data: Optional[dict[str, list[dict]]] = None,
        ph_data: Optional[list[dict]] = None,
        hn_data: Optional[list[dict]] = None
    ) -> ScanResult:
        """
        Analyze collected data and generate full report.

        Args:
            reddit_data: {subreddit: [{title, url, keywords_found}, ...]}
            ph_data: [{name, tagline, votes, keywords_found}, ...]
            hn_data: [{title, url, points, keywords_found}, ...]

        Returns:
            Complete ScanResult
        """
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = ScanResult(
            scan_id=scan_id,
            scan_time=datetime.now().isoformat(),
            reddit_posts=reddit_data or {},
            producthunt_launches=ph_data or [],
            hackernews_posts=hn_data or [],
        )

        # Collect all keywords with sources
        all_keywords = []
        keyword_sources = {}

        # From Reddit
        for subreddit, posts in result.reddit_posts.items():
            for post in posts:
                for kw in post.get("keywords_found", []):
                    if kw not in keyword_sources:
                        keyword_sources[kw] = []
                    keyword_sources[kw].append(f"Reddit r/{subreddit}")
                    if kw not in all_keywords:
                        all_keywords.append(kw)

        # From Product Hunt
        for launch in result.producthunt_launches:
            for kw in launch.get("keywords_found", []):
                if kw not in keyword_sources:
                    keyword_sources[kw] = []
                keyword_sources[kw].append("Product Hunt")
                if kw not in all_keywords:
                    all_keywords.append(kw)

        # From Hacker News
        for post in result.hackernews_posts:
            for kw in post.get("keywords_found", []):
                if kw not in keyword_sources:
                    keyword_sources[kw] = []
                keyword_sources[kw].append("Hacker News")
                if kw not in all_keywords:
                    all_keywords.append(kw)

        result.all_keywords = all_keywords
        result.keyword_sources = keyword_sources
        result.total_keywords = len(all_keywords)

        # Gap analysis
        discovered = [
            {
                "keyword": kw,
                "source_platform": ", ".join(keyword_sources.get(kw, [])[:2]),
                "trend_score": 80.0,
            }
            for kw in all_keywords
        ]
        result.gap_report = self.gap_analyzer.analyze(discovered)
        result.total_gaps = result.gap_report.total_gaps
        result.total_covered = result.gap_report.total_covered

        # Cluster keywords
        keyword_data = [
            {
                "keyword": kw,
                "score": 80,
                "source": ", ".join(keyword_sources.get(kw, [])),
            }
            for kw in all_keywords
        ]
        result.clusters = self.clusterer.cluster(keyword_data)

        # Generate trend scores
        keyword_signals = {}
        for kw in all_keywords[:50]:
            sources = keyword_sources.get(kw, [])
            signals = []

            for source in sources:
                if "Reddit" in source:
                    signals.append(TrendSignal(
                        keyword=kw,
                        source="reddit",
                        score=80,
                        timestamp=datetime.now().isoformat(),
                    ))
                elif "Product Hunt" in source:
                    signals.append(TrendSignal(
                        keyword=kw,
                        source="producthunt",
                        score=75,
                        timestamp=datetime.now().isoformat(),
                    ))
                elif "Hacker News" in source:
                    signals.append(TrendSignal(
                        keyword=kw,
                        source="hackernews",
                        score=70,
                        timestamp=datetime.now().isoformat(),
                    ))

            if signals:
                keyword_signals[kw] = signals

        result.trend_scores = self.trend_analyzer.rank_keywords(keyword_signals)

        # Top opportunities (gaps with high trend scores)
        gap_keywords = {g.keyword.lower() for g in result.gap_report.gaps}
        for score in result.trend_scores[:20]:
            if score.keyword.lower() in gap_keywords:
                result.top_opportunities.append({
                    "keyword": score.keyword,
                    "trend_score": score.composite_score,
                    "direction": score.trend_direction,
                    "recommendation": score.recommendation,
                })

        self.last_scan = result
        return result

    def format_report(self, result: Optional[ScanResult] = None) -> str:
        """Format scan result as Scout V3-style report."""
        result = result or self.last_scan
        if not result:
            return "No scan results available. Run analyze() first."

        lines = []

        # Header
        lines.append("🔍 Scout Agent Report")
        lines.append(f"— {result.scan_time}")
        lines.append("")

        # Summary
        lines.append("=" * 60)
        lines.append("📊 SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Total Keywords Found: {result.total_keywords}")
        lines.append(f"Gaps (not in your features): {result.total_gaps}")
        lines.append(f"Already Covered: {result.total_covered}")
        lines.append(f"Clusters Identified: {len(result.clusters)}")
        lines.append("")

        # Reddit results
        if result.reddit_posts:
            lines.append("-" * 40)
            lines.append("📱 REDDIT FINDINGS")
            lines.append("-" * 40)
            for sub, posts in result.reddit_posts.items():
                kw_count = sum(len(p.get("keywords_found", [])) for p in posts)
                lines.append(f"\nr/{sub} ({kw_count} keywords from {len(posts)} posts):")
                for post in posts[:5]:
                    keywords = post.get("keywords_found", [])
                    if keywords:
                        lines.append(f"  • {post.get('url', '')[:60]}...")
                        lines.append(f"    Found: {', '.join(keywords[:5])}")

        # Top gaps
        if result.gap_report and result.gap_report.gaps:
            lines.append("")
            lines.append("-" * 40)
            lines.append("🔥 TOP GAPS")
            lines.append("-" * 40)
            for gap in result.gap_report.gaps[:15]:
                lines.append(f"\n🔥 {gap.keyword}")
                lines.append(f"   Trend: {gap.trend_score}%")
                lines.append(f"   Source: {gap.source_platform}")
                lines.append(f"   Why: {gap.why_gap[:80]}...")

        # Top opportunities
        if result.top_opportunities:
            lines.append("")
            lines.append("-" * 40)
            lines.append("⚡ TOP OPPORTUNITIES (Gaps + High Trends)")
            lines.append("-" * 40)
            for opp in result.top_opportunities[:10]:
                lines.append(f"\n{opp['keyword']}")
                lines.append(f"   Score: {opp['trend_score']:.0f}% {opp['direction']}")
                lines.append(f"   → {opp['recommendation']}")

        # Clusters
        if result.clusters:
            lines.append("")
            lines.append("-" * 40)
            lines.append("🎯 KEYWORD CLUSTERS")
            lines.append("-" * 40)
            for cluster in result.clusters[:10]:
                lines.append(f"\n{cluster.name} ({len(cluster.keywords)} keywords)")
                lines.append(f"   Keywords: {', '.join(cluster.keywords[:4])}")

        return "\n".join(lines)

    def export_json(self, result: Optional[ScanResult] = None) -> str:
        """Export scan result as JSON."""
        result = result or self.last_scan
        if not result:
            return "{}"

        export = {
            "scan_id": result.scan_id,
            "scan_time": result.scan_time,
            "niche": self.niche,
            "summary": {
                "total_keywords": result.total_keywords,
                "total_gaps": result.total_gaps,
                "total_covered": result.total_covered,
            },
            "keywords": result.all_keywords,
            "gaps": [
                {
                    "keyword": g.keyword,
                    "trend_score": g.trend_score,
                    "source": g.source_platform,
                    "why_gap": g.why_gap,
                }
                for g in (result.gap_report.gaps if result.gap_report else [])
            ],
            "top_opportunities": result.top_opportunities,
            "clusters": [
                {
                    "name": c.name,
                    "keywords": c.keywords,
                    "avg_score": c.avg_score,
                }
                for c in result.clusters
            ],
        }

        return json.dumps(export, indent=2)


def create_scout_agent(features: list[str], niche: str = "") -> ScoutAgent:
    """Factory function to create a Scout Agent."""
    return ScoutAgent(
        your_features=features,
        niche=niche or "AI image/video/audio creation platform"
    )


# =============================================================================
# AUTO MODE - Automatically detect features and niche from URL
# =============================================================================

from .site_analyzer import SiteAnalyzer, SiteStructure
from .feature_extractor import FeatureExtractor, extract_features_from_html
from .niche_detector import NicheDetector, NicheResult


@dataclass
class AutoScanConfig:
    """Configuration for auto scanning."""
    url: str
    mode: str = "auto"  # "auto" or "manual"

    # Auto-detected (populated after site analysis)
    detected_features: list[str] = field(default_factory=list)
    detected_niche: str = ""
    niche_confidence: float = 0.0

    # Manual overrides (optional)
    manual_features: list[str] = field(default_factory=list)
    manual_niche: str = ""

    # Final values (auto + manual merged)
    final_features: list[str] = field(default_factory=list)
    final_niche: str = ""


class AutoScoutAgent:
    """
    Scout Agent with AUTO MODE.

    Two modes:
    1. AUTO: Provide URL -> crawls sitemap/site -> extracts features -> detects niche -> runs gap analysis
    2. MANUAL: Provide features + niche directly -> runs gap analysis

    Usage (Auto Mode):
        agent = AutoScoutAgent.from_url("https://example.com")

        # Step 1: Get URLs to crawl
        urls = agent.get_site_urls()

        # Step 2: Feed HTML content
        agent.process_page("home", html)
        agent.process_page("features", html)

        # Step 3: Auto-detect features and niche
        config = agent.auto_detect()
        print(f"Detected niche: {config.detected_niche}")
        print(f"Detected features: {config.detected_features}")

        # Step 4 (optional): Add manual features
        agent.add_manual_features(["custom feature 1", "custom feature 2"])

        # Step 5: Run market research
        result = agent.run_research()

    Usage (Manual Mode):
        agent = AutoScoutAgent.manual(
            features=["flux ai", "kling ai", "ai upscaler"],
            niche="AI image/video platform"
        )
        result = agent.run_research()
    """

    def __init__(self, url: Optional[str] = None, mode: str = "auto"):
        self.mode = mode
        self.url = url

        # Site analysis components
        self.site_analyzer: Optional[SiteAnalyzer] = None
        self.feature_extractor = FeatureExtractor()
        self.niche_detector = NicheDetector()

        # Config
        self.config = AutoScanConfig(url=url or "", mode=mode)

        # Page content storage
        self.page_content: dict[str, str] = {}

        # Scout agent (created after detection)
        self._scout_agent: Optional[ScoutAgent] = None

        # Initialize site analyzer if URL provided
        if url:
            self.site_analyzer = SiteAnalyzer(url)

    @classmethod
    def from_url(cls, url: str) -> "AutoScoutAgent":
        """Create AutoScoutAgent in AUTO mode from URL."""
        return cls(url=url, mode="auto")

    @classmethod
    def manual(cls, features: list[str], niche: str) -> "AutoScoutAgent":
        """Create AutoScoutAgent in MANUAL mode."""
        agent = cls(mode="manual")
        agent.config.manual_features = features
        agent.config.manual_niche = niche
        agent.config.final_features = features
        agent.config.final_niche = niche
        return agent

    def get_site_urls(self) -> dict:
        """
        Get URLs to fetch for site analysis.

        Returns dict with categorized URLs:
        - robots_txt: URL for robots.txt
        - sitemap: URL for sitemap.xml
        - pages: List of {url, type, priority} for key pages
        """
        if not self.site_analyzer:
            return {"error": "No URL provided. Use from_url() or provide URL."}

        urls = self.site_analyzer.get_urls_to_fetch()
        return {
            "base_url": self.site_analyzer.base_url,
            "robots_txt": urls["robots_txt"],
            "sitemap": urls["sitemap"],
            "pages": [
                {"url": urls["homepage"], "type": "home", "priority": 1.0},
                {"url": urls["key_pages"]["features"], "type": "features", "priority": 0.9},
                {"url": urls["key_pages"]["pricing"], "type": "pricing", "priority": 0.8},
                {"url": urls["key_pages"]["about"], "type": "about", "priority": 0.7},
            ],
            "instructions": """
            1. Fetch robots.txt and pass to process_robots_txt()
            2. Fetch sitemap.xml and pass to process_sitemap()
            3. Fetch each page and pass to process_page(type, html)
            4. Call auto_detect() to get detected features/niche
            5. Optionally add_manual_features() for custom additions
            6. Call run_research() for gap analysis
            """
        }

    def process_robots_txt(self, content: str) -> list[str]:
        """Process robots.txt to find additional sitemaps."""
        if self.site_analyzer:
            return self.site_analyzer.parse_robots_txt(content)
        return []

    def process_sitemap(self, xml_content: str) -> int:
        """Process sitemap.xml. Returns number of URLs found."""
        if self.site_analyzer:
            entries = self.site_analyzer.parse_sitemap_xml(xml_content)
            return len(entries)
        return 0

    def process_page(self, page_type: str, html: str):
        """
        Process page HTML for feature extraction.

        Args:
            page_type: "home", "features", "pricing", "about"
            html: Raw HTML content
        """
        self.page_content[page_type] = html

        # Update site analyzer
        if self.site_analyzer:
            self.site_analyzer.process_page_html(page_type, html)

        # Extract features based on page type
        if page_type == "features":
            self.feature_extractor.extract_from_features_page(html)
        elif page_type == "pricing":
            self.feature_extractor.extract_from_pricing_page(html)
        else:
            self.feature_extractor.extract_from_html(html, page_type)

    def auto_detect(self) -> AutoScanConfig:
        """
        Run auto-detection of features and niche.

        Returns AutoScanConfig with detected values.
        """
        if self.mode != "auto":
            return self.config

        # Get detected features
        feature_result = self.feature_extractor.get_result()
        self.config.detected_features = feature_result.feature_names[:50]

        # Get site structure for niche detection
        structure = None
        if self.site_analyzer:
            structure = self.site_analyzer.get_structure()

        # Detect niche
        niche_result = self.niche_detector.detect(
            homepage_text=self.page_content.get("home", ""),
            features_text=self.page_content.get("features", ""),
            pricing_text=self.page_content.get("pricing", ""),
            about_text=self.page_content.get("about", ""),
            site_title=structure.site_title if structure else "",
            site_description=structure.site_description if structure else ""
        )

        self.config.detected_niche = niche_result.primary_niche
        self.config.niche_confidence = niche_result.confidence

        # Merge with manual overrides
        self._merge_config()

        return self.config

    def add_manual_features(self, features: list[str]):
        """Add manual features to supplement auto-detected ones."""
        self.config.manual_features.extend(features)
        self._merge_config()

    def set_manual_niche(self, niche: str):
        """Override or set the niche manually."""
        self.config.manual_niche = niche
        self._merge_config()

    def _merge_config(self):
        """Merge auto-detected and manual values."""
        # Combine features (manual takes precedence)
        all_features = list(self.config.manual_features)
        for f in self.config.detected_features:
            if f.lower() not in [m.lower() for m in all_features]:
                all_features.append(f)
        self.config.final_features = all_features

        # Niche: manual overrides auto
        self.config.final_niche = (
            self.config.manual_niche or
            self.config.detected_niche or
            "Unknown niche"
        )

    def get_scout_agent(self) -> ScoutAgent:
        """Get the underlying ScoutAgent with detected/manual config."""
        if not self._scout_agent:
            if not self.config.final_features:
                self._merge_config()

            self._scout_agent = ScoutAgent(
                your_features=self.config.final_features,
                niche=self.config.final_niche
            )

        return self._scout_agent

    def get_research_plan(self) -> dict:
        """Get the research plan (URLs to fetch for gap analysis)."""
        agent = self.get_scout_agent()
        return agent.get_scan_plan()

    def run_research(
        self,
        reddit_data: Optional[dict[str, list[dict]]] = None,
        ph_data: Optional[list[dict]] = None,
        hn_data: Optional[list[dict]] = None
    ) -> ScanResult:
        """
        Run the market research analysis.

        Args:
            reddit_data: Reddit posts data (optional)
            ph_data: Product Hunt data (optional)
            hn_data: Hacker News data (optional)

        Returns:
            Complete ScanResult
        """
        agent = self.get_scout_agent()
        return agent.analyze(reddit_data, ph_data, hn_data)

    def format_report(self) -> str:
        """Format the research report."""
        agent = self.get_scout_agent()
        return agent.format_report()

    def get_config_summary(self) -> str:
        """Get summary of current configuration."""
        lines = [
            "=" * 60,
            f"AutoScoutAgent Configuration",
            "=" * 60,
            f"Mode: {self.mode.upper()}",
            f"URL: {self.url or 'N/A'}",
            "",
            f"Detected Niche: {self.config.detected_niche or 'Not detected'}",
            f"Niche Confidence: {self.config.niche_confidence:.0%}",
            f"Detected Features: {len(self.config.detected_features)}",
            "",
            f"Manual Niche: {self.config.manual_niche or 'Not set'}",
            f"Manual Features: {len(self.config.manual_features)}",
            "",
            "Final Configuration:",
            f"  Niche: {self.config.final_niche}",
            f"  Features: {len(self.config.final_features)}",
        ]

        if self.config.final_features:
            lines.append("")
            lines.append("Top Features:")
            for f in self.config.final_features[:10]:
                lines.append(f"  • {f}")

        return "\n".join(lines)


def create_auto_scout(url: str) -> AutoScoutAgent:
    """Create an AutoScoutAgent in auto mode."""
    return AutoScoutAgent.from_url(url)


def create_manual_scout(features: list[str], niche: str) -> AutoScoutAgent:
    """Create an AutoScoutAgent in manual mode."""
    return AutoScoutAgent.manual(features, niche)
