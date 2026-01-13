"""
Scorer/Prioritizer module - Scores keywords and generates opportunity rankings.

Scoring formula:
score = 0.35 * normalized_trend + 0.25 * norm_volume - 0.20 * norm_competition + 0.20 * feasibility

Creates prioritized opportunities with MVP specs.
"""

from dataclasses import dataclass, field
from typing import Optional
from .models import (
    Keyword, Opportunity, DevEffort, Intent,
    SocialMetrics, SiteType, LaunchPlaybook
)


@dataclass
class ScoringWeights:
    """Configurable weights for opportunity scoring."""
    trend_weight: float = 0.35
    volume_weight: float = 0.25
    competition_weight: float = 0.20  # Negative impact
    feasibility_weight: float = 0.20
    recency_weight: float = 0.10  # Bonus for recent trends

    def validate(self) -> bool:
        """Ensure weights sum to approximately 1.0."""
        total = (
            self.trend_weight +
            self.volume_weight +
            self.competition_weight +
            self.feasibility_weight
        )
        return 0.95 <= total <= 1.05


class KeywordScorer:
    """
    Scores keywords based on multiple factors.

    Usage:
        scorer = KeywordScorer()
        scored_keywords = scorer.score_keywords(keywords, social_metrics)
    """

    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()

    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to 0-1 range."""
        if max_val <= min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))

    def calculate_composite_score(
        self,
        keyword: Keyword,
        social_metrics: Optional[SocialMetrics] = None,
        max_volume: int = 100000,
        max_social: int = 1000
    ) -> float:
        """
        Calculate composite score for a keyword.

        Args:
            keyword: Keyword with metrics
            social_metrics: Optional social metrics for the keyword
            max_volume: Maximum expected search volume for normalization
            max_social: Maximum expected social mentions for normalization

        Returns:
            Composite score between 0 and 1
        """
        # Normalize trend score (already 0-1 typically)
        norm_trend = self.normalize(keyword.trend_score, 0, 1)

        # Use 30-day trend slope if available
        if keyword.trend_30d != 0:
            norm_trend = (norm_trend + self.normalize(keyword.trend_30d + 1, 0, 2)) / 2

        # Normalize volume
        norm_volume = self.normalize(keyword.monthly_volume, 0, max_volume)

        # Normalize competition (inverted - lower is better)
        norm_competition = self.normalize(keyword.difficulty, 0, 1)

        # Calculate feasibility based on intent and complexity
        feasibility = self._estimate_feasibility(keyword)

        # Add social signals if available
        social_bonus = 0.0
        if social_metrics:
            total_mentions = (
                social_metrics.twitter_mentions +
                social_metrics.reddit_posts +
                social_metrics.hackernews_threads
            )
            social_bonus = self.normalize(total_mentions, 0, max_social) * 0.1

        # Calculate composite score
        score = (
            self.weights.trend_weight * norm_trend +
            self.weights.volume_weight * norm_volume -
            self.weights.competition_weight * norm_competition +
            self.weights.feasibility_weight * feasibility +
            social_bonus
        )

        return max(0.0, min(1.0, score))

    def _estimate_feasibility(self, keyword: Keyword) -> float:
        """
        Estimate feasibility based on keyword characteristics.

        Higher feasibility for:
        - Shorter phrases (simpler concepts)
        - Transactional/commercial intent (clear business case)
        - High TF-IDF (relevant to the site)
        """
        feasibility = 0.5  # Base

        # Shorter phrases are often simpler to address
        word_count = len(keyword.keyword.split())
        if word_count <= 2:
            feasibility += 0.2
        elif word_count <= 3:
            feasibility += 0.1

        # Commercial/transactional intent is more actionable
        if keyword.intent in (Intent.TRANSACTIONAL, Intent.COMMERCIAL):
            feasibility += 0.2
        elif keyword.intent == Intent.INFORMATIONAL:
            feasibility += 0.1

        # High TF-IDF means it's relevant to the site
        if keyword.tfidf_score > 0.5:
            feasibility += 0.1

        return min(1.0, feasibility)

    def score_keywords(
        self,
        keywords: list[Keyword],
        social_metrics: Optional[dict[str, SocialMetrics]] = None
    ) -> list[Keyword]:
        """
        Score a list of keywords and update their composite scores.

        Args:
            keywords: List of keywords to score
            social_metrics: Optional mapping of keyword -> SocialMetrics

        Returns:
            Keywords sorted by composite score (descending)
        """
        # Find max values for normalization
        max_volume = max((k.monthly_volume for k in keywords), default=100000)
        max_volume = max(max_volume, 1000)  # Minimum threshold

        if social_metrics:
            max_social = max(
                sum([
                    m.twitter_mentions,
                    m.reddit_posts,
                    m.hackernews_threads
                ])
                for m in social_metrics.values()
            ) if social_metrics else 1000
        else:
            max_social = 1000

        for keyword in keywords:
            metrics = social_metrics.get(keyword.keyword) if social_metrics else None
            keyword.composite_score = self.calculate_composite_score(
                keyword, metrics, max_volume, max_social
            )

            # Also update social mentions count
            if metrics:
                keyword.social_mentions = (
                    metrics.twitter_mentions +
                    metrics.reddit_posts
                )

        # Sort by composite score
        keywords.sort(key=lambda k: k.composite_score, reverse=True)

        return keywords


class OpportunityGenerator:
    """
    Generates prioritized opportunities from scored keywords.

    Usage:
        generator = OpportunityGenerator(site_type=SiteType.SAAS)
        opportunities = generator.generate(keywords, social_metrics)
    """

    # MVP templates by opportunity type
    MVP_TEMPLATES = {
        "tool": [
            "Landing page with value proposition",
            "Core functionality (1 main feature)",
            "Simple authentication (email/OAuth)",
            "Basic dashboard or output view",
        ],
        "integration": [
            "OAuth connection to target service",
            "Core data sync functionality",
            "Simple configuration UI",
            "Status/success notifications",
        ],
        "automation": [
            "Trigger configuration interface",
            "Core automation logic",
            "Action/output handling",
            "Run history/logs view",
        ],
        "analytics": [
            "Data collection endpoint",
            "Processing/aggregation logic",
            "Dashboard with key metrics",
            "Export functionality (CSV/PDF)",
        ],
        "content": [
            "Content generation/curation engine",
            "Simple editing interface",
            "Publishing workflow",
            "Basic analytics on content",
        ],
    }

    # GTM mechanics templates
    GTM_TEMPLATES = [
        "Landing page SEO (target top 5 keywords)",
        "Launch on Product Hunt",
        "Post in relevant Reddit communities",
        "Twitter/X launch announcement",
        "Direct outreach to niche influencers",
        "Content marketing (how-to guides)",
        "Email waitlist with early access",
        "Free tier to drive word-of-mouth",
    ]

    def __init__(self, site_type: SiteType = SiteType.SAAS):
        self.site_type = site_type
        self.opportunity_counter = 0

    def _estimate_dev_days(self, keyword: Keyword, opportunity_type: str) -> tuple[DevEffort, int]:
        """Estimate development effort for an opportunity."""
        # Base estimates by type
        base_days = {
            "tool": 7,
            "integration": 10,
            "automation": 5,
            "analytics": 8,
            "content": 4,
        }

        days = base_days.get(opportunity_type, 7)

        # Adjust based on keyword complexity
        word_count = len(keyword.keyword.split())
        if word_count >= 4:
            days += 3

        # Adjust based on intent
        if keyword.intent == Intent.TRANSACTIONAL:
            days += 2  # Needs payment integration

        # Determine effort category
        if days <= 5:
            effort = DevEffort.LOW
        elif days <= 10:
            effort = DevEffort.MEDIUM
        else:
            effort = DevEffort.HIGH

        return effort, days

    def _classify_opportunity_type(self, keyword: Keyword) -> str:
        """Classify the type of opportunity based on keyword."""
        kw_lower = keyword.keyword.lower()

        if any(w in kw_lower for w in ["api", "connect", "sync", "integrate"]):
            return "integration"
        elif any(w in kw_lower for w in ["automate", "automatic", "schedule", "trigger"]):
            return "automation"
        elif any(w in kw_lower for w in ["analytics", "report", "dashboard", "metrics", "track"]):
            return "analytics"
        elif any(w in kw_lower for w in ["content", "generate", "create", "write"]):
            return "content"
        else:
            return "tool"

    def _generate_value_prop(self, keyword: Keyword, opportunity_type: str) -> str:
        """Generate a value proposition based on keyword and type."""
        templates = {
            "tool": "A simple tool to {keyword} without the complexity",
            "integration": "Connect and {keyword} in one click",
            "automation": "Automatically {keyword} while you sleep",
            "analytics": "Get clear insights into {keyword} performance",
            "content": "Create {keyword} content 10x faster",
        }

        template = templates.get(opportunity_type, "Simplify {keyword} for everyone")
        return template.format(keyword=keyword.keyword)

    def _generate_why_now(self, keyword: Keyword, social_metrics: Optional[SocialMetrics] = None) -> str:
        """Generate the 'why now' rationale."""
        reasons = []

        if keyword.trend_score > 0.5:
            reasons.append("rising search interest")

        if keyword.trend_30d > 0.3:
            reasons.append("30-day trend spike")

        if social_metrics:
            if social_metrics.twitter_mentions > 100:
                reasons.append("active Twitter discussion")
            if social_metrics.reddit_posts > 20:
                reasons.append("growing Reddit interest")
            if social_metrics.producthunt_launches:
                reasons.append("competitors launching in this space")

        if keyword.intent == Intent.TRANSACTIONAL:
            reasons.append("high commercial intent")

        if not reasons:
            reasons.append("underserved market need")

        return " + ".join(reasons[:3])

    def generate(
        self,
        keywords: list[Keyword],
        social_metrics: Optional[dict[str, SocialMetrics]] = None,
        top_n: int = 10
    ) -> list[Opportunity]:
        """
        Generate prioritized opportunities from scored keywords.

        Args:
            keywords: Scored keywords (should be pre-sorted by score)
            social_metrics: Optional social metrics mapping
            top_n: Number of opportunities to generate

        Returns:
            List of Opportunity objects sorted by priority
        """
        opportunities = []
        seen_types = set()  # Ensure diversity

        for keyword in keywords[:top_n * 2]:  # Consider more candidates
            if len(opportunities) >= top_n:
                break

            opp_type = self._classify_opportunity_type(keyword)

            # Skip if we have too many of this type
            type_count = sum(1 for o in opportunities if opp_type in o.title.lower())
            if type_count >= 3:
                continue

            self.opportunity_counter += 1
            opp_id = f"opp_{self.opportunity_counter}"

            effort, days = self._estimate_dev_days(keyword, opp_type)
            metrics = social_metrics.get(keyword.keyword) if social_metrics else None

            # Build title
            title_templates = {
                "tool": "{keyword} Tool",
                "integration": "{keyword} Integration",
                "automation": "{keyword} Automation",
                "analytics": "{keyword} Analytics",
                "content": "{keyword} Generator",
            }
            title = title_templates.get(opp_type, "{keyword} Solution").format(
                keyword=keyword.keyword.title()
            )

            opportunity = Opportunity(
                id=opp_id,
                title=title,
                value_prop=self._generate_value_prop(keyword, opp_type),
                why_now=self._generate_why_now(keyword, metrics),
                top_keywords=[keyword.keyword] + [
                    k.keyword for k in keywords[1:4]
                    if k.keyword != keyword.keyword
                ][:2],
                dev_effort=effort,
                dev_days=days,
                priority_score=keyword.composite_score,
                mvp_scope=self.MVP_TEMPLATES.get(opp_type, self.MVP_TEMPLATES["tool"])[:4],
                gtm_mechanics=self.GTM_TEMPLATES[:4]
            )

            opportunities.append(opportunity)

        # Sort by priority score
        opportunities.sort(key=lambda o: o.priority_score, reverse=True)

        return opportunities


class PlaybookGenerator:
    """
    Generates launch playbooks for top opportunities.

    Usage:
        generator = PlaybookGenerator()
        playbooks = generator.generate(opportunities)
    """

    def __init__(self):
        pass

    def _generate_headlines(self, opportunity: Opportunity) -> tuple[str, list[str]]:
        """Generate landing page headlines."""
        main = f"{opportunity.title}: {opportunity.value_prop}"

        variations = [
            f"Stop struggling with {opportunity.top_keywords[0]}",
            f"The easiest way to {opportunity.top_keywords[0]}",
            f"Finally, {opportunity.top_keywords[0]} made simple",
        ]

        return main, variations

    def _generate_ad_copies(self, opportunity: Opportunity) -> list[str]:
        """Generate short ad copies (30-90 chars)."""
        kw = opportunity.top_keywords[0] if opportunity.top_keywords else "your workflow"

        return [
            f"Try {opportunity.title} free",
            f"Automate {kw} in seconds",
            f"The #1 {kw} solution",
            f"Save hours on {kw}",
            f"Join 1000+ users who {kw} faster",
        ][:5]

    def _generate_email_campaign(self, opportunity: Opportunity) -> tuple[list[str], str]:
        """Generate email subject lines and first email body."""
        subjects = [
            f"You're in! Welcome to {opportunity.title}",
            f"Quick start: Get value from {opportunity.title} in 5 min",
            f"One tip to get the most from {opportunity.title}",
            f"What others are building with {opportunity.title}",
            f"Upgrade to Pro: Unlock all features",
        ]

        body = f"""Hi {{first_name}},

Welcome to {opportunity.title}!

You signed up because you want to {opportunity.value_prop.lower()}.

Here's how to get started in under 5 minutes:

1. Log in to your dashboard
2. {opportunity.mvp_scope[0] if opportunity.mvp_scope else "Set up your first project"}
3. {opportunity.mvp_scope[1] if len(opportunity.mvp_scope) > 1 else "Configure your preferences"}
4. See results immediately

Need help? Reply to this email or check our quick start guide.

Best,
The {opportunity.title} Team

P.S. We're building in public! Follow us for updates and new features.
"""
        return subjects, body

    def _generate_launch_checklist(self, opportunity: Opportunity) -> list[dict]:
        """Generate a 14-day launch checklist."""
        checklist = [
            {"day": 1, "task": "Finalize landing page copy and design", "category": "marketing"},
            {"day": 1, "task": "Set up analytics (GA4, Mixpanel)", "category": "technical"},
            {"day": 2, "task": "Complete core feature development", "category": "technical"},
            {"day": 3, "task": "Set up authentication and onboarding flow", "category": "technical"},
            {"day": 4, "task": "Integrate payment (Stripe)", "category": "technical"},
            {"day": 5, "task": "Internal QA and bug fixes", "category": "technical"},
            {"day": 6, "task": "Set up email sequences (welcome, onboarding)", "category": "marketing"},
            {"day": 7, "task": "Soft launch to early access list", "category": "marketing"},
            {"day": 8, "task": "Collect feedback and iterate", "category": "product"},
            {"day": 9, "task": "Prepare Product Hunt assets (logo, images, video)", "category": "marketing"},
            {"day": 10, "task": "Schedule Product Hunt launch", "category": "marketing"},
            {"day": 11, "task": "Write launch blog post and social content", "category": "marketing"},
            {"day": 12, "task": "Reach out to niche communities and influencers", "category": "marketing"},
            {"day": 13, "task": "Product Hunt launch day!", "category": "marketing"},
            {"day": 14, "task": "Post-launch: Analyze metrics, respond to feedback", "category": "product"},
        ]

        return checklist

    def generate(self, opportunities: list[Opportunity], top_n: int = 3) -> list[LaunchPlaybook]:
        """
        Generate launch playbooks for top opportunities.

        Args:
            opportunities: Ranked opportunities
            top_n: Number of playbooks to generate

        Returns:
            List of LaunchPlaybook objects
        """
        playbooks = []

        for opp in opportunities[:top_n]:
            headline, subheads = self._generate_headlines(opp)
            ad_copies = self._generate_ad_copies(opp)
            email_subjects, email_body = self._generate_email_campaign(opp)
            checklist = self._generate_launch_checklist(opp)

            playbook = LaunchPlaybook(
                opportunity_id=opp.id,
                headline=headline,
                subheads=subheads,
                ad_copies=ad_copies,
                email_subjects=email_subjects,
                first_email_body=email_body,
                launch_checklist=checklist
            )

            playbooks.append(playbook)

        return playbooks
