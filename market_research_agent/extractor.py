"""
Parser/Extractor module - Extracts structured data from HTML content.

Extracts:
- Meta tags (title, description, OG, Twitter cards)
- Headings (H1, H2, H3)
- JSON-LD structured data
- Pricing information
- Feature lists
- Forms and CTAs
- Techstack hints
"""

import re
import json
from dataclasses import dataclass, field
from typing import Optional
from .models import PricingTier


@dataclass
class ExtractedMeta:
    """Extracted meta information from a page."""
    title: str = ""
    description: str = ""
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = ""
    twitter_title: str = ""
    twitter_description: str = ""
    canonical: str = ""
    lang: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class ExtractedContent:
    """All extracted content from a page."""
    url: str
    meta: ExtractedMeta = field(default_factory=ExtractedMeta)
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    h3: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    bullet_points: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    images: list[dict] = field(default_factory=list)
    forms: list[dict] = field(default_factory=list)
    ctas: list[str] = field(default_factory=list)
    json_ld: list[dict] = field(default_factory=list)
    pricing_tiers: list[PricingTier] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    integrations: list[str] = field(default_factory=list)
    techstack_hints: list[str] = field(default_factory=list)


class HTMLExtractor:
    """
    Extracts structured data from HTML content.

    Usage:
        extractor = HTMLExtractor()
        content = extractor.extract(html, url)
    """

    # Common tech signatures in HTML/JS
    TECH_SIGNATURES = {
        "react": [r"react", r"_reactRoot", r"__NEXT_DATA__", r"next\.js"],
        "vue": [r"vue", r"v-if", r"v-for", r"nuxt"],
        "angular": [r"ng-", r"angular", r"zone\.js"],
        "svelte": [r"svelte", r"sveltekit"],
        "stripe": [r"stripe\.com", r"js\.stripe\.com"],
        "intercom": [r"intercom", r"widget\.intercom\.io"],
        "hubspot": [r"hubspot", r"hs-scripts"],
        "segment": [r"segment\.com", r"analytics\.js"],
        "google_analytics": [r"google-analytics", r"gtag", r"ga\("],
        "mixpanel": [r"mixpanel"],
        "amplitude": [r"amplitude"],
        "hotjar": [r"hotjar"],
        "sentry": [r"sentry\.io", r"sentry-"],
        "aws": [r"amazonaws\.com", r"cloudfront\.net"],
        "cloudflare": [r"cloudflare", r"cf-ray"],
        "vercel": [r"vercel", r"\.vercel\.app"],
        "netlify": [r"netlify"],
        "heroku": [r"herokuapp\.com"],
        "wordpress": [r"wp-content", r"wp-includes"],
        "shopify": [r"shopify", r"cdn\.shopify"],
        "webflow": [r"webflow"],
        "tailwind": [r"tailwindcss", r"tailwind\."],
        "bootstrap": [r"bootstrap"],
    }

    # Patterns for CTA detection
    CTA_PATTERNS = [
        r"get\s+started",
        r"sign\s*up",
        r"start\s+free",
        r"try\s+free",
        r"book\s+demo",
        r"request\s+demo",
        r"contact\s+us",
        r"buy\s+now",
        r"subscribe",
        r"join\s+now",
        r"learn\s+more",
        r"start\s+trial",
        r"free\s+trial",
    ]

    # Integration name patterns
    INTEGRATION_PATTERNS = [
        r"integrates?\s+with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"connect(?:s|ed)?\s+(?:to|with)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"works?\s+with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]

    def __init__(self):
        pass

    def clean_text(self, text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove HTML entities
        text = re.sub(r'&[a-z]+;', ' ', text)
        return text.strip()

    def extract_tag_content(self, html: str, tag: str, attr: Optional[str] = None, attr_val: Optional[str] = None) -> list[str]:
        """Extract content from HTML tags."""
        results = []

        if attr and attr_val:
            # Match tags with specific attribute
            pattern = rf'<{tag}[^>]*{attr}=["\']?{attr_val}["\']?[^>]*>([^<]*)</{tag}>'
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            results.extend(matches)

            # Also check for self-closing or content attribute
            pattern = rf'<{tag}[^>]*{attr}=["\']?{attr_val}["\']?[^>]*content=["\']([^"\']+)["\']'
            matches = re.findall(pattern, html, re.IGNORECASE)
            results.extend(matches)
        else:
            # Match all tags of this type
            pattern = rf'<{tag}[^>]*>([^<]*)</{tag}>'
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            results.extend(matches)

        return [self.clean_text(r) for r in results if self.clean_text(r)]

    def extract_meta_tags(self, html: str) -> ExtractedMeta:
        """Extract all meta information from HTML."""
        meta = ExtractedMeta()

        # Title
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if title_match:
            meta.title = self.clean_text(title_match.group(1))

        # Meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if desc_match:
            meta.description = self.clean_text(desc_match.group(1))

        # OG tags
        og_patterns = {
            'og_title': r'property=["\']og:title["\'][^>]*content=["\']([^"\']+)["\']',
            'og_description': r'property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']',
            'og_image': r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            'og_type': r'property=["\']og:type["\'][^>]*content=["\']([^"\']+)["\']',
        }

        for attr, pattern in og_patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                setattr(meta, attr, self.clean_text(match.group(1)))

        # Twitter cards
        tw_patterns = {
            'twitter_title': r'name=["\']twitter:title["\'][^>]*content=["\']([^"\']+)["\']',
            'twitter_description': r'name=["\']twitter:description["\'][^>]*content=["\']([^"\']+)["\']',
        }

        for attr, pattern in tw_patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                setattr(meta, attr, self.clean_text(match.group(1)))

        # Canonical URL
        canonical_match = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if canonical_match:
            meta.canonical = canonical_match.group(1)

        # Language
        lang_match = re.search(r'<html[^>]*lang=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if lang_match:
            meta.lang = lang_match.group(1)

        # Keywords meta tag
        keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if keywords_match:
            meta.keywords = [k.strip() for k in keywords_match.group(1).split(',')]

        return meta

    def extract_json_ld(self, html: str) -> list[dict]:
        """Extract JSON-LD structured data."""
        results = []

        # Find all script tags with type application/ld+json
        pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>([^<]+)</script>'
        matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match)
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
            except json.JSONDecodeError:
                continue

        return results

    def extract_headings(self, html: str) -> tuple[list[str], list[str], list[str]]:
        """Extract H1, H2, H3 headings."""
        h1 = self.extract_tag_content(html, 'h1')
        h2 = self.extract_tag_content(html, 'h2')
        h3 = self.extract_tag_content(html, 'h3')
        return h1, h2, h3

    def extract_bullet_points(self, html: str) -> list[str]:
        """Extract bullet points from lists."""
        bullets = []

        # Extract li content
        li_pattern = r'<li[^>]*>([^<]+(?:<[^>]+>[^<]+)*)</li>'
        matches = re.findall(li_pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            # Remove nested tags
            clean = re.sub(r'<[^>]+>', ' ', match)
            clean = self.clean_text(clean)
            if clean and len(clean) > 10:
                bullets.append(clean)

        return bullets

    def extract_pricing(self, html: str) -> list[PricingTier]:
        """Extract pricing tiers from HTML."""
        tiers = []

        # Look for common pricing patterns
        # Price pattern: $X, $X/mo, $X/month, $X per month
        price_pattern = r'\$[\d,]+(?:\.\d{2})?(?:\s*[/per]+\s*(?:mo(?:nth)?|year|yr|user|seat))?'

        # Find pricing sections
        pricing_section = re.search(
            r'(?:pricing|plans|subscription)[^<]*</h[123]>(.{500,5000}?)(?:<footer|</main|</section)',
            html, re.IGNORECASE | re.DOTALL
        )

        if pricing_section:
            section = pricing_section.group(1)

            # Find tier names (usually in h3/h4 or strong/bold)
            tier_names = re.findall(r'<(?:h[34]|strong|b)[^>]*>([^<]+)</(?:h[34]|strong|b)>', section, re.IGNORECASE)
            prices = re.findall(price_pattern, section, re.IGNORECASE)

            # Match names with prices
            for i, name in enumerate(tier_names[:len(prices)]):
                clean_name = self.clean_text(name)
                if clean_name and not any(x in clean_name.lower() for x in ['feature', 'include', 'benefit']):
                    tiers.append(PricingTier(
                        tier=clean_name,
                        price=prices[i] if i < len(prices) else "Contact",
                    ))

        return tiers

    def extract_features(self, html: str) -> list[str]:
        """Extract feature mentions from HTML."""
        features = []

        # Look for feature sections
        feature_patterns = [
            r'(?:features?|capabilities)[^<]*</h[123]>(.{200,3000}?)(?:<h[123]|</section|</div>)',
            r'<(?:ul|ol)[^>]*class=["\'][^"\']*feature[^"\']*["\'][^>]*>(.+?)</(?:ul|ol)>',
        ]

        for pattern in feature_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Extract bullet points
                bullets = re.findall(r'<li[^>]*>([^<]+)', match, re.IGNORECASE)
                for bullet in bullets:
                    clean = self.clean_text(bullet)
                    if clean and len(clean) > 5 and len(clean) < 200:
                        features.append(clean)

        # Also check h2/h3 headings for feature names
        h2, h3 = self.extract_headings(html)[1:]
        for heading in h2 + h3:
            if any(word in heading.lower() for word in ['automat', 'integrat', 'analytic', 'report', 'dashboard', 'api', 'sync', 'export', 'import', 'collaborate']):
                features.append(heading)

        return list(set(features))[:50]  # Dedupe and limit

    def extract_forms(self, html: str) -> list[dict]:
        """Extract form information."""
        forms = []

        form_pattern = r'<form([^>]*)>(.*?)</form>'
        matches = re.findall(form_pattern, html, re.IGNORECASE | re.DOTALL)

        for attrs, content in matches:
            form_info = {"type": "unknown", "fields": []}

            # Determine form type
            if re.search(r'sign\s*up|register|create\s*account', content, re.IGNORECASE):
                form_info["type"] = "signup"
            elif re.search(r'login|sign\s*in', content, re.IGNORECASE):
                form_info["type"] = "login"
            elif re.search(r'contact|message|inquiry', content, re.IGNORECASE):
                form_info["type"] = "contact"
            elif re.search(r'subscribe|newsletter|email', content, re.IGNORECASE):
                form_info["type"] = "newsletter"
            elif re.search(r'demo|schedule|book', content, re.IGNORECASE):
                form_info["type"] = "demo"

            # Extract input fields
            inputs = re.findall(r'<input[^>]*(?:name|type|placeholder)=["\']([^"\']+)["\']', content, re.IGNORECASE)
            form_info["fields"] = inputs[:10]

            forms.append(form_info)

        return forms

    def extract_ctas(self, html: str) -> list[str]:
        """Extract call-to-action text."""
        ctas = []

        # Look for buttons and links with CTA text
        button_pattern = r'<(?:button|a)[^>]*>([^<]+)</(?:button|a)>'
        matches = re.findall(button_pattern, html, re.IGNORECASE)

        for match in matches:
            clean = self.clean_text(match).lower()
            for pattern in self.CTA_PATTERNS:
                if re.search(pattern, clean, re.IGNORECASE):
                    ctas.append(self.clean_text(match))
                    break

        return list(set(ctas))

    def extract_techstack(self, html: str) -> list[str]:
        """Detect technology stack from HTML/JS signatures."""
        detected = []

        for tech, patterns in self.TECH_SIGNATURES.items():
            for pattern in patterns:
                if re.search(pattern, html, re.IGNORECASE):
                    detected.append(tech)
                    break

        return detected

    def extract_integrations(self, html: str) -> list[str]:
        """Extract mentioned integrations."""
        integrations = []

        # Common integration names to look for
        common_integrations = [
            'Slack', 'Salesforce', 'HubSpot', 'Zapier', 'Google', 'Microsoft',
            'GitHub', 'GitLab', 'Jira', 'Asana', 'Trello', 'Notion',
            'Stripe', 'PayPal', 'QuickBooks', 'Xero', 'Mailchimp', 'SendGrid',
            'Twilio', 'AWS', 'Azure', 'Dropbox', 'Box', 'Zoom', 'Teams',
        ]

        # Check for mentions
        for integration in common_integrations:
            if re.search(rf'\b{integration}\b', html, re.IGNORECASE):
                integrations.append(integration)

        # Also look for integration sections
        for pattern in self.INTEGRATION_PATTERNS:
            matches = re.findall(pattern, html)
            integrations.extend(matches)

        return list(set(integrations))

    def extract(self, html: str, url: str) -> ExtractedContent:
        """
        Extract all structured content from HTML.

        Args:
            html: Raw HTML content
            url: Source URL

        Returns:
            ExtractedContent with all extracted data
        """
        content = ExtractedContent(url=url)

        # Extract meta
        content.meta = self.extract_meta_tags(html)

        # Extract headings
        content.h1, content.h2, content.h3 = self.extract_headings(html)

        # Extract bullet points
        content.bullet_points = self.extract_bullet_points(html)

        # Extract JSON-LD
        content.json_ld = self.extract_json_ld(html)

        # Extract pricing
        content.pricing_tiers = self.extract_pricing(html)

        # Extract features
        content.features = self.extract_features(html)

        # Extract forms
        content.forms = self.extract_forms(html)

        # Extract CTAs
        content.ctas = self.extract_ctas(html)

        # Extract techstack
        content.techstack_hints = self.extract_techstack(html)

        # Extract integrations
        content.integrations = self.extract_integrations(html)

        return content

    def merge_extractions(self, extractions: list[ExtractedContent]) -> ExtractedContent:
        """Merge multiple page extractions into one."""
        if not extractions:
            return ExtractedContent(url="")

        merged = ExtractedContent(url=extractions[0].url)
        merged.meta = extractions[0].meta  # Use first page's meta

        for ext in extractions:
            merged.h1.extend(ext.h1)
            merged.h2.extend(ext.h2)
            merged.h3.extend(ext.h3)
            merged.bullet_points.extend(ext.bullet_points)
            merged.json_ld.extend(ext.json_ld)
            merged.pricing_tiers.extend(ext.pricing_tiers)
            merged.features.extend(ext.features)
            merged.forms.extend(ext.forms)
            merged.ctas.extend(ext.ctas)
            merged.techstack_hints.extend(ext.techstack_hints)
            merged.integrations.extend(ext.integrations)

        # Deduplicate
        merged.h1 = list(set(merged.h1))
        merged.h2 = list(set(merged.h2))
        merged.h3 = list(set(merged.h3))
        merged.bullet_points = list(set(merged.bullet_points))
        merged.features = list(set(merged.features))
        merged.ctas = list(set(merged.ctas))
        merged.techstack_hints = list(set(merged.techstack_hints))
        merged.integrations = list(set(merged.integrations))

        return merged
