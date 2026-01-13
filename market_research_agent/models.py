"""
Data models for the Market Research Agent.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
from enum import Enum
from datetime import datetime
import json


class SiteType(Enum):
    """Classification of website types."""
    SAAS = "SaaS"
    ECOMMERCE = "e-commerce"
    MARKETPLACE = "marketplace"
    BLOG = "blog"
    AGENCY = "agency"
    DOCS = "documentation"
    PORTFOLIO = "portfolio"
    NEWS = "news"
    COMMUNITY = "community"
    UNKNOWN = "unknown"


class BusinessModel(Enum):
    """Business model types."""
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one-time"
    FREEMIUM = "freemium"
    FREE = "free"
    MARKETPLACE_FEE = "marketplace-fee"
    ADVERTISING = "advertising"
    UNKNOWN = "unknown"


class Intent(Enum):
    """Search intent classification."""
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class DevEffort(Enum):
    """Development effort estimation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PricingTier:
    """Pricing tier information."""
    tier: str
    price: str
    limits: str = ""
    features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SiteProfile:
    """Complete profile of an analyzed website."""
    url: str
    site_type: SiteType = SiteType.UNKNOWN
    business_model: BusinessModel = BusinessModel.UNKNOWN
    title: str = ""
    description: str = ""
    features: list[str] = field(default_factory=list)
    pricing: list[PricingTier] = field(default_factory=list)
    techstack_hints: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    funnel_points: list[str] = field(default_factory=list)
    target_audience: list[str] = field(default_factory=list)
    pages_crawled: list[str] = field(default_factory=list)
    last_crawled: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "site_type": self.site_type.value,
            "business_model": self.business_model.value,
            "title": self.title,
            "description": self.description,
            "features": self.features,
            "pricing": [p.to_dict() for p in self.pricing],
            "techstack_hints": self.techstack_hints,
            "integrations": self.integrations,
            "funnel_points": self.funnel_points,
            "target_audience": self.target_audience,
            "pages_crawled": self.pages_crawled,
            "last_crawled": self.last_crawled
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class Keyword:
    """Keyword with associated metrics."""
    keyword: str
    source: str = ""  # Where it was found (page/heading)
    intent: Intent = Intent.INFORMATIONAL
    tfidf_score: float = 0.0
    monthly_volume: int = 0
    cpc: float = 0.0
    difficulty: float = 0.0
    trend_score: float = 0.0  # Slope from Google Trends
    trend_7d: float = 0.0
    trend_30d: float = 0.0
    trend_90d: float = 0.0
    social_mentions: int = 0
    composite_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "keyword": self.keyword,
            "source": self.source,
            "intent": self.intent.value,
            "tfidf_score": round(self.tfidf_score, 4),
            "monthly_volume": self.monthly_volume,
            "cpc": round(self.cpc, 2),
            "difficulty": round(self.difficulty, 2),
            "trend_score": round(self.trend_score, 4),
            "trend_7d": round(self.trend_7d, 4),
            "trend_30d": round(self.trend_30d, 4),
            "trend_90d": round(self.trend_90d, 4),
            "social_mentions": self.social_mentions,
            "composite_score": round(self.composite_score, 4)
        }

    def to_csv_row(self) -> str:
        return ",".join([
            self.keyword,
            str(self.monthly_volume),
            str(round(self.difficulty, 2)),
            str(round(self.trend_score, 4)),
            self.intent.value,
            str(round(self.composite_score, 4))
        ])


@dataclass
class SocialMetrics:
    """Social media metrics for a keyword or topic."""
    keyword: str
    twitter_mentions: int = 0
    twitter_hashtags: list[str] = field(default_factory=list)
    twitter_influencers: list[str] = field(default_factory=list)
    reddit_subreddits: list[str] = field(default_factory=list)
    reddit_posts: int = 0
    reddit_avg_upvotes: float = 0.0
    reddit_top_posts: list[dict] = field(default_factory=list)
    producthunt_launches: list[dict] = field(default_factory=list)
    hackernews_threads: int = 0
    hackernews_titles: list[str] = field(default_factory=list)
    pain_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Opportunity:
    """A prioritized launch opportunity."""
    id: str
    title: str
    value_prop: str
    why_now: str
    top_keywords: list[str] = field(default_factory=list)
    dev_effort: DevEffort = DevEffort.MEDIUM
    dev_days: int = 7
    priority_score: float = 0.0
    mvp_scope: list[str] = field(default_factory=list)
    gtm_mechanics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "value_prop": self.value_prop,
            "why_now": self.why_now,
            "top_keywords": self.top_keywords,
            "dev_effort": self.dev_effort.value,
            "dev_days": self.dev_days,
            "priority_score": round(self.priority_score, 4),
            "mvp_scope": self.mvp_scope,
            "gtm_mechanics": self.gtm_mechanics
        }


@dataclass
class LaunchPlaybook:
    """Complete launch playbook for an opportunity."""
    opportunity_id: str
    headline: str
    subheads: list[str] = field(default_factory=list)
    ad_copies: list[str] = field(default_factory=list)
    email_subjects: list[str] = field(default_factory=list)
    first_email_body: str = ""
    launch_checklist: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self) -> str:
        md = f"# Launch Playbook: {self.headline}\n\n"

        md += "## Headlines & Variations\n\n"
        md += f"**Main Headline:** {self.headline}\n\n"
        md += "**Subhead Variations:**\n"
        for i, sub in enumerate(self.subheads, 1):
            md += f"{i}. {sub}\n"

        md += "\n## Ad Copies (30-90 chars)\n\n"
        for i, ad in enumerate(self.ad_copies, 1):
            md += f"{i}. {ad}\n"

        md += "\n## Email Campaign\n\n"
        md += "### Subject Lines:\n"
        for i, subj in enumerate(self.email_subjects, 1):
            md += f"{i}. {subj}\n"

        md += f"\n### First Email Body:\n\n{self.first_email_body}\n"

        md += "\n## 14-Day Launch Checklist\n\n"
        for item in self.launch_checklist:
            status = "[ ]" if not item.get("done", False) else "[x]"
            md += f"- {status} **Day {item.get('day', '?')}:** {item.get('task', '')}\n"

        return md


@dataclass
class ResearchOutput:
    """Complete research output bundle."""
    site_profile: SiteProfile
    seed_phrases: list[str] = field(default_factory=list)
    expanded_keywords: list[Keyword] = field(default_factory=list)
    social_signals: dict[str, SocialMetrics] = field(default_factory=dict)
    opportunities: list[Opportunity] = field(default_factory=list)
    playbooks: list[LaunchPlaybook] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "site_profile": self.site_profile.to_dict(),
            "seed_phrases": self.seed_phrases,
            "expanded_keywords": [k.to_dict() for k in self.expanded_keywords],
            "social_signals": {k: v.to_dict() for k, v in self.social_signals.items()},
            "opportunities": [o.to_dict() for o in self.opportunities]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
