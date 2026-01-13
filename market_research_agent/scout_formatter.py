"""
Scout-style Output Formatter - Matches Scout V3/Tensor Scope output format.

Produces output in sections:
1. Scout scan results (keywords from Reddit)
2. Features breakdown (technologies, use cases, filters)
3. Sources (Reddit posts with found keywords)
4. Gaps with "Why it's a gap" explanations
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ScoutResult:
    """Complete Scout-style analysis result."""
    scan_date: str = field(default_factory=lambda: datetime.now().strftime("%d-%m-%Y %I:%M %p"))
    total_keywords: int = 0
    niche: str = ""
    features: list[str] = field(default_factory=list)
    technologies: list[str] = field(default_factory=list)
    use_cases: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    sources: list[dict] = field(default_factory=list)
    gaps: list[dict] = field(default_factory=list)


class ScoutFormatter:
    """
    Formats output in Scout V3/Tensor Scope style.

    Usage:
        formatter = ScoutFormatter(niche="AI image/video platform")
        output = formatter.format_full_report(...)
    """

    def __init__(self, niche: str = "AI image/video/audio creation platform"):
        self.niche = niche

    def format_scout_header(self, scan_num: int = 1, total_scans: int = 1) -> str:
        """Format the Scout header."""
        timestamp = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        return f"🔍 Scout V3 ({scan_num}/{total_scans})\n— {timestamp}"

    def format_reddit_results(
        self,
        subreddit_results: dict[str, list[dict]]
    ) -> str:
        """
        Format Reddit scraping results.

        Args:
            subreddit_results: Dict mapping subreddit -> list of posts
                Each post: {url, title, keywords_found}
        """
        lines = []
        total_keywords = sum(
            len(post.get("keywords_found", []))
            for posts in subreddit_results.values()
            for post in posts
        )

        lines.append(f"🔍 {total_keywords} Keywords (from scraped content)")
        lines.append("")

        for subreddit, posts in subreddit_results.items():
            sub_keywords = sum(len(p.get("keywords_found", [])) for p in posts)
            lines.append(f"Reddit r/{subreddit} ({sub_keywords}):")

            for post in posts[:10]:  # Limit to 10 posts per subreddit
                url = post.get("url", "")
                keywords = post.get("keywords_found", [])
                if keywords:
                    lines.append(f"• {url}")
                    lines.append(f"Found: {', '.join(keywords[:7])}")

            lines.append("")

        return "\n".join(lines)

    def format_features_section(
        self,
        features: list[str],
        technologies: list[str],
        use_cases: list[str],
        filters: list[str] = None
    ) -> str:
        """Format the features breakdown section."""
        lines = []

        total = len(features)
        lines.append(f"📦 Your Features (Part 1)")
        lines.append(f"🎯 Your Niche: {self.niche}")
        lines.append("")
        lines.append(f"✨ Features ({total} total):")

        for feature in features[:50]:
            lines.append(feature)

        lines.append("")
        lines.append("📦 Your Features (Part 2)")

        if technologies:
            lines.append(f"🤖 Technologies ({len(technologies)} total):")
            for tech in technologies:
                lines.append(f"• {tech}")

        lines.append("")

        if use_cases:
            lines.append(f"💡 Use Cases ({len(use_cases)} total):")
            for uc in use_cases:
                lines.append(f"• {uc}")

        if filters:
            lines.append("")
            lines.append(f"🎨 Filters ({len(filters)} total):")
            for f in filters[:20]:
                lines.append(f"• {f}")

        return "\n".join(lines)

    def format_sources_section(self, sources: list[dict]) -> str:
        """
        Format the sources section.

        Args:
            sources: List of dicts with keys:
                - subreddit, url, keywords_found
        """
        lines = []
        lines.append("📊 Sources")
        lines.append("📚 Scout Analyzed:")
        lines.append("")

        for source in sources[:20]:
            subreddit = source.get("subreddit", "")
            url = source.get("url", "")
            keywords = source.get("keywords_found", [])
            keyword_count = len(keywords)

            lines.append(f"• Reddit r/{subreddit} ({keyword_count} keywords)")
            lines.append(url)
            lines.append(f"Found: {', '.join(keywords[:5])}")
            lines.append("")

        return "\n".join(lines)

    def format_gap(self, gap: dict) -> str:
        """
        Format a single gap entry.

        Args:
            gap: Dict with keys:
                - keyword, trend_score, source_platform, why_gap, research_links
        """
        lines = []

        keyword = gap.get("keyword", "Unknown")
        trend = gap.get("trend_score", 80)
        source = gap.get("source_platform", "")
        why = gap.get("why_gap", "")
        research = gap.get("research_links", [])

        lines.append(f"🔥 {keyword}")
        lines.append(f"Trend: {trend}%")
        lines.append("")
        lines.append(f"Found: {source}")
        lines.append("")
        lines.append(f"Why it's a gap: {why}")

        if research:
            lines.append("")
            lines.append(f"Research: {'; '.join(research[:3])}")

        return "\n".join(lines)

    def format_gaps_section(self, gaps: list[dict]) -> str:
        """Format all gaps."""
        lines = []

        for gap in gaps:
            lines.append(self.format_gap(gap))
            lines.append("")

        return "\n".join(lines)

    def format_full_report(
        self,
        subreddit_results: dict[str, list[dict]],
        your_features: list[str],
        technologies: list[str],
        use_cases: list[str],
        gaps: list[dict],
        filters: list[str] = None
    ) -> str:
        """
        Generate complete Scout-style report.

        Returns the full formatted report as a string.
        """
        sections = []

        # Header
        sections.append(self.format_scout_header())
        sections.append("")

        # Reddit results
        sections.append(self.format_reddit_results(subreddit_results))

        # Features
        sections.append(self.format_features_section(
            your_features, technologies, use_cases, filters
        ))
        sections.append("")

        # Sources
        sources = []
        for sub, posts in subreddit_results.items():
            for post in posts:
                sources.append({
                    "subreddit": sub,
                    "url": post.get("url", ""),
                    "keywords_found": post.get("keywords_found", []),
                })
        sections.append(self.format_sources_section(sources))

        # Gaps
        sections.append(self.format_gaps_section(gaps))

        return "\n".join(sections)


def format_scout_output(
    keywords_by_subreddit: dict,
    your_features: list[str],
    gaps: list[dict]
) -> str:
    """
    Quick function to format Scout-style output.

    Args:
        keywords_by_subreddit: {subreddit: [{url, keywords_found}, ...]}
        your_features: Your platform's existing features
        gaps: List of gap dicts

    Returns:
        Formatted string
    """
    formatter = ScoutFormatter()

    # Extract technologies and use cases from features
    technologies = [f for f in your_features if any(
        kw in f.lower() for kw in ["ai", "flux", "kling", "wan", "sora", "veo", "qwen", "nano"]
    )]
    use_cases = [f for f in your_features if any(
        kw in f.lower() for kw in ["upscaler", "remover", "generator", "background", "filter"]
    )]

    return formatter.format_full_report(
        subreddit_results=keywords_by_subreddit,
        your_features=your_features,
        technologies=technologies,
        use_cases=use_cases,
        gaps=gaps
    )
