"""
Competitor Compare - Analyze multiple sites side-by-side.

Features:
- Compare your site vs multiple competitors
- Find unique features each competitor has that you don't
- Identify market gaps across all players
- Feature overlap analysis
- Competitive advantage scoring
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class CompetitorProfile:
    """Profile of a single competitor."""
    url: str
    name: str
    niche: str = ""
    features: list[str] = field(default_factory=list)
    unique_features: list[str] = field(default_factory=list)  # Features only they have
    shared_features: list[str] = field(default_factory=list)  # Features shared with you
    missing_features: list[str] = field(default_factory=list)  # Features they lack that you have
    feature_count: int = 0
    strength_score: float = 0.0  # 0-100


@dataclass
class CompetitiveGap:
    """A gap in the market."""
    feature: str
    your_status: str  # "have", "missing"
    competitors_with: list[str] = field(default_factory=list)
    competitors_without: list[str] = field(default_factory=list)
    market_coverage: float = 0.0  # % of competitors that have it
    priority: str = "medium"  # "high", "medium", "low"
    opportunity_score: float = 0.0


@dataclass
class CompetitorAnalysis:
    """Complete competitive analysis result."""
    analysis_id: str
    analysis_time: str
    your_url: str
    your_features: list[str]

    # Competitor data
    competitors: list[CompetitorProfile] = field(default_factory=list)

    # Gaps and opportunities
    gaps_you_have: list[CompetitiveGap] = field(default_factory=list)  # Your advantages
    gaps_you_lack: list[CompetitiveGap] = field(default_factory=list)  # Your opportunities
    market_gaps: list[CompetitiveGap] = field(default_factory=list)  # Nobody has

    # Summary stats
    total_features_in_market: int = 0
    your_market_coverage: float = 0.0
    competitive_score: float = 0.0


class CompetitorCompare:
    """
    Compare your site against competitors.

    Usage:
        compare = CompetitorCompare(
            your_url="https://yoursite.com",
            your_features=["flux ai", "kling ai", "upscaler"]
        )

        # Add competitors
        compare.add_competitor(
            url="https://competitor1.com",
            name="Competitor 1",
            features=["flux ai", "sdxl", "img2img"]
        )

        compare.add_competitor(
            url="https://competitor2.com",
            name="Competitor 2",
            features=["kling ai", "sora", "video gen"]
        )

        # Run analysis
        result = compare.analyze()

        # Get report
        print(compare.format_report())
    """

    def __init__(
        self,
        your_url: str,
        your_features: list[str],
        your_name: str = "Your Site"
    ):
        self.your_url = your_url
        self.your_name = your_name
        self.your_features = [f.lower().strip() for f in your_features]
        self.competitors: list[CompetitorProfile] = []
        self.last_analysis: Optional[CompetitorAnalysis] = None

    def add_competitor(
        self,
        url: str,
        name: str,
        features: list[str],
        niche: str = ""
    ):
        """Add a competitor to compare against."""
        profile = CompetitorProfile(
            url=url,
            name=name,
            niche=niche,
            features=[f.lower().strip() for f in features],
            feature_count=len(features)
        )
        self.competitors.append(profile)

    def analyze(self) -> CompetitorAnalysis:
        """
        Run competitive analysis.

        Returns CompetitorAnalysis with gaps and opportunities.
        """
        analysis_id = f"comp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Collect all features in market
        all_features = set(self.your_features)
        for comp in self.competitors:
            all_features.update(comp.features)

        all_features_list = sorted(all_features)

        # Analyze each competitor
        for comp in self.competitors:
            comp_features_set = set(comp.features)
            your_features_set = set(self.your_features)

            # Features only they have
            comp.unique_features = [
                f for f in comp.features
                if f not in your_features_set and
                all(f not in set(c.features) for c in self.competitors if c != comp)
            ]

            # Shared with you
            comp.shared_features = [f for f in comp.features if f in your_features_set]

            # Features they lack that you have
            comp.missing_features = [f for f in self.your_features if f not in comp_features_set]

            # Strength score (based on feature coverage)
            comp.strength_score = (len(comp.features) / max(1, len(all_features))) * 100

        # Analyze gaps
        gaps_you_have = []
        gaps_you_lack = []
        market_gaps = []

        for feature in all_features_list:
            you_have = feature in self.your_features
            comps_with = [c.name for c in self.competitors if feature in c.features]
            comps_without = [c.name for c in self.competitors if feature not in c.features]

            market_coverage = len(comps_with) / max(1, len(self.competitors)) * 100

            # Calculate priority and opportunity score
            if you_have and not comps_with:
                # You have it, no one else does - your advantage!
                priority = "high"
                opportunity_score = 90 + (10 * (1 - market_coverage / 100))
                gaps_you_have.append(CompetitiveGap(
                    feature=feature,
                    your_status="have",
                    competitors_with=comps_with,
                    competitors_without=comps_without,
                    market_coverage=market_coverage,
                    priority=priority,
                    opportunity_score=opportunity_score,
                ))
            elif not you_have and comps_with:
                # You don't have it, but competitors do - opportunity!
                if market_coverage >= 50:
                    priority = "high"
                    opportunity_score = 80 + (market_coverage * 0.2)
                elif market_coverage >= 25:
                    priority = "medium"
                    opportunity_score = 60 + (market_coverage * 0.3)
                else:
                    priority = "low"
                    opportunity_score = 40 + (market_coverage * 0.4)

                gaps_you_lack.append(CompetitiveGap(
                    feature=feature,
                    your_status="missing",
                    competitors_with=comps_with,
                    competitors_without=comps_without,
                    market_coverage=market_coverage,
                    priority=priority,
                    opportunity_score=opportunity_score,
                ))
            elif not you_have and not comps_with:
                # Nobody has it - market gap!
                market_gaps.append(CompetitiveGap(
                    feature=feature,
                    your_status="missing",
                    competitors_with=[],
                    competitors_without=[c.name for c in self.competitors],
                    market_coverage=0.0,
                    priority="medium",
                    opportunity_score=50,  # Unknown opportunity
                ))

        # Sort by opportunity score
        gaps_you_have.sort(key=lambda x: x.opportunity_score, reverse=True)
        gaps_you_lack.sort(key=lambda x: x.opportunity_score, reverse=True)

        # Calculate your market coverage
        your_coverage = (len(self.your_features) / max(1, len(all_features))) * 100

        # Calculate competitive score
        avg_competitor_features = sum(len(c.features) for c in self.competitors) / max(1, len(self.competitors))
        competitive_score = min(100, (len(self.your_features) / max(1, avg_competitor_features)) * 70 + 30)

        self.last_analysis = CompetitorAnalysis(
            analysis_id=analysis_id,
            analysis_time=datetime.now().isoformat(),
            your_url=self.your_url,
            your_features=self.your_features,
            competitors=self.competitors,
            gaps_you_have=gaps_you_have,
            gaps_you_lack=gaps_you_lack,
            market_gaps=market_gaps,
            total_features_in_market=len(all_features),
            your_market_coverage=your_coverage,
            competitive_score=competitive_score,
        )

        return self.last_analysis

    def format_report(self, analysis: Optional[CompetitorAnalysis] = None) -> str:
        """Format competitive analysis as readable report."""
        analysis = analysis or self.last_analysis
        if not analysis:
            return "No analysis available. Run analyze() first."

        lines = [
            "=" * 70,
            "🏆 COMPETITIVE ANALYSIS REPORT",
            "=" * 70,
            f"Your Site: {self.your_name} ({self.your_url})",
            f"Analysis Time: {analysis.analysis_time}",
            "",
            "-" * 40,
            "📊 SUMMARY",
            "-" * 40,
            f"Your Features: {len(self.your_features)}",
            f"Total Features in Market: {analysis.total_features_in_market}",
            f"Your Market Coverage: {analysis.your_market_coverage:.1f}%",
            f"Competitive Score: {analysis.competitive_score:.1f}/100",
            f"Competitors Analyzed: {len(analysis.competitors)}",
            "",
        ]

        # Competitor overview
        lines.append("-" * 40)
        lines.append("🎯 COMPETITORS")
        lines.append("-" * 40)
        for comp in analysis.competitors:
            lines.append(f"\n{comp.name} ({comp.url})")
            lines.append(f"  Features: {comp.feature_count}")
            lines.append(f"  Strength Score: {comp.strength_score:.1f}%")
            lines.append(f"  Shared with you: {len(comp.shared_features)}")
            lines.append(f"  Unique to them: {len(comp.unique_features)}")
            if comp.unique_features[:3]:
                lines.append(f"    → {', '.join(comp.unique_features[:3])}")

        # Your competitive advantages
        if analysis.gaps_you_have:
            lines.append("")
            lines.append("-" * 40)
            lines.append("💪 YOUR COMPETITIVE ADVANTAGES")
            lines.append("-" * 40)
            lines.append("Features only YOU have:")
            for gap in analysis.gaps_you_have[:10]:
                lines.append(f"  ✓ {gap.feature}")
                lines.append(f"    → No competitor has this!")

        # Opportunities (gaps you lack)
        if analysis.gaps_you_lack:
            lines.append("")
            lines.append("-" * 40)
            lines.append("🔥 TOP OPPORTUNITIES")
            lines.append("-" * 40)
            lines.append("Features competitors have that you don't:")
            for gap in analysis.gaps_you_lack[:15]:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[gap.priority]
                lines.append(f"\n  {priority_icon} {gap.feature}")
                lines.append(f"     Priority: {gap.priority.upper()}")
                lines.append(f"     Market Coverage: {gap.market_coverage:.0f}%")
                lines.append(f"     Competitors with: {', '.join(gap.competitors_with[:3])}")

        # Market gaps
        if analysis.market_gaps:
            lines.append("")
            lines.append("-" * 40)
            lines.append("🌟 MARKET GAPS (First-Mover Opportunities)")
            lines.append("-" * 40)
            lines.append("Features NOBODY in market has yet:")
            for gap in analysis.market_gaps[:10]:
                lines.append(f"  ○ {gap.feature}")

        return "\n".join(lines)

    def export_json(self, analysis: Optional[CompetitorAnalysis] = None) -> str:
        """Export analysis as JSON."""
        analysis = analysis or self.last_analysis
        if not analysis:
            return "{}"

        export = {
            "analysis_id": analysis.analysis_id,
            "analysis_time": analysis.analysis_time,
            "your_site": {
                "url": self.your_url,
                "name": self.your_name,
                "features": self.your_features,
                "feature_count": len(self.your_features),
            },
            "summary": {
                "total_features_in_market": analysis.total_features_in_market,
                "your_market_coverage": analysis.your_market_coverage,
                "competitive_score": analysis.competitive_score,
            },
            "competitors": [
                {
                    "name": c.name,
                    "url": c.url,
                    "features": c.features,
                    "strength_score": c.strength_score,
                    "unique_features": c.unique_features,
                    "shared_features": c.shared_features,
                }
                for c in analysis.competitors
            ],
            "your_advantages": [
                {"feature": g.feature, "score": g.opportunity_score}
                for g in analysis.gaps_you_have
            ],
            "opportunities": [
                {
                    "feature": g.feature,
                    "priority": g.priority,
                    "market_coverage": g.market_coverage,
                    "competitors_with": g.competitors_with,
                }
                for g in analysis.gaps_you_lack
            ],
            "market_gaps": [g.feature for g in analysis.market_gaps],
        }

        return json.dumps(export, indent=2)


def compare_competitors(
    your_features: list[str],
    competitors: list[dict],
    your_url: str = "",
) -> CompetitorAnalysis:
    """
    Quick function to compare competitors.

    Args:
        your_features: List of your features
        competitors: List of {name, url, features} dicts
        your_url: Your site URL

    Returns:
        CompetitorAnalysis result
    """
    compare = CompetitorCompare(
        your_url=your_url,
        your_features=your_features,
    )

    for comp in competitors:
        compare.add_competitor(
            url=comp.get("url", ""),
            name=comp.get("name", "Unknown"),
            features=comp.get("features", []),
        )

    return compare.analyze()
