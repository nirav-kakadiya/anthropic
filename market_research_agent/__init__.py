"""
Market Research Agent - Automated website analysis and opportunity discovery.

Given a website URL, this agent:
1. Crawls and analyzes the site structure
2. Classifies site type (SaaS, e-commerce, marketplace, etc.)
3. Extracts keywords, features, pricing, and techstack
4. Gathers trend signals from Google Trends and social platforms
5. Scores and prioritizes launch opportunities
6. Outputs structured artifacts (JSON, CSV, markdown playbooks)

NEW: Scout V3 Features
7. Reddit scraping for AI tools/models (r/StableDiffusion, r/comfyui, etc.)
8. Gap analysis comparing discovered keywords vs your features
9. AI model/tool detection (ComfyUI, LoRA, SDXL, Z-Image, etc.)
10. Scout-style formatted output with "Why it's a gap" explanations
"""

__version__ = "2.0.0"
__author__ = "Market Research Agent"

# Core modules
from .orchestrator import MarketResearchAgent
from .models import SiteProfile, Keyword, Opportunity

# New Scout-style modules
from .gap_analyzer import GapAnalyzer, GapResult, GapAnalysisReport
from .reddit_scraper import RedditScanner, get_ai_subreddit_urls, extract_ai_keywords
from .ai_detector import AIDetector, detect_ai_items, get_ai_model_list, get_ai_tool_list
from .scout_formatter import ScoutFormatter, format_scout_output

__all__ = [
    # Core
    "MarketResearchAgent",
    "SiteProfile",
    "Keyword",
    "Opportunity",
    # Gap Analysis
    "GapAnalyzer",
    "GapResult",
    "GapAnalysisReport",
    # Reddit Scraping
    "RedditScanner",
    "get_ai_subreddit_urls",
    "extract_ai_keywords",
    # AI Detection
    "AIDetector",
    "detect_ai_items",
    "get_ai_model_list",
    "get_ai_tool_list",
    # Scout Output
    "ScoutFormatter",
    "format_scout_output",
]
