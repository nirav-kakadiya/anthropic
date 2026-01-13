"""
Market Research Agent - Automated website analysis and opportunity discovery.

Given a website URL, this agent:
1. Crawls and analyzes the site structure
2. Classifies site type (SaaS, e-commerce, marketplace, etc.)
3. Extracts keywords, features, pricing, and techstack
4. Gathers trend signals from Google Trends and social platforms
5. Scores and prioritizes launch opportunities
6. Outputs structured artifacts (JSON, CSV, markdown playbooks)
"""

__version__ = "1.0.0"
__author__ = "Market Research Agent"

from .orchestrator import MarketResearchAgent
from .models import SiteProfile, Keyword, Opportunity

__all__ = ["MarketResearchAgent", "SiteProfile", "Keyword", "Opportunity"]
