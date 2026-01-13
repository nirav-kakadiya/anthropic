#!/usr/bin/env python3
"""
Command-line interface for the Market Research Agent.

Usage:
    python -m market_research_agent.cli analyze https://example.com
    python -m market_research_agent.cli plan https://example.com
    python -m market_research_agent.cli keywords https://example.com
"""

import argparse
import json
import sys
from typing import Optional

from .orchestrator import MarketResearchAgent, AgentConfig, create_agent
from .formatter import OutputFormatter


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Market Research Agent - Analyze websites and discover opportunities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get crawl plan for a website
  python -m market_research_agent plan https://example.com

  # Analyze with HTML file
  python -m market_research_agent analyze https://example.com --html page.html

  # Get trend queries
  python -m market_research_agent trends https://example.com

  # Export keywords to CSV
  python -m market_research_agent keywords https://example.com --format csv
        """
    )

    parser.add_argument(
        "command",
        choices=["plan", "analyze", "trends", "keywords", "opportunities"],
        help="Command to run"
    )

    parser.add_argument(
        "url",
        help="Website URL to analyze"
    )

    parser.add_argument(
        "--html",
        type=str,
        help="Path to HTML file to analyze"
    )

    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv", "markdown", "digest"],
        default="json",
        help="Output format (default: json)"
    )

    parser.add_argument(
        "--max-keywords", "-k",
        type=int,
        default=200,
        help="Maximum keywords to extract (default: 200)"
    )

    parser.add_argument(
        "--max-opportunities", "-o",
        type=int,
        default=10,
        help="Maximum opportunities to generate (default: 10)"
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty print JSON output"
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )

    return parser.parse_args()


def load_html_file(filepath: str) -> str:
    """Load HTML content from file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_plan(agent: MarketResearchAgent, args: argparse.Namespace) -> None:
    """Output crawl plan."""
    plan = agent.get_crawl_plan()

    if args.format == "json":
        print(json.dumps(plan, indent=2))
    else:
        print("=== Crawl Plan ===")
        print(f"Base URL: {plan['base_url']}")
        print(f"Domain: {plan['domain']}")
        print("\nURLs to fetch:")
        for item in plan['urls_to_fetch']:
            print(f"  - [{item['type']}] {item['url']}")


def cmd_analyze(agent: MarketResearchAgent, args: argparse.Namespace) -> None:
    """Analyze website content."""
    pages = []

    if args.html:
        html = load_html_file(args.html)
        pages.append({"url": args.url, "html": html})
    else:
        # No HTML provided - just create minimal analysis
        pages.append({"url": args.url, "html": ""})
        if not args.quiet:
            print("Note: No HTML provided. Use --html to provide page content.", file=sys.stderr)

    results = agent.analyze_content(pages)
    output = agent.format_output(args.format)
    print(output)


def cmd_trends(agent: MarketResearchAgent, args: argparse.Namespace) -> None:
    """Get trend search queries."""
    # Need to analyze first
    pages = []
    if args.html:
        html = load_html_file(args.html)
        pages.append({"url": args.url, "html": html})
    else:
        pages.append({"url": args.url, "html": ""})

    agent.analyze_content(pages)
    queries = agent.get_trend_queries()

    if args.format == "json":
        print(json.dumps(queries, indent=2))
    else:
        print("=== Trend Search Queries ===")
        for platform, items in queries.items():
            if platform != "metadata":
                print(f"\n{platform.upper()}:")
                if isinstance(items, list):
                    for item in items[:5]:
                        print(f"  - {item}")
                elif isinstance(items, dict):
                    for key, val in items.items():
                        if isinstance(val, list):
                            print(f"  {key}: {len(val)} queries")


def cmd_keywords(agent: MarketResearchAgent, args: argparse.Namespace) -> None:
    """Extract and display keywords."""
    pages = []
    if args.html:
        html = load_html_file(args.html)
        pages.append({"url": args.url, "html": html})
    else:
        pages.append({"url": args.url, "html": ""})

    agent.analyze_content(pages)

    formatter = OutputFormatter()

    if args.format == "csv":
        print(formatter.keywords_to_csv(agent.keywords))
    elif args.format == "json":
        print(formatter.keywords_to_json(agent.keywords))
    else:
        print("=== Extracted Keywords ===")
        for i, kw in enumerate(agent.keywords[:20], 1):
            print(f"{i:3}. {kw.keyword} (score: {kw.composite_score:.3f})")


def cmd_opportunities(agent: MarketResearchAgent, args: argparse.Namespace) -> None:
    """Generate and display opportunities."""
    pages = []
    if args.html:
        html = load_html_file(args.html)
        pages.append({"url": args.url, "html": html})
    else:
        pages.append({"url": args.url, "html": ""})

    agent.analyze_content(pages)

    formatter = OutputFormatter()

    if args.format == "csv":
        print(formatter.opportunities_to_csv(agent.opportunities))
    elif args.format == "json":
        print(formatter.opportunities_to_json(agent.opportunities))
    elif args.format == "markdown":
        for opp in agent.opportunities[:5]:
            print(f"## {opp.title}")
            print(f"**Value:** {opp.value_prop}")
            print(f"**Why Now:** {opp.why_now}")
            print(f"**Effort:** {opp.dev_days} days")
            print()
    else:
        print("=== Top Opportunities ===")
        for i, opp in enumerate(agent.opportunities[:10], 1):
            print(f"\n{i}. {opp.title}")
            print(f"   Score: {opp.priority_score:.2f}")
            print(f"   Effort: {opp.dev_days} days")
            print(f"   Why: {opp.why_now}")


def main():
    """Main entry point."""
    args = parse_args()

    config = AgentConfig(
        top_keywords=args.max_keywords,
        top_opportunities=args.max_opportunities,
    )

    agent = MarketResearchAgent(url=args.url, config=config)

    commands = {
        "plan": cmd_plan,
        "analyze": cmd_analyze,
        "trends": cmd_trends,
        "keywords": cmd_keywords,
        "opportunities": cmd_opportunities,
    }

    command_func = commands.get(args.command)
    if command_func:
        command_func(agent, args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
