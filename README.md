# Market Research Agent

An automated market research system that analyzes websites, extracts keywords, gathers trend signals, and prioritizes launch opportunities.

## Overview

Given a website URL (yours or a competitor's), this agent:

1. **Crawls & Analyzes** - Fetches sitemap, robots.txt, and key pages
2. **Classifies** - Identifies site type (SaaS, e-commerce, marketplace, etc.) and business model
3. **Extracts** - Pulls features, pricing, techstack, integrations, and CTAs
4. **Discovers Keywords** - Uses TF-IDF to extract and score seed keywords
5. **Gathers Trends** - Generates queries for Google Trends, Twitter/X, Reddit, Product Hunt, Hacker News
6. **Prioritizes** - Scores opportunities using composite formula
7. **Generates Playbooks** - Creates MVP specs and 14-day launch checklists

## Architecture

```
market_research_agent/
├── __init__.py          # Package initialization
├── models.py            # Data models (SiteProfile, Keyword, Opportunity)
├── crawler.py           # Website crawler with robots.txt support
├── extractor.py         # HTML content extractor
├── classifier.py        # Site type and business model classifier
├── keyword_extractor.py # TF-IDF keyword extraction
├── trend_gatherer.py    # Trend query generation
├── scorer.py            # Opportunity scoring and playbook generation
├── formatter.py         # Output formatting (JSON, CSV, Markdown)
├── orchestrator.py      # Main agent coordinator
├── cli.py               # Command-line interface
└── prompts.py           # Ready-to-use Claude prompts
```

## Quick Start

### Using with Claude Code

The simplest way to use this agent is through Claude:

```python
from market_research_agent import MarketResearchAgent

# Create agent
agent = MarketResearchAgent(url="https://example.com")

# Get crawl plan (what pages to fetch)
plan = agent.get_crawl_plan()

# After fetching pages with WebFetch, analyze them
results = agent.analyze_content([
    {"url": "https://example.com", "html": homepage_html},
    {"url": "https://example.com/pricing", "html": pricing_html},
])

# Get formatted output
print(results.to_json())
```

### Command Line

```bash
# Get crawl plan
python -m market_research_agent.cli plan https://example.com

# Analyze with HTML file
python -m market_research_agent.cli analyze https://example.com --html page.html

# Get trend queries
python -m market_research_agent.cli trends https://example.com --html page.html

# Export keywords as CSV
python -m market_research_agent.cli keywords https://example.com --format csv
```

## Workflow

### Step 1: Get Crawl Plan

```python
agent = MarketResearchAgent(url="https://example.com")
plan = agent.get_crawl_plan()
# Returns URLs to fetch: homepage, /pricing, /features, etc.
```

### Step 2: Fetch Pages (via WebFetch or requests)

```python
# Using Claude Code's WebFetch
pages = []
for url_info in plan['urls_to_fetch']:
    html = fetch_url(url_info['url'])  # Your fetch function
    pages.append({"url": url_info['url'], "html": html})
```

### Step 3: Analyze Content

```python
results = agent.analyze_content(pages)
```

### Step 4: Get Trend Queries

```python
trend_plan = agent.get_trend_queries()
# Use these queries with WebSearch or social APIs
```

### Step 5: Add Social Metrics (Optional)

```python
from market_research_agent.models import SocialMetrics

social_data = {
    "keyword1": SocialMetrics(
        keyword="keyword1",
        twitter_mentions=150,
        reddit_posts=25,
        # ...
    )
}
results = agent.analyze_content(pages, social_metrics=social_data)
```

### Step 6: Get Output

```python
# JSON output
print(agent.format_output("json"))

# Markdown report
print(agent.format_output("markdown"))

# Human digest
print(agent.format_output("digest"))

# CSV keywords
print(agent.format_output("csv"))
```

## Output Schema

```json
{
  "site_profile": {
    "url": "https://example.com",
    "site_type": "SaaS",
    "business_model": "subscription",
    "features": ["automation", "calendar sync", "api"],
    "pricing": [
      {"tier": "Starter", "price": "$9/mo", "limits": "1 seat"}
    ],
    "techstack_hints": ["React", "Stripe", "AWS"]
  },
  "seed_phrases": ["automate invoicing", "team calendar sync"],
  "expanded_keywords": [
    {
      "keyword": "automate invoices",
      "monthly_volume": 12000,
      "trend_score": 0.85,
      "intent": "commercial",
      "composite_score": 0.72
    }
  ],
  "opportunities": [
    {
      "id": "opp_1",
      "title": "Invoice Automation Tool",
      "value_prop": "A simple tool to automate invoices without complexity",
      "why_now": "rising search interest + no simple integration",
      "dev_days": 7,
      "priority_score": 0.88,
      "mvp_scope": ["Landing page", "Core feature", "Auth", "Dashboard"]
    }
  ]
}
```

## Scoring Formula

Opportunities are scored using:

```
score = 0.35 * trend + 0.25 * volume - 0.20 * competition + 0.20 * feasibility
```

- **Trend (35%)**: Google Trends slope, social momentum
- **Volume (25%)**: Monthly search volume
- **Competition (20%)**: Difficulty score (lower is better)
- **Feasibility (20%)**: Dev effort estimate, intent clarity

## Claude Prompts

Ready-to-use prompts are available in `prompts.py`:

```python
from market_research_agent.prompts import (
    get_site_analysis_prompt,
    get_keyword_expansion_prompt,
    get_social_listening_prompt,
    get_opportunity_prioritization_prompt,
    get_launch_playbook_prompt,
    get_full_analysis_prompt,
)

# Get prompts for Claude
prompt1 = get_site_analysis_prompt("https://example.com")
prompt2 = get_keyword_expansion_prompt(["keyword1", "keyword2"])
# ... use with Claude API or Claude Code
```

## Site Types Detected

- **SaaS**: Software-as-a-service platforms
- **E-commerce**: Online stores
- **Marketplace**: Two-sided platforms
- **Blog**: Content sites
- **Agency**: Service providers
- **Docs**: Documentation sites
- **News**: News/media sites
- **Community**: Forums and communities

## What Gets Extracted

- **Meta**: Title, description, OG tags, Twitter cards
- **Content**: H1/H2/H3 headings, bullet points
- **Features**: Feature lists, benefits
- **Pricing**: Tiers, prices, limits
- **Tech Stack**: React, Vue, Stripe, AWS, etc.
- **Integrations**: Connected services
- **CTAs**: Signup flows, demo requests

## Trend Sources

The agent generates queries for:

- **Google Trends**: 7d/30d/90d trend slopes
- **Twitter/X**: Mentions, hashtags, influencers
- **Reddit**: Subreddits, posts, upvotes
- **Product Hunt**: Recent launches
- **Hacker News**: Discussions
- **YouTube**: Tutorials, reviews

## No-Cost Operation

This agent is designed to work without paid APIs:

- Uses TF-IDF for keyword scoring (no SEMrush/Ahrefs needed)
- Generates queries for free Google Trends lookup
- Works with old.reddit.com for public Reddit data
- Uses Algolia's free HN search API
- Integrates with Claude Code's WebFetch/WebSearch

## Example Output

```
============================================================
MARKET RESEARCH DIGEST
============================================================

Site: https://example.com
Type: SaaS
Keywords Found: 156
Opportunities Identified: 10

----------------------------------------
TOP 3 LAUNCH IDEAS
----------------------------------------

1. Invoice Automation Tool
   Why: rising search interest + no simple integration
   Effort: 7 days
   Score: 88%

2. Calendar Sync Integration
   Why: 30-day trend spike + active Reddit interest
   Effort: 10 days
   Score: 76%

3. API Analytics Dashboard
   Why: high commercial intent + underserved market
   Effort: 8 days
   Score: 71%

----------------------------------------
QUICK NEXT STEPS
----------------------------------------

For 'Invoice Automation Tool':

  1. Landing page with value proposition
  2. Core functionality (1 main feature)
  3. Simple authentication (email/OAuth)

============================================================
```

## License

MIT License
