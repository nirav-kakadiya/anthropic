"""
Gap Analyzer module - Compares discovered keywords against existing platform features.

This module identifies product gaps by:
1. Taking a list of discovered keywords/tools from Reddit/social
2. Comparing against your existing feature list
3. Flagging items that are NOT in your feature list as gaps
4. Generating "Why it's a gap" explanations
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from difflib import SequenceMatcher


@dataclass
class GapResult:
    """A single gap analysis result."""
    keyword: str
    trend_score: float = 80.0  # Default trend score
    source_platform: str = ""  # e.g., "Reddit r/StableDiffusion"
    source_url: str = ""
    is_gap: bool = True
    matched_feature: str = ""  # If matched, what it matched to
    why_gap: str = ""  # Explanation of why this is a gap
    category: str = ""  # technology, use_case, filter, tool, model


@dataclass
class GapAnalysisReport:
    """Complete gap analysis report."""
    total_keywords_found: int = 0
    total_gaps: int = 0
    total_covered: int = 0
    gaps: list[GapResult] = field(default_factory=list)
    covered: list[GapResult] = field(default_factory=list)
    by_category: dict[str, list[GapResult]] = field(default_factory=dict)


class GapAnalyzer:
    """
    Analyzes keywords against existing features to find product gaps.

    Usage:
        analyzer = GapAnalyzer(existing_features=["flux ai", "kling ai", ...])
        report = analyzer.analyze(discovered_keywords)
    """

    # AI-specific keyword categories
    CATEGORY_PATTERNS = {
        "model": [
            r"flux", r"kling", r"wan", r"sora", r"veo", r"sdxl", r"stable.?diffusion",
            r"qwen", r"gpt", r"nano.?banana", r"ltx", r"z.?image", r"comfyui",
            r"lora", r"rife", r"controlnet", r"fooocus", r"midjourney",
        ],
        "tool": [
            r"upscaler", r"remover", r"generator", r"editor", r"converter",
            r"workflow", r"toolkit", r"manager", r"suite", r"pipeline",
        ],
        "filter": [
            r"filter", r"effect", r"style", r"aesthetic", r"look",
        ],
        "technique": [
            r"training", r"fine.?tuning", r"interpolation", r"injection",
            r"quantization", r"distill", r"lora",
        ],
        "use_case": [
            r"background", r"upscale", r"remove", r"generate", r"create",
            r"animate", r"transform", r"convert",
        ],
    }

    # Gap explanation templates
    GAP_TEMPLATES = {
        "model": "'{keyword}' is a specific AI model referenced in {source}. The platform's feature list does not include this model or any very similar entry, indicating users seeking this model may be underserved.",
        "tool": "'{keyword}' appears to be a specific tool/utility mentioned on {source}. No exact or similar entry exists in the platform features, representing a tool integration gap.",
        "filter": "'{keyword}' is a specific visual filter/effect. The platform has many filters but does not include this exact one or a close match, so it represents a styling gap.",
        "technique": "'{keyword}' refers to a specific AI technique/capability. The platform does not offer this functionality, representing a technical capability gap.",
        "use_case": "'{keyword}' describes a specific use case/workflow. This exact capability is not covered by existing features, suggesting an opportunity to add this functionality.",
        "default": "'{keyword}' does not match any entry in the platform's feature list. This represents a potential product gap that could be addressed to capture user demand.",
    }

    def __init__(
        self,
        existing_features: list[str],
        similarity_threshold: float = 0.85
    ):
        """
        Initialize with existing platform features.

        Args:
            existing_features: List of feature names already on platform
            similarity_threshold: How similar a keyword must be to count as "covered"
        """
        self.existing_features = [f.lower().strip() for f in existing_features]
        self.similarity_threshold = similarity_threshold

    def normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        # Lowercase
        text = text.lower()
        # Remove special characters except spaces and hyphens
        text = re.sub(r'[^\w\s-]', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings."""
        a_norm = self.normalize(a)
        b_norm = self.normalize(b)

        # Exact match
        if a_norm == b_norm:
            return 1.0

        # Check if one contains the other
        if a_norm in b_norm or b_norm in a_norm:
            return 0.9

        # Sequence matching
        return SequenceMatcher(None, a_norm, b_norm).ratio()

    def find_match(self, keyword: str) -> tuple[bool, str, float]:
        """
        Check if keyword matches any existing feature.

        Returns:
            (is_match, matched_feature, similarity_score)
        """
        keyword_norm = self.normalize(keyword)

        best_match = ""
        best_score = 0.0

        for feature in self.existing_features:
            score = self.calculate_similarity(keyword_norm, feature)

            if score > best_score:
                best_score = score
                best_match = feature

        is_match = best_score >= self.similarity_threshold
        return is_match, best_match, best_score

    def categorize_keyword(self, keyword: str) -> str:
        """Categorize a keyword into a type."""
        keyword_lower = keyword.lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, keyword_lower):
                    return category

        return "other"

    def generate_gap_explanation(
        self,
        keyword: str,
        category: str,
        source: str
    ) -> str:
        """Generate explanation for why something is a gap."""
        template = self.GAP_TEMPLATES.get(category, self.GAP_TEMPLATES["default"])
        return template.format(keyword=keyword, source=source)

    def analyze_keyword(
        self,
        keyword: str,
        source_platform: str = "",
        source_url: str = "",
        trend_score: float = 80.0
    ) -> GapResult:
        """
        Analyze a single keyword against existing features.

        Returns:
            GapResult with gap analysis
        """
        is_match, matched_feature, similarity = self.find_match(keyword)
        category = self.categorize_keyword(keyword)

        result = GapResult(
            keyword=keyword,
            trend_score=trend_score,
            source_platform=source_platform,
            source_url=source_url,
            category=category,
        )

        if is_match:
            result.is_gap = False
            result.matched_feature = matched_feature
            result.why_gap = f"Covered by existing feature: '{matched_feature}' (similarity: {similarity:.0%})"
        else:
            result.is_gap = True
            result.why_gap = self.generate_gap_explanation(keyword, category, source_platform)

        return result

    def analyze(
        self,
        discovered_keywords: list[dict]
    ) -> GapAnalysisReport:
        """
        Analyze multiple keywords against existing features.

        Args:
            discovered_keywords: List of dicts with keys:
                - keyword: str
                - source_platform: str (optional)
                - source_url: str (optional)
                - trend_score: float (optional)

        Returns:
            GapAnalysisReport with all results
        """
        report = GapAnalysisReport()
        report.total_keywords_found = len(discovered_keywords)

        for item in discovered_keywords:
            keyword = item.get("keyword", "")
            if not keyword:
                continue

            result = self.analyze_keyword(
                keyword=keyword,
                source_platform=item.get("source_platform", ""),
                source_url=item.get("source_url", ""),
                trend_score=item.get("trend_score", 80.0)
            )

            if result.is_gap:
                report.gaps.append(result)
                report.total_gaps += 1
            else:
                report.covered.append(result)
                report.total_covered += 1

            # Group by category
            if result.category not in report.by_category:
                report.by_category[result.category] = []
            report.by_category[result.category].append(result)

        return report

    def format_gap_report(self, report: GapAnalysisReport) -> str:
        """Format gap report as readable text."""
        lines = []

        lines.append("=" * 60)
        lines.append("GAP ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Total Keywords Analyzed: {report.total_keywords_found}")
        lines.append(f"Gaps Found: {report.total_gaps}")
        lines.append(f"Already Covered: {report.total_covered}")
        lines.append("")

        # Top gaps
        lines.append("-" * 40)
        lines.append("🔥 TOP GAPS")
        lines.append("-" * 40)

        for gap in report.gaps[:20]:
            lines.append(f"\n🔥 {gap.keyword}")
            lines.append(f"Trend: {gap.trend_score}%")
            lines.append(f"Found: {gap.source_platform}")
            lines.append(f"Category: {gap.category}")
            lines.append(f"Why it's a gap: {gap.why_gap}")

        # By category
        lines.append("\n" + "-" * 40)
        lines.append("📊 GAPS BY CATEGORY")
        lines.append("-" * 40)

        for category, items in report.by_category.items():
            gaps_in_cat = [i for i in items if i.is_gap]
            if gaps_in_cat:
                lines.append(f"\n{category.upper()} ({len(gaps_in_cat)} gaps):")
                for gap in gaps_in_cat[:5]:
                    lines.append(f"  • {gap.keyword}")

        return "\n".join(lines)


def create_gap_analyzer(features: list[str]) -> GapAnalyzer:
    """Factory function to create a gap analyzer."""
    return GapAnalyzer(existing_features=features)
