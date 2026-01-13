"""
Real-time Trend Analyzer - Fetches and analyzes trends from multiple sources.

Combines data from:
- Google Trends (via search queries)
- Reddit (post velocity, upvotes)
- Product Hunt (launches, votes)
- Hacker News (discussions, points)
- Twitter/X (mentions, engagement)

Calculates composite trend scores with time-decay weighting.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import math


@dataclass
class TrendSignal:
    """A single trend signal from one source."""
    keyword: str
    source: str  # google_trends, reddit, producthunt, hackernews, twitter
    score: float  # 0-100
    velocity: float = 0.0  # Rate of change
    volume: int = 0  # Raw count (mentions, posts, etc.)
    timestamp: str = ""
    url: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class TrendScore:
    """Composite trend score for a keyword."""
    keyword: str
    composite_score: float  # 0-100
    trend_direction: str  # "rising", "stable", "falling"
    confidence: float  # 0-1
    signals: list[TrendSignal] = field(default_factory=list)
    first_seen: str = ""
    peak_score: float = 0.0
    recommendation: str = ""


class TrendAnalyzer:
    """
    Analyzes trends across multiple platforms.

    Usage:
        analyzer = TrendAnalyzer()
        scores = analyzer.calculate_scores(signals)
    """

    # Source weights for composite scoring
    SOURCE_WEIGHTS = {
        "google_trends": 0.30,
        "reddit": 0.25,
        "producthunt": 0.20,
        "hackernews": 0.15,
        "twitter": 0.10,
    }

    # Time decay factor (older signals worth less)
    TIME_DECAY_DAYS = 30

    def __init__(self):
        pass

    def normalize_score(self, value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normalize a value to 0-100 scale."""
        if max_val <= min_val:
            return 0.0
        normalized = ((value - min_val) / (max_val - min_val)) * 100
        return max(0.0, min(100.0, normalized))

    def calculate_time_decay(self, timestamp: str) -> float:
        """Calculate time decay factor (1.0 = recent, 0.0 = old)."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age_days = (datetime.now(dt.tzinfo) - dt).days
            decay = math.exp(-age_days / self.TIME_DECAY_DAYS)
            return max(0.1, decay)
        except (ValueError, TypeError):
            return 0.5  # Default for unknown timestamps

    def calculate_velocity(self, current: float, previous: float, days: int = 7) -> float:
        """Calculate trend velocity (rate of change)."""
        if days <= 0:
            return 0.0
        return (current - previous) / days

    def determine_trend_direction(self, velocity: float) -> str:
        """Determine trend direction from velocity."""
        if velocity > 5:
            return "🚀 rapidly rising"
        elif velocity > 1:
            return "📈 rising"
        elif velocity > -1:
            return "➡️ stable"
        elif velocity > -5:
            return "📉 falling"
        else:
            return "⬇️ rapidly falling"

    def generate_recommendation(self, score: TrendScore) -> str:
        """Generate actionable recommendation based on trend."""
        if score.composite_score >= 80 and "rising" in score.trend_direction:
            return "🔥 HIGH PRIORITY: Build immediately - trending now!"
        elif score.composite_score >= 60 and "rising" in score.trend_direction:
            return "⚡ GOOD OPPORTUNITY: Strong momentum, consider building"
        elif score.composite_score >= 40:
            return "👀 MONITOR: Moderate interest, watch for growth"
        elif "rising" in score.trend_direction:
            return "🌱 EMERGING: Low volume but growing, early opportunity"
        else:
            return "⏸️ WAIT: Low interest, not recommended now"

    def calculate_composite_score(self, signals: list[TrendSignal]) -> TrendScore:
        """
        Calculate composite trend score from multiple signals.

        Args:
            signals: List of TrendSignal objects for same keyword

        Returns:
            TrendScore with composite analysis
        """
        if not signals:
            return TrendScore(keyword="unknown", composite_score=0, trend_direction="unknown", confidence=0)

        keyword = signals[0].keyword
        weighted_sum = 0.0
        total_weight = 0.0
        velocities = []

        for signal in signals:
            weight = self.SOURCE_WEIGHTS.get(signal.source, 0.1)
            time_decay = self.calculate_time_decay(signal.timestamp)
            adjusted_weight = weight * time_decay

            weighted_sum += signal.score * adjusted_weight
            total_weight += adjusted_weight
            velocities.append(signal.velocity)

        # Calculate composite score
        composite = weighted_sum / total_weight if total_weight > 0 else 0

        # Calculate average velocity
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0

        # Determine confidence based on number of sources
        unique_sources = len(set(s.source for s in signals))
        confidence = min(1.0, unique_sources / 3)

        trend_score = TrendScore(
            keyword=keyword,
            composite_score=round(composite, 1),
            trend_direction=self.determine_trend_direction(avg_velocity),
            confidence=round(confidence, 2),
            signals=signals,
            peak_score=max(s.score for s in signals),
        )

        trend_score.recommendation = self.generate_recommendation(trend_score)

        return trend_score

    def rank_keywords(self, keyword_signals: dict[str, list[TrendSignal]]) -> list[TrendScore]:
        """
        Rank multiple keywords by their trend scores.

        Args:
            keyword_signals: Dict mapping keyword -> list of signals

        Returns:
            List of TrendScore sorted by composite score (descending)
        """
        scores = []

        for keyword, signals in keyword_signals.items():
            score = self.calculate_composite_score(signals)
            scores.append(score)

        # Sort by composite score
        scores.sort(key=lambda s: s.composite_score, reverse=True)

        return scores

    def format_trend_report(self, scores: list[TrendScore], top_n: int = 20) -> str:
        """Format trend scores as readable report."""
        lines = []

        lines.append("=" * 60)
        lines.append("🔥 TREND ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"Keywords analyzed: {len(scores)}")
        lines.append("")

        lines.append("-" * 40)
        lines.append("TOP TRENDING KEYWORDS")
        lines.append("-" * 40)

        for i, score in enumerate(scores[:top_n], 1):
            lines.append(f"\n{i}. {score.keyword}")
            lines.append(f"   Score: {score.composite_score}% {score.trend_direction}")
            lines.append(f"   Confidence: {score.confidence:.0%}")
            lines.append(f"   Sources: {len(score.signals)}")
            lines.append(f"   → {score.recommendation}")

        # Categorize by recommendation
        lines.append("\n" + "-" * 40)
        lines.append("BY PRIORITY")
        lines.append("-" * 40)

        high_priority = [s for s in scores if "HIGH PRIORITY" in s.recommendation]
        good_opp = [s for s in scores if "GOOD OPPORTUNITY" in s.recommendation]
        emerging = [s for s in scores if "EMERGING" in s.recommendation]

        if high_priority:
            lines.append(f"\n🔥 HIGH PRIORITY ({len(high_priority)}):")
            for s in high_priority[:5]:
                lines.append(f"   • {s.keyword} ({s.composite_score}%)")

        if good_opp:
            lines.append(f"\n⚡ GOOD OPPORTUNITIES ({len(good_opp)}):")
            for s in good_opp[:5]:
                lines.append(f"   • {s.keyword} ({s.composite_score}%)")

        if emerging:
            lines.append(f"\n🌱 EMERGING ({len(emerging)}):")
            for s in emerging[:5]:
                lines.append(f"   • {s.keyword} ({s.composite_score}%)")

        return "\n".join(lines)


# Convenience functions

def create_trend_signal(
    keyword: str,
    source: str,
    score: float,
    volume: int = 0,
    url: str = ""
) -> TrendSignal:
    """Create a trend signal with current timestamp."""
    return TrendSignal(
        keyword=keyword,
        source=source,
        score=score,
        volume=volume,
        url=url,
        timestamp=datetime.now().isoformat()
    )


def quick_trend_analysis(keyword_data: list[dict]) -> list[TrendScore]:
    """
    Quick trend analysis from raw data.

    Args:
        keyword_data: List of dicts with:
            - keyword: str
            - signals: list of {source, score, volume}

    Returns:
        Ranked list of TrendScore
    """
    analyzer = TrendAnalyzer()
    keyword_signals = {}

    for item in keyword_data:
        keyword = item.get("keyword", "")
        signals = []

        for sig in item.get("signals", []):
            signals.append(create_trend_signal(
                keyword=keyword,
                source=sig.get("source", "unknown"),
                score=sig.get("score", 50),
                volume=sig.get("volume", 0),
            ))

        if signals:
            keyword_signals[keyword] = signals

    return analyzer.rank_keywords(keyword_signals)
