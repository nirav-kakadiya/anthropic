"""
Market Research Agent v2.3 - Complete AI Market Research Suite

ULTIMATE MARKET RESEARCH PLATFORM!

Features:
1. AUTO MODE: Just provide URL -> auto-detects features & niche
2. LIVE FETCHER: Async HTTP with rate limiting and retries
3. COMPETITOR COMPARE: Side-by-side multi-competitor analysis
4. ALERTS: Discord & Slack webhook notifications
5. STORAGE: SQLite database for scan history & trends
6. SCHEDULER: Automated daily/weekly/hourly scans
7. EXPORTER: CSV, Excel, PDF, HTML, Markdown exports
8. WEB DASHBOARD: Flask-based UI for easy access
9. Reddit, Product Hunt, Hacker News scraping
10. AI model/tool detection (100+ patterns)
11. Gap analysis with "Why it's a gap" explanations
12. Keyword clustering and trend scoring

Quick Start:
    from market_research_agent import AutoScoutAgent

    # AUTO MODE
    agent = AutoScoutAgent.from_url("https://your-site.com")
    agent.process_page("home", html)
    config = agent.auto_detect()
    result = agent.run_research()

    # MANUAL MODE
    agent = AutoScoutAgent.manual(
        features=["flux ai", "kling ai"],
        niche="AI platform"
    )
    result = agent.run_research()

    # COMPETITOR ANALYSIS
    from market_research_agent import CompetitorCompare
    compare = CompetitorCompare(your_url, your_features)
    compare.add_competitor(url, name, features)
    analysis = compare.analyze()

    # ALERTS
    from market_research_agent import AlertManager
    alerts = AlertManager()
    alerts.add_discord("webhook_url")
    alerts.notify_trend("flux 2.0", score=95, source="Reddit")

    # WEB DASHBOARD
    from market_research_agent import run_dashboard
    run_dashboard(port=5000)
"""

__version__ = "2.3.0"
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

# Live Fetcher (async HTTP with rate limiting)
from .live_fetcher import (
    LiveFetcher,
    FetchResult,
    SiteScanner,
    create_fetcher,
)

# Competitor Comparison
from .competitor_compare import (
    CompetitorCompare,
    CompetitorProfile,
    CompetitiveGap,
    CompetitorAnalysis,
    compare_competitors,
)

# Alerts (Discord, Slack)
from .alerts import (
    AlertManager,
    Alert,
    AlertType,
    AlertPriority,
    DiscordWebhook,
    SlackWebhook,
    create_alert_manager,
)

# Storage (SQLite database)
from .storage import (
    ScanStorage,
    StoredScan,
    KeywordHistory,
    create_storage,
)

# Scheduler (automated scans)
from .scheduler import (
    ScanScheduler,
    ScheduledTask,
    ScheduleInterval,
    TaskResult,
    create_scheduler,
)

# Exporter (CSV, Excel, PDF, HTML, Markdown)
from .exporter import (
    ReportExporter,
    ExportOptions,
    export_report,
    create_exporter,
)

# Web Dashboard
from .web_dashboard import (
    DashboardApp,
    create_flask_app,
    run_dashboard,
    create_app,
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

    # Live Fetcher
    "LiveFetcher",
    "FetchResult",
    "SiteScanner",
    "create_fetcher",

    # Competitor Comparison
    "CompetitorCompare",
    "CompetitorProfile",
    "CompetitiveGap",
    "CompetitorAnalysis",
    "compare_competitors",

    # Alerts
    "AlertManager",
    "Alert",
    "AlertType",
    "AlertPriority",
    "DiscordWebhook",
    "SlackWebhook",
    "create_alert_manager",

    # Storage
    "ScanStorage",
    "StoredScan",
    "KeywordHistory",
    "create_storage",

    # Scheduler
    "ScanScheduler",
    "ScheduledTask",
    "ScheduleInterval",
    "TaskResult",
    "create_scheduler",

    # Exporter
    "ReportExporter",
    "ExportOptions",
    "export_report",
    "create_exporter",

    # Web Dashboard
    "DashboardApp",
    "create_flask_app",
    "run_dashboard",
    "create_app",
]
