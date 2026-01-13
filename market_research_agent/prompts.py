"""
Ready-to-use prompts for Claude-based research workflows.

These prompts are designed to be used with Claude to perform the
complete market research workflow.
"""

# System message to set context
SYSTEM_MESSAGE = """
You are a research agent. For each site URL given, produce a structured site_profile,
seed keywords, and a prioritized list of trending opportunities. Use public web sources
only, respect robots.txt, and return JSON and a short human summary. Prioritize recency
(last 90 days). Output must be in the exact JSON schema asked.
"""


def get_site_analysis_prompt(url: str, recency: str = "90", market: str = "global") -> str:
    """
    Prompt 1: Site analysis + seed extraction.

    Run first to analyze the website and extract initial data.
    """
    return f"""Task: Crawl and analyze this website: {url}

Parameters:
- Recency window: {recency} days.
- Market: {market} (English).
- Depth: sitemap + internal links up to depth 2.

Return: JSON with keys:
- site_profile (url, site_type, business_model, features, pricing, techstack_hints)
- seed_phrases (list of 50 extracted keywords/phrases)
- feature_list (detected features)
- pricing_table (if any)

Also return a short human summary (3 bullets).
Do not search social yet — only website content, sitemap, robots.txt, and structured data.

Expected JSON schema:
{{
  "site_profile": {{
    "url": "{url}",
    "site_type": "SaaS|e-commerce|marketplace|blog|agency|docs",
    "business_model": "subscription|freemium|one-time|free",
    "features": ["feature1", "feature2"],
    "pricing": [{{"tier":"name","price":"$X/mo","limits":"..."}}],
    "techstack_hints": ["React","Stripe"],
    "last_crawled": "ISO timestamp"
  }},
  "seed_phrases": ["phrase1", "phrase2"],
  "feature_list": ["feature1", "feature2"],
  "pricing_table": [...],
  "summary": ["bullet1", "bullet2", "bullet3"]
}}"""


def get_keyword_expansion_prompt(seed_phrases: list[str]) -> str:
    """
    Prompt 2: Expand keywords and fetch trend data.
    """
    seeds = ", ".join(f'"{p}"' for p in seed_phrases[:30])
    return f"""Task: Using these seed phrases, expand keywords and fetch trend data:
Seed phrases: [{seeds}]

For each expanded keyword, provide:
- monthly_search_volume (global estimate),
- search_difficulty (0-1 scale),
- trending_score (slope from Google Trends for 7d/30d/90d),
- intent [informational/commercial/transactional].

Return a CSV-style list for top 200 keywords ordered by trending_score desc.
Use past 90 days for trend slope.

Format:
keyword,monthly_volume,difficulty,trend_score,intent
"keyword 1",12000,0.65,0.85,commercial
...

Also include related/long-tail variations for each seed phrase."""


def get_social_listening_prompt(keywords: list[str]) -> str:
    """
    Prompt 3: Social listening across platforms.
    """
    kws = ", ".join(f'"{k}"' for k in keywords[:30])
    return f"""Task: For these keywords, search social signals in past 90 days:
Keywords: [{kws}]

For each keyword gather:
- Twitter/X: mention count, top hashtags (5), top 5 influential accounts mentioning it
- Reddit: relevant subreddits, post count, average upvotes, top 5 posts (title+link)
- Product Hunt: any related launches (title, date, votes)
- Hacker News: thread count and titles

Return a JSON mapping: keyword -> social_metrics

Also extract the top 10 discussion pain points / quotes from these platforms.

Expected format:
{{
  "keyword1": {{
    "twitter": {{"mentions": 150, "hashtags": ["#tag1"], "influencers": ["@user1"]}},
    "reddit": {{"subreddits": ["r/sub1"], "posts": 25, "avg_upvotes": 45, "top_posts": [...]}},
    "producthunt": {{"launches": [{{"title": "...", "date": "...", "votes": 123}}]}},
    "hackernews": {{"threads": 5, "titles": ["Title 1", "Title 2"]}}
  }},
  "pain_points": [
    "Quote or complaint 1",
    "Quote or complaint 2"
  ]
}}"""


def get_opportunity_prioritization_prompt(keywords_with_metrics: str) -> str:
    """
    Prompt 4: Prioritize opportunities and propose MVPs.
    """
    return f"""Task: Using the keyword data below, compute priority scores and return top 10 opportunities.

Keyword data:
{keywords_with_metrics}

Scoring formula:
score = 0.35*normalized_trend + 0.25*norm_volume - 0.20*norm_competition + 0.20*feasibility

For each opportunity include:
- title: Clear product/feature name
- one-sentence value prop
- top 3 keywords to target
- estimated dev_days (LOW/MED/HIGH and numeric 1-14)
- recommended 1-week MVP scope (features to ship in first week)
- go-to-market mechanics (landing page + 2 growth experiments)

Return as JSON array ordered by priority score.

Expected format:
[
  {{
    "id": "opp_1",
    "title": "Opportunity Title",
    "value_prop": "One sentence value proposition",
    "why_now": "Rising interest + market gap",
    "top_keywords": ["kw1", "kw2", "kw3"],
    "dev_effort": "LOW",
    "dev_days": 7,
    "priority_score": 0.88,
    "mvp_scope": ["Core feature 1", "Landing page", "Auth flow", "Basic dashboard"],
    "gtm_mechanics": ["Product Hunt launch", "Reddit community posts", "SEO targeting"]
  }}
]"""


def get_launch_playbook_prompt(opportunities: str) -> str:
    """
    Prompt 5: Generate launch-ready deliverables.
    """
    return f"""Task: For these top 3 opportunities, produce launch playbooks:

Opportunities:
{opportunities}

For each opportunity produce:

1. Landing Page Copy:
   - Main headline
   - 3 variation subheads
   - Hero section copy

2. Ad Copies (3 versions, 30-90 chars each)

3. Email Campaign:
   - 5 onboarding email subject lines
   - First welcome email body (full text)

4. 14-Day Launch Checklist:
   - Day-by-day tasks
   - Mix of technical + marketing
   - Key metrics to track

Return as markdown with clear sections for each opportunity.

Format:
# Opportunity 1: [Title]

## Landing Page
**Headline:** ...
**Subheads:**
1. ...
2. ...
3. ...

## Ad Copies
1. ...
2. ...
3. ...

## Email Campaign
### Subject Lines
1. ...

### First Email
[Full email body]

## 14-Day Checklist
- [ ] Day 1: ...
- [ ] Day 2: ...
..."""


# Combined single-shot prompt for complete analysis
FULL_ANALYSIS_PROMPT = """SYSTEM: You are a research assistant that, given a website URL, will:
1. Crawl public pages and extract feature/pricing/tech info
2. Produce seed keywords and expand them with trend signals (7/30/90 day slopes)
3. Fetch social mentions from X and Reddit (last 90 days)
4. Return prioritized launch ideas with MVP and launch checklist
5. Respect robots.txt and rate limits

USER: Analyze {url}.
Recency window: 90 days.
Market: Global (English).

Return JSON with keys:
- site_profile
- seed_phrases (50 keywords)
- expanded_keywords (top 200 with metrics)
- social_signals (top 50 keywords)
- opportunities (top 10)

Also produce "launch_playbook.md" for top 3 opportunities.
Prioritize ideas that can be prototyped in <=14 dev days.

Focus on:
- Currently trending keywords (rising Google Trends)
- Pain points from Reddit discussions
- Recent Product Hunt launches in the space
- Gaps in competitor offerings
"""


def get_full_analysis_prompt(url: str) -> str:
    """Get the full analysis prompt for a URL."""
    return FULL_ANALYSIS_PROMPT.format(url=url)


# Output schema template
OUTPUT_SCHEMA = {
    "site_profile": {
        "url": "https://example.com",
        "site_type": "SaaS",
        "business_model": "subscription",
        "features": ["automation", "calendar sync", "api"],
        "pricing": [
            {"tier": "Starter", "price": "$9/mo", "limits": "1 seat"},
            {"tier": "Pro", "price": "$29/mo", "limits": "10 seats"}
        ],
        "techstack_hints": ["React", "Stripe", "AWS"],
        "last_crawled": "2024-01-01T00:00:00Z"
    },
    "seed_phrases": ["automate invoicing", "team calendar sync", "api reporting"],
    "top_keywords": [
        {
            "keyword": "automate invoices",
            "monthly_volume": 12000,
            "trend_score": 0.85,
            "competition": 0.6,
            "intent": "commercial",
            "composite_score": 0.72
        }
    ],
    "opportunities": [
        {
            "id": "opp_1",
            "title": "Instant Invoice Automation",
            "why_now": "rising search interest + no simple integration",
            "est_dev_days": 7,
            "priority_score": 0.88,
            "mvp": ["one-click Stripe connect", "generate invoice", "email/send pdf"]
        }
    ]
}
