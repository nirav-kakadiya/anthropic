"""
Market Research Agent v2.1 - Complete AI Market Research Suite

BETTER THAN SCOUT V3! 🚀

Features:
1. Website analysis and classification
2. Keyword extraction with TF-IDF scoring
3. Reddit scraping (r/StableDiffusion, r/comfyui, r/generativeAI, etc.)
4. Product Hunt launch monitoring
5. Hacker News discussion tracking
6. AI model/tool detection (100+ patterns)
7. Gap analysis vs your existing features
8. Keyword clustering
9. Trend scoring with recommendations
10. Scout V3-style formatted output

Usage:
    from market_research_agent import ScoutAgent

    # Create agent with your features
    agent = ScoutAgent(
        your_features=["flux ai", "kling ai", "ai upscaler", ...],
        niche="AI image/video platform"
    )

    # Get scan plan (URLs to fetch)
    plan = agent.get_scan_plan()

    # After fetching, analyze
    result = agent.analyze(reddit_data, ph_data, hn_data)

    # Get formatted report
    print(agent.format_report())
"""

__version__ = "2.1.0"
__author__ = "Market Research Agent"

# Core website analysis
from .orchestrator import MarketResearchAgent
from .models import SiteProfile, Keyword, Opportunity

# Gap Analysis
from .gap_analyzer import GapAnalyzer, GapResult, GapAnalysisReport

# Reddit Scraping
from .reddit_scraper import RedditScanner, get_ai_subreddit_urls, extract_ai_keywords

# Social Platform Scraping
from .social_scrapers import (
    ProductHuntScanner,
    HackerNewsScanner,
    TwitterScanner,
    SocialAggregator,
    get_producthunt_urls,
    get_hackernews_api_urls,
)

# AI Detection
from .ai_detector import AIDetector, detect_ai_items, get_ai_model_list, get_ai_tool_list

# Keyword Clustering
from .keyword_cluster import KeywordClusterer, KeywordCluster, cluster_keywords

# Trend Analysis
from .trend_analyzer import TrendAnalyzer, TrendSignal, TrendScore, quick_trend_analysis

# Scout Formatting
from .scout_formatter import ScoutFormatter, format_scout_output

# Unified Scout Agent (MAIN ENTRY POINT)
from .scout_agent import ScoutAgent, ScanResult, create_scout_agent

__all__ = [
    # Version
    "__version__",

    # Main Entry Points
    "ScoutAgent",
    "create_scout_agent",
    "ScanResult",
    "MarketResearchAgent",

    # Core Models
    "SiteProfile",
    "Keyword",
    "Opportunity",

    # Gap Analysis
    "GapAnalyzer",
    "GapResult",
    "GapAnalysisReport",

    # Reddit
    "RedditScanner",
    "get_ai_subreddit_urls",
    "extract_ai_keywords",

    # Social Platforms
    "ProductHuntScanner",
    "HackerNewsScanner",
    "TwitterScanner",
    "SocialAggregator",
    "get_producthunt_urls",
    "get_hackernews_api_urls",

    # AI Detection
    "AIDetector",
    "detect_ai_items",
    "get_ai_model_list",
    "get_ai_tool_list",

    # Clustering
    "KeywordClusterer",
    "KeywordCluster",
    "cluster_keywords",

    # Trend Analysis
    "TrendAnalyzer",
    "TrendSignal",
    "TrendScore",
    "quick_trend_analysis",

    # Formatting
    "ScoutFormatter",
    "format_scout_output",
]
