"""
Site Classifier module - Classifies websites by type and business model.

Detects:
- Site type: SaaS, e-commerce, marketplace, blog, agency, docs, etc.
- Business model: subscription, freemium, one-time, marketplace fees
- Target audience signals
"""

from dataclasses import dataclass
from typing import Optional
from .models import SiteType, BusinessModel
from .extractor import ExtractedContent


@dataclass
class ClassificationResult:
    """Result of site classification."""
    site_type: SiteType
    site_type_confidence: float
    business_model: BusinessModel
    business_model_confidence: float
    target_audience: list[str]
    signals: list[str]  # Evidence that led to classification


class SiteClassifier:
    """
    Classifies websites based on extracted content signals.

    Usage:
        classifier = SiteClassifier()
        result = classifier.classify(extracted_content)
    """

    # Signal patterns for each site type
    SITE_TYPE_SIGNALS = {
        SiteType.SAAS: {
            "keywords": [
                "software", "platform", "dashboard", "analytics", "api",
                "integration", "automate", "workflow", "collaborate", "sync",
                "cloud", "app", "tool", "solution", "service",
            ],
            "url_patterns": ["/api", "/docs", "/integrations", "/features", "/pricing"],
            "cta_patterns": ["start free trial", "get started", "sign up free", "try for free"],
            "pricing_indicators": ["per month", "per user", "per seat", "/mo", "annual"],
        },
        SiteType.ECOMMERCE: {
            "keywords": [
                "shop", "buy", "cart", "checkout", "shipping", "delivery",
                "product", "order", "payment", "store", "collection",
                "sale", "discount", "price", "stock", "inventory",
            ],
            "url_patterns": ["/shop", "/cart", "/products", "/collections", "/checkout"],
            "cta_patterns": ["add to cart", "buy now", "shop now", "add to bag"],
            "pricing_indicators": ["$", "free shipping", "in stock", "out of stock"],
        },
        SiteType.MARKETPLACE: {
            "keywords": [
                "marketplace", "sellers", "buyers", "vendors", "listings",
                "freelance", "hire", "find", "browse", "compare",
                "offer", "bid", "rating", "review", "verified",
            ],
            "url_patterns": ["/sellers", "/buyers", "/listings", "/browse", "/categories"],
            "cta_patterns": ["join as seller", "find freelancer", "post a job", "browse listings"],
            "pricing_indicators": ["commission", "fee", "starting at", "from $"],
        },
        SiteType.BLOG: {
            "keywords": [
                "blog", "article", "post", "author", "category", "tags",
                "read", "published", "minutes read", "comments", "share",
            ],
            "url_patterns": ["/blog", "/posts", "/articles", "/author", "/category"],
            "cta_patterns": ["read more", "subscribe", "newsletter", "follow"],
            "pricing_indicators": [],
        },
        SiteType.AGENCY: {
            "keywords": [
                "agency", "services", "portfolio", "clients", "work",
                "case study", "project", "team", "expertise", "consultation",
                "design", "development", "marketing", "strategy", "creative",
            ],
            "url_patterns": ["/services", "/portfolio", "/work", "/clients", "/case-studies"],
            "cta_patterns": ["contact us", "get a quote", "schedule call", "let's talk"],
            "pricing_indicators": ["custom quote", "contact for pricing", "starting from"],
        },
        SiteType.DOCS: {
            "keywords": [
                "documentation", "guide", "tutorial", "reference", "api",
                "getting started", "quickstart", "sdk", "library", "example",
                "installation", "configuration", "usage", "faq",
            ],
            "url_patterns": ["/docs", "/documentation", "/guide", "/api", "/reference"],
            "cta_patterns": ["get started", "view docs", "read the docs"],
            "pricing_indicators": [],
        },
        SiteType.NEWS: {
            "keywords": [
                "news", "breaking", "latest", "headline", "reporter",
                "journalism", "story", "coverage", "update", "announcement",
            ],
            "url_patterns": ["/news", "/latest", "/headlines", "/breaking"],
            "cta_patterns": ["read more", "subscribe", "breaking news"],
            "pricing_indicators": ["subscription", "premium access"],
        },
        SiteType.COMMUNITY: {
            "keywords": [
                "community", "forum", "discussion", "members", "join",
                "group", "topic", "thread", "reply", "post",
            ],
            "url_patterns": ["/community", "/forum", "/discussions", "/members"],
            "cta_patterns": ["join community", "join now", "become a member"],
            "pricing_indicators": ["free to join", "premium membership"],
        },
    }

    # Business model indicators
    BUSINESS_MODEL_SIGNALS = {
        BusinessModel.SUBSCRIPTION: [
            "per month", "per year", "monthly", "annually", "/mo", "/yr",
            "subscription", "recurring", "cancel anytime", "billed monthly",
        ],
        BusinessModel.FREEMIUM: [
            "free plan", "free tier", "free forever", "upgrade to pro",
            "premium features", "basic free", "starter free",
        ],
        BusinessModel.ONE_TIME: [
            "one-time", "lifetime", "pay once", "no subscription",
            "purchase", "buy now", "single payment",
        ],
        BusinessModel.FREE: [
            "free", "open source", "no cost", "completely free",
            "free to use", "free forever",
        ],
        BusinessModel.MARKETPLACE_FEE: [
            "commission", "platform fee", "transaction fee", "service fee",
            "seller fee", "percentage", "per transaction",
        ],
        BusinessModel.ADVERTISING: [
            "sponsored", "advertisement", "promoted", "ad supported",
            "free with ads", "ad-free premium",
        ],
    }

    # Target audience patterns
    AUDIENCE_PATTERNS = {
        "developers": ["developer", "api", "sdk", "code", "github", "programming"],
        "small_business": ["small business", "smb", "startup", "entrepreneur"],
        "enterprise": ["enterprise", "large team", "organization", "corporate"],
        "marketers": ["marketing", "seo", "campaign", "analytics", "conversion"],
        "designers": ["design", "creative", "ui", "ux", "figma", "sketch"],
        "sales": ["sales", "crm", "leads", "pipeline", "deals", "prospects"],
        "hr": ["hr", "hiring", "recruitment", "employee", "workforce"],
        "finance": ["finance", "accounting", "invoice", "expense", "budget"],
        "ecommerce_owners": ["store owner", "merchant", "seller", "online store"],
        "content_creators": ["creator", "content", "video", "podcast", "blog"],
        "freelancers": ["freelance", "contractor", "independent", "gig"],
    }

    def __init__(self):
        pass

    def _count_matches(self, text: str, patterns: list[str]) -> int:
        """Count how many patterns match in the text."""
        text_lower = text.lower()
        return sum(1 for p in patterns if p.lower() in text_lower)

    def _get_all_text(self, content: ExtractedContent) -> str:
        """Get all text content concatenated."""
        parts = [
            content.meta.title,
            content.meta.description,
            " ".join(content.h1),
            " ".join(content.h2),
            " ".join(content.h3),
            " ".join(content.bullet_points),
            " ".join(content.features),
            " ".join(content.ctas),
        ]
        return " ".join(parts)

    def classify_site_type(self, content: ExtractedContent) -> tuple[SiteType, float, list[str]]:
        """
        Classify the site type based on content signals.

        Returns:
            Tuple of (SiteType, confidence score, list of evidence signals)
        """
        all_text = self._get_all_text(content)
        scores: dict[SiteType, float] = {}
        evidence: dict[SiteType, list[str]] = {}

        for site_type, signals in self.SITE_TYPE_SIGNALS.items():
            score = 0.0
            type_evidence = []

            # Check keywords (weight: 0.4)
            keyword_matches = self._count_matches(all_text, signals["keywords"])
            if keyword_matches > 0:
                keyword_score = min(keyword_matches / 5, 1.0) * 0.4
                score += keyword_score
                type_evidence.append(f"{keyword_matches} keyword matches")

            # Check URL patterns (weight: 0.2)
            url_matches = sum(1 for p in signals["url_patterns"]
                             if any(p in page for page in [content.url]))
            if url_matches > 0:
                score += 0.2
                type_evidence.append(f"{url_matches} URL pattern matches")

            # Check CTA patterns (weight: 0.2)
            cta_text = " ".join(content.ctas).lower()
            cta_matches = self._count_matches(cta_text, signals["cta_patterns"])
            if cta_matches > 0:
                score += min(cta_matches / 2, 1.0) * 0.2
                type_evidence.append(f"{cta_matches} CTA matches")

            # Check pricing indicators (weight: 0.2)
            if signals["pricing_indicators"]:
                pricing_text = " ".join(str(p.price) for p in content.pricing_tiers)
                pricing_text += " " + all_text
                pricing_matches = self._count_matches(pricing_text, signals["pricing_indicators"])
                if pricing_matches > 0:
                    score += min(pricing_matches / 3, 1.0) * 0.2
                    type_evidence.append(f"{pricing_matches} pricing indicator matches")

            scores[site_type] = score
            evidence[site_type] = type_evidence

        # Get the highest scoring type
        if scores:
            best_type = max(scores, key=scores.get)
            confidence = scores[best_type]
            return best_type, confidence, evidence.get(best_type, [])

        return SiteType.UNKNOWN, 0.0, []

    def classify_business_model(self, content: ExtractedContent) -> tuple[BusinessModel, float]:
        """
        Classify the business model based on pricing and content signals.

        Returns:
            Tuple of (BusinessModel, confidence score)
        """
        all_text = self._get_all_text(content)

        # Add pricing text
        pricing_text = " ".join(
            f"{p.tier} {p.price} {p.limits}"
            for p in content.pricing_tiers
        )
        all_text += " " + pricing_text

        scores: dict[BusinessModel, float] = {}

        for model, signals in self.BUSINESS_MODEL_SIGNALS.items():
            matches = self._count_matches(all_text, signals)
            scores[model] = min(matches / 3, 1.0)

        # Boost subscription if multiple pricing tiers exist
        if len(content.pricing_tiers) >= 2:
            scores[BusinessModel.SUBSCRIPTION] = scores.get(BusinessModel.SUBSCRIPTION, 0) + 0.3

        # Get the highest scoring model
        if scores:
            best_model = max(scores, key=scores.get)
            return best_model, min(scores[best_model], 1.0)

        return BusinessModel.UNKNOWN, 0.0

    def identify_target_audience(self, content: ExtractedContent) -> list[str]:
        """Identify target audience segments."""
        all_text = self._get_all_text(content)
        audiences = []

        for audience, patterns in self.AUDIENCE_PATTERNS.items():
            matches = self._count_matches(all_text, patterns)
            if matches >= 2:
                audiences.append(audience)

        return audiences

    def classify(self, content: ExtractedContent) -> ClassificationResult:
        """
        Perform full site classification.

        Args:
            content: Extracted content from the site

        Returns:
            ClassificationResult with all classification details
        """
        site_type, type_confidence, signals = self.classify_site_type(content)
        business_model, model_confidence = self.classify_business_model(content)
        target_audience = self.identify_target_audience(content)

        return ClassificationResult(
            site_type=site_type,
            site_type_confidence=type_confidence,
            business_model=business_model,
            business_model_confidence=model_confidence,
            target_audience=target_audience,
            signals=signals
        )


def generate_research_plan(classification: ClassificationResult, content: ExtractedContent) -> dict:
    """
    Generate a research plan based on site classification.

    Returns a dictionary with recommended searches and focus areas.
    """
    plan = {
        "site_type": classification.site_type.value,
        "primary_searches": [],
        "social_platforms": [],
        "trend_keywords": [],
        "competitor_focus": [],
        "pain_point_queries": [],
    }

    # Base searches for all types
    plan["social_platforms"] = ["twitter", "reddit", "producthunt", "hackernews"]
    plan["trend_keywords"] = content.features[:10]

    if classification.site_type == SiteType.SAAS:
        plan["primary_searches"] = [
            "competitor features comparison",
            "integrations and API demand",
            "pain keywords (how to automate X, avoid Y)",
            "recent launches and funding news",
            "user reviews and complaints",
        ]
        plan["pain_point_queries"] = [
            "how to automate {feature}",
            "{feature} alternative",
            "{feature} vs {competitor}",
            "best {category} software",
        ]
        plan["competitor_focus"] = [
            "feature gaps",
            "pricing comparison",
            "integration ecosystem",
            "user sentiment",
        ]

    elif classification.site_type == SiteType.ECOMMERCE:
        plan["primary_searches"] = [
            "product-level trends",
            "seasonal demand patterns",
            "best-seller lists in category",
            "influencer reviews",
            "Reddit product threads",
        ]
        plan["pain_point_queries"] = [
            "best {product} review",
            "{product} alternative",
            "where to buy {product}",
            "{product} discount code",
        ]
        plan["competitor_focus"] = [
            "pricing strategy",
            "shipping and returns",
            "product range",
            "customer reviews",
        ]

    elif classification.site_type == SiteType.MARKETPLACE:
        plan["primary_searches"] = [
            "supply side friction points",
            "onboarding friction",
            "pricing model comparisons",
            "underserved categories",
            "trust and verification signals",
        ]
        plan["pain_point_queries"] = [
            "how to find {service} provider",
            "best freelance {category}",
            "{marketplace} fees too high",
            "{marketplace} alternative",
        ]
        plan["competitor_focus"] = [
            "fee structure",
            "seller onboarding",
            "buyer experience",
            "trust mechanisms",
        ]

    elif classification.site_type == SiteType.BLOG:
        plan["primary_searches"] = [
            "trending topics in niche",
            "high-volume informational keywords",
            "content gaps analysis",
            "backlink opportunities",
        ]
        plan["pain_point_queries"] = [
            "how to {topic}",
            "{topic} guide",
            "{topic} tutorial",
            "best {topic} resources",
        ]

    elif classification.site_type == SiteType.AGENCY:
        plan["primary_searches"] = [
            "service demand trends",
            "pricing benchmarks",
            "client pain points",
            "skill demand changes",
        ]
        plan["pain_point_queries"] = [
            "best {service} agency",
            "{service} agency cost",
            "hire {service} expert",
        ]

    # Add general searches
    plan["general_searches"] = [
        "Recent Product Hunt launches in category",
        "Hacker News discussions",
        "Reddit community sentiment",
        "Twitter/X trending discussions",
        "Google Trends for seed keywords",
        "SERP features and changes",
    ]

    return plan
