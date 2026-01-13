"""
Output Formatter module - Formats research results into various output formats.

Output formats:
- JSON (complete research output)
- CSV (keywords, opportunities)
- Markdown (launch playbooks, summaries)
"""

import json
import csv
import io
from datetime import datetime
from typing import Optional
from .models import (
    SiteProfile, Keyword, Opportunity, LaunchPlaybook,
    ResearchOutput, SocialMetrics
)


class OutputFormatter:
    """
    Formats research results into various output formats.

    Usage:
        formatter = OutputFormatter()
        json_output = formatter.to_json(research_output)
        csv_output = formatter.keywords_to_csv(keywords)
        md_output = formatter.to_markdown_summary(research_output)
    """

    def __init__(self, pretty_print: bool = True):
        self.pretty_print = pretty_print

    def to_json(self, data: ResearchOutput) -> str:
        """Convert complete research output to JSON."""
        indent = 2 if self.pretty_print else None
        return json.dumps(data.to_dict(), indent=indent, ensure_ascii=False)

    def site_profile_to_json(self, profile: SiteProfile) -> str:
        """Convert site profile to JSON."""
        indent = 2 if self.pretty_print else None
        return json.dumps(profile.to_dict(), indent=indent, ensure_ascii=False)

    def keywords_to_json(self, keywords: list[Keyword]) -> str:
        """Convert keywords to JSON."""
        indent = 2 if self.pretty_print else None
        return json.dumps(
            [k.to_dict() for k in keywords],
            indent=indent,
            ensure_ascii=False
        )

    def opportunities_to_json(self, opportunities: list[Opportunity]) -> str:
        """Convert opportunities to JSON."""
        indent = 2 if self.pretty_print else None
        return json.dumps(
            [o.to_dict() for o in opportunities],
            indent=indent,
            ensure_ascii=False
        )

    def keywords_to_csv(self, keywords: list[Keyword]) -> str:
        """Convert keywords to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "keyword",
            "monthly_volume",
            "difficulty",
            "trend_score",
            "intent",
            "composite_score",
            "source"
        ])

        # Data rows
        for kw in keywords:
            writer.writerow([
                kw.keyword,
                kw.monthly_volume,
                round(kw.difficulty, 2),
                round(kw.trend_score, 4),
                kw.intent.value,
                round(kw.composite_score, 4),
                kw.source
            ])

        return output.getvalue()

    def opportunities_to_csv(self, opportunities: list[Opportunity]) -> str:
        """Convert opportunities to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "id",
            "title",
            "priority_score",
            "dev_effort",
            "dev_days",
            "top_keywords",
            "why_now"
        ])

        # Data rows
        for opp in opportunities:
            writer.writerow([
                opp.id,
                opp.title,
                round(opp.priority_score, 4),
                opp.dev_effort.value,
                opp.dev_days,
                "; ".join(opp.top_keywords),
                opp.why_now
            ])

        return output.getvalue()

    def playbook_to_markdown(self, playbook: LaunchPlaybook) -> str:
        """Convert a single playbook to markdown."""
        return playbook.to_markdown()

    def to_markdown_summary(
        self,
        research: ResearchOutput,
        include_playbooks: bool = True
    ) -> str:
        """Generate a comprehensive markdown summary."""
        md = []

        # Header
        md.append(f"# Market Research Report")
        md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        md.append(f"**Website:** {research.site_profile.url}")
        md.append("")

        # Site Profile Summary
        md.append("## Site Analysis")
        md.append("")
        md.append(f"- **Type:** {research.site_profile.site_type.value}")
        md.append(f"- **Business Model:** {research.site_profile.business_model.value}")
        md.append(f"- **Title:** {research.site_profile.title}")
        md.append(f"- **Description:** {research.site_profile.description[:200]}...")
        md.append("")

        # Features
        if research.site_profile.features:
            md.append("### Key Features Detected")
            for feature in research.site_profile.features[:10]:
                md.append(f"- {feature}")
            md.append("")

        # Tech Stack
        if research.site_profile.techstack_hints:
            md.append("### Technology Stack")
            md.append(", ".join(research.site_profile.techstack_hints))
            md.append("")

        # Top Keywords
        md.append("## Top Keywords")
        md.append("")
        md.append("| Keyword | Volume | Trend | Score |")
        md.append("|---------|--------|-------|-------|")
        for kw in research.expanded_keywords[:20]:
            md.append(
                f"| {kw.keyword} | {kw.monthly_volume} | "
                f"{round(kw.trend_score, 2)} | {round(kw.composite_score, 2)} |"
            )
        md.append("")

        # Top Opportunities
        md.append("## Top Opportunities")
        md.append("")
        for i, opp in enumerate(research.opportunities[:5], 1):
            md.append(f"### {i}. {opp.title}")
            md.append(f"**Value Prop:** {opp.value_prop}")
            md.append(f"**Why Now:** {opp.why_now}")
            md.append(f"**Dev Effort:** {opp.dev_effort.value} ({opp.dev_days} days)")
            md.append(f"**Priority Score:** {round(opp.priority_score, 2)}")
            md.append("")
            md.append("**MVP Scope:**")
            for item in opp.mvp_scope:
                md.append(f"- {item}")
            md.append("")

        # Include playbooks
        if include_playbooks and research.playbooks:
            md.append("---")
            md.append("# Launch Playbooks")
            md.append("")
            for playbook in research.playbooks:
                md.append(playbook.to_markdown())
                md.append("")
                md.append("---")
                md.append("")

        return "\n".join(md)

    def to_human_digest(self, research: ResearchOutput) -> str:
        """Generate a concise human-readable digest."""
        lines = []

        lines.append("=" * 60)
        lines.append("MARKET RESEARCH DIGEST")
        lines.append("=" * 60)
        lines.append("")

        # Quick summary
        lines.append(f"Site: {research.site_profile.url}")
        lines.append(f"Type: {research.site_profile.site_type.value}")
        lines.append(f"Keywords Found: {len(research.expanded_keywords)}")
        lines.append(f"Opportunities Identified: {len(research.opportunities)}")
        lines.append("")

        # Top 3 actions
        lines.append("-" * 40)
        lines.append("TOP 3 LAUNCH IDEAS")
        lines.append("-" * 40)
        lines.append("")

        for i, opp in enumerate(research.opportunities[:3], 1):
            lines.append(f"{i}. {opp.title}")
            lines.append(f"   Why: {opp.why_now}")
            lines.append(f"   Effort: {opp.dev_days} days")
            lines.append(f"   Score: {round(opp.priority_score * 100)}%")
            lines.append("")

        # Quick next steps
        lines.append("-" * 40)
        lines.append("QUICK NEXT STEPS")
        lines.append("-" * 40)
        lines.append("")

        if research.opportunities:
            top_opp = research.opportunities[0]
            lines.append(f"For '{top_opp.title}':")
            lines.append("")
            for i, step in enumerate(top_opp.mvp_scope[:3], 1):
                lines.append(f"  {i}. {step}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


def save_outputs(
    research: ResearchOutput,
    output_dir: str = ".",
    prefix: str = "research"
) -> dict[str, str]:
    """
    Save all outputs to files.

    Returns dict of {format: filepath}.
    """
    formatter = OutputFormatter()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    files = {}

    # JSON files
    files["site_profile.json"] = f"{output_dir}/{prefix}_site_profile_{timestamp}.json"
    files["keywords.json"] = f"{output_dir}/{prefix}_keywords_{timestamp}.json"
    files["opportunities.json"] = f"{output_dir}/{prefix}_opportunities_{timestamp}.json"
    files["full_report.json"] = f"{output_dir}/{prefix}_full_{timestamp}.json"

    # CSV files
    files["keywords.csv"] = f"{output_dir}/{prefix}_keywords_{timestamp}.csv"
    files["opportunities.csv"] = f"{output_dir}/{prefix}_opportunities_{timestamp}.csv"

    # Markdown
    files["report.md"] = f"{output_dir}/{prefix}_report_{timestamp}.md"
    files["digest.txt"] = f"{output_dir}/{prefix}_digest_{timestamp}.txt"

    return files


def format_for_export(research: ResearchOutput, format_type: str) -> str:
    """
    Format research output for a specific export type.

    Args:
        research: Complete research output
        format_type: One of 'json', 'csv', 'markdown', 'digest'

    Returns:
        Formatted string output
    """
    formatter = OutputFormatter()

    if format_type == "json":
        return formatter.to_json(research)
    elif format_type == "csv":
        return formatter.keywords_to_csv(research.expanded_keywords)
    elif format_type == "markdown":
        return formatter.to_markdown_summary(research)
    elif format_type == "digest":
        return formatter.to_human_digest(research)
    else:
        raise ValueError(f"Unknown format type: {format_type}")
