"""
Main Orchestrator - Coordinates all research agent components.

This is the main entry point for the Market Research Agent.
It orchestrates crawling, extraction, classification, keyword analysis,
trend gathering, scoring, and output generation.

Usage:
    agent = MarketResearchAgent(url="https://example.com")
    results = agent.analyze()
    print(results.to_json())
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from .models import (
    SiteProfile, Keyword, Opportunity, LaunchPlaybook,
    ResearchOutput, SocialMetrics, SiteType, BusinessModel
)
from .crawler import Crawler, CrawlResult, CrawledPage
from .extractor import HTMLExtractor, ExtractedContent
from .classifier import SiteClassifier, ClassificationResult, generate_research_plan
from .keyword_extractor import KeywordExtractor, expand_keywords
from .trend_gatherer import TrendGatherer, create_trend_search_plan
from .scorer import KeywordScorer, OpportunityGenerator, PlaybookGenerator
from .formatter import OutputFormatter


@dataclass
class AgentConfig:
    """Configuration for the Market Research Agent."""
    max_pages: int = 50
    max_depth: int = 2
    recency_window: str = "90d"
    market: str = "global"
    top_keywords: int = 200
    top_opportunities: int = 10
    generate_playbooks: int = 3
    rate_limit: float = 1.0


class MarketResearchAgent:
    """
    Main agent that orchestrates the complete research workflow.

    The agent follows this pipeline:
    1. Crawl website (sitemap, robots.txt, key pages)
    2. Extract structured content (meta, headings, features, pricing)
    3. Classify site type and business model
    4. Extract and score keywords using TF-IDF
    5. Generate trend search plan (for external tools)
    6. Score keywords and generate opportunities
    7. Create launch playbooks for top opportunities
    8. Format and output results

    Usage:
        agent = MarketResearchAgent(url="https://example.com")

        # Option 1: Get crawl plan only (for manual crawling)
        plan = agent.get_crawl_plan()

        # Option 2: Analyze with provided HTML content
        results = agent.analyze_content(html_pages)

        # Option 3: Generate trend search queries
        trend_queries = agent.get_trend_queries(keywords)
    """

    def __init__(
        self,
        url: str,
        config: Optional[AgentConfig] = None
    ):
        self.url = url.rstrip("/")
        self.domain = urlparse(url).netloc
        self.config = config or AgentConfig()

        # Initialize components
        self.crawler = Crawler(
            base_url=self.url,
            max_depth=self.config.max_depth,
            max_pages=self.config.max_pages,
            rate_limit=self.config.rate_limit
        )
        self.extractor = HTMLExtractor()
        self.classifier = SiteClassifier()
        self.keyword_extractor = KeywordExtractor()
        self.trend_gatherer = TrendGatherer()
        self.keyword_scorer = KeywordScorer()
        self.formatter = OutputFormatter()

        # State
        self.crawl_result: Optional[CrawlResult] = None
        self.extracted_content: Optional[ExtractedContent] = None
        self.classification: Optional[ClassificationResult] = None
        self.site_profile: Optional[SiteProfile] = None
        self.keywords: list[Keyword] = []
        self.opportunities: list[Opportunity] = []
        self.playbooks: list[LaunchPlaybook] = []

    def get_crawl_plan(self) -> dict:
        """
        Get the crawl plan without actually crawling.

        Returns a dict with URLs to fetch and parsing instructions.
        Useful when crawling must be done by external tools (e.g., WebFetch).
        """
        return {
            "base_url": self.url,
            "domain": self.domain,
            "urls_to_fetch": [
                {"url": f"{self.url}/robots.txt", "type": "robots"},
                {"url": f"{self.url}/sitemap.xml", "type": "sitemap"},
                {"url": self.url, "type": "homepage"},
                {"url": f"{self.url}/pricing", "type": "pricing"},
                {"url": f"{self.url}/features", "type": "features"},
                {"url": f"{self.url}/docs", "type": "docs"},
                {"url": f"{self.url}/blog", "type": "blog"},
                {"url": f"{self.url}/about", "type": "about"},
                {"url": f"{self.url}/integrations", "type": "integrations"},
                {"url": f"{self.url}/api", "type": "api"},
            ],
            "priority_order": [
                "homepage", "pricing", "features", "integrations", "about"
            ],
            "max_pages": self.config.max_pages,
            "instructions": {
                "robots": "Parse robots.txt for sitemap URLs and disallowed paths",
                "sitemap": "Parse sitemap.xml for all page URLs",
                "homepage": "Extract title, meta, h1/h2/h3, features, CTAs",
                "pricing": "Extract pricing tiers, features per tier, CTAs",
                "features": "Extract feature lists, benefits, integrations",
            }
        }

    def process_html(self, html: str, url: str) -> ExtractedContent:
        """Process a single HTML page and extract content."""
        return self.extractor.extract(html, url)

    def analyze_content(
        self,
        pages: list[dict],
        social_metrics: Optional[dict[str, SocialMetrics]] = None
    ) -> ResearchOutput:
        """
        Analyze provided page content and generate research output.

        Args:
            pages: List of dicts with 'url' and 'html' keys
            social_metrics: Optional pre-fetched social metrics

        Returns:
            Complete ResearchOutput
        """
        # Step 1: Extract content from all pages
        extractions = []
        for page in pages:
            if page.get("html"):
                extraction = self.process_html(page["html"], page["url"])
                extractions.append(extraction)

        if not extractions:
            # Create minimal extraction if no HTML provided
            extractions = [ExtractedContent(url=self.url)]

        # Merge all extractions
        self.extracted_content = self.extractor.merge_extractions(extractions)

        # Step 2: Classify site
        self.classification = self.classifier.classify(self.extracted_content)

        # Step 3: Build site profile
        self.site_profile = self._build_site_profile()

        # Step 4: Extract keywords
        self.keywords = self.keyword_extractor.extract(
            self.extracted_content,
            top_n=self.config.top_keywords
        )

        # Step 5: Score keywords
        self.keywords = self.keyword_scorer.score_keywords(
            self.keywords,
            social_metrics
        )

        # Step 6: Generate opportunities
        opp_generator = OpportunityGenerator(
            site_type=self.classification.site_type
        )
        self.opportunities = opp_generator.generate(
            self.keywords,
            social_metrics,
            top_n=self.config.top_opportunities
        )

        # Step 7: Generate playbooks
        playbook_generator = PlaybookGenerator()
        self.playbooks = playbook_generator.generate(
            self.opportunities,
            top_n=self.config.generate_playbooks
        )

        # Step 8: Build and return output
        return ResearchOutput(
            site_profile=self.site_profile,
            seed_phrases=[k.keyword for k in self.keywords[:50]],
            expanded_keywords=self.keywords,
            social_signals=social_metrics or {},
            opportunities=self.opportunities,
            playbooks=self.playbooks
        )

    def _build_site_profile(self) -> SiteProfile:
        """Build site profile from extracted content and classification."""
        if not self.extracted_content or not self.classification:
            return SiteProfile(url=self.url)

        return SiteProfile(
            url=self.url,
            site_type=self.classification.site_type,
            business_model=self.classification.business_model,
            title=self.extracted_content.meta.title,
            description=self.extracted_content.meta.description,
            features=self.extracted_content.features,
            pricing=self.extracted_content.pricing_tiers,
            techstack_hints=self.extracted_content.techstack_hints,
            integrations=self.extracted_content.integrations,
            funnel_points=[f["type"] for f in self.extracted_content.forms],
            target_audience=self.classification.target_audience,
        )

    def get_trend_queries(self, keywords: Optional[list[Keyword]] = None) -> dict:
        """
        Get trend search queries for external tools.

        Args:
            keywords: Keywords to research (uses extracted if not provided)

        Returns:
            Dict with structured queries for each platform
        """
        kws = keywords or self.keywords
        if not kws:
            return {"error": "No keywords available. Run analyze_content first."}

        return create_trend_search_plan(
            kws,
            self.classification.site_type.value if self.classification else "unknown"
        )

    def get_research_plan(self) -> dict:
        """
        Get complete research plan based on site classification.

        Returns actionable search queries and focus areas.
        """
        if not self.classification or not self.extracted_content:
            return {"error": "Run analyze_content first to classify site."}

        return generate_research_plan(self.classification, self.extracted_content)

    def format_output(self, format_type: str = "json") -> str:
        """
        Format current results in specified format.

        Args:
            format_type: One of 'json', 'csv', 'markdown', 'digest'
        """
        if not self.site_profile:
            return json.dumps({"error": "No results available. Run analyze_content first."})

        output = ResearchOutput(
            site_profile=self.site_profile,
            seed_phrases=[k.keyword for k in self.keywords[:50]],
            expanded_keywords=self.keywords,
            opportunities=self.opportunities,
            playbooks=self.playbooks
        )

        if format_type == "json":
            return self.formatter.to_json(output)
        elif format_type == "markdown":
            return self.formatter.to_markdown_summary(output)
        elif format_type == "digest":
            return self.formatter.to_human_digest(output)
        elif format_type == "csv":
            return self.formatter.keywords_to_csv(self.keywords)
        else:
            return self.formatter.to_json(output)


def create_agent(url: str, **kwargs) -> MarketResearchAgent:
    """Factory function to create a configured agent."""
    config = AgentConfig(**kwargs) if kwargs else None
    return MarketResearchAgent(url=url, config=config)


def quick_analyze(url: str, html_content: str) -> str:
    """
    Quick analysis function for single-page analysis.

    Args:
        url: Website URL
        html_content: HTML content of the page

    Returns:
        JSON string with analysis results
    """
    agent = create_agent(url)
    results = agent.analyze_content([{"url": url, "html": html_content}])
    return results.to_json()
