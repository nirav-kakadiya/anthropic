"""
Market Research Agent v2.2 - Complete AI Market Research Suite

BETTER THAN SCOUT V3! Now with AUTO MODE!

Features:
1. AUTO MODE: Just provide URL -> auto-detects features & niche
2. Website analysis with sitemap/robots.txt parsing
3. Automatic feature extraction from pages
4. Automatic niche/industry detection
5. Reddit scraping (r/StableDiffusion, r/comfyui, r/generativeAI, etc.)
6. Product Hunt launch monitoring
7. Hacker News discussion tracking
8. AI model/tool detection (100+ patterns)
9. Gap analysis vs your existing features
10. Keyword clustering
11. Trend scoring with recommendations
12. Scout V3-style formatted output

Usage (AUTO MODE - just provide URL):
    from market_research_agent import AutoScoutAgent

    # Create agent from URL - auto-detects everything!
    agent = AutoScoutAgent.from_url("https://your-site.com")

    # Get URLs to crawl
    urls = agent.get_site_urls()

    # Feed HTML content
    agent.process_page("home", homepage_html)
    agent.process_page("features", features_html)

    # Auto-detect features and niche
    config = agent.auto_detect()
    print(f"Detected: {config.detected_niche}")
    print(f"Features: {len(config.detected_features)}")

    # Optionally add manual features
    agent.add_manual_features(["custom feature"])

    # Run research
    result = agent.run_research(reddit_data, ph_data, hn_data)

Usage (MANUAL MODE - provide features directly):
    from market_research_agent import AutoScoutAgent

    agent = AutoScoutAgent.manual(
        features=["flux ai", "kling ai", "ai upscaler"],
        niche="AI image/video platform"
    )
    result = agent.run_research(reddit_data, ph_data, hn_data)
"""

__version__ = "2.2.0"
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

# AUTO MODE - Automatic feature and niche detection
from .scout_agent import (
    AutoScoutAgent,
    AutoScanConfig,
    create_auto_scout,
    create_manual_scout,
)

# Site Analysis (for auto mode)
from .site_analyzer import SiteAnalyzer, SiteStructure, create_site_analyzer

# Feature Extraction (for auto mode)
from .feature_extractor import (
    FeatureExtractor,
    ExtractedFeature,
    FeatureExtractionResult,
    extract_features_from_html,
)

# Niche Detection (for auto mode)
from .niche_detector import (
    NicheDetector,
    NicheResult,
    detect_niche,
    detect_niche_from_features,
)

__all__ = [
    # Version
    "__version__",

    # Main Entry Points
    "ScoutAgent",
    "create_scout_agent",
    "ScanResult",
    "MarketResearchAgent",

    # AUTO MODE (NEW!)
    "AutoScoutAgent",
    "AutoScanConfig",
    "create_auto_scout",
    "create_manual_scout",

    # Site Analysis
    "SiteAnalyzer",
    "SiteStructure",
    "create_site_analyzer",

    # Feature Extraction
    "FeatureExtractor",
    "ExtractedFeature",
    "FeatureExtractionResult",
    "extract_features_from_html",

    # Niche Detection
    "NicheDetector",
    "NicheResult",
    "detect_niche",
    "detect_niche_from_features",

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
