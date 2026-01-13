"""
Feature Extractor - Automatically detect features from website content.

Analyzes:
- Homepage headlines and descriptions
- Features page content
- Pricing page tiers and features
- Navigation menus
- Product sections

Extracts product features, capabilities, and offerings.
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class ExtractedFeature:
    """A single extracted feature."""
    name: str
    category: str  # "core", "integration", "ai", "tool", etc.
    confidence: float  # 0.0 - 1.0
    source_page: str  # Where it was found
    context: str = ""  # Surrounding text


@dataclass
class FeatureExtractionResult:
    """Complete feature extraction result."""
    features: list[ExtractedFeature] = field(default_factory=list)
    feature_names: list[str] = field(default_factory=list)  # Simple list
    categories: dict[str, list[str]] = field(default_factory=dict)
    total_found: int = 0


class FeatureExtractor:
    """
    Extract features from website content.

    Looks for:
    - Feature lists (bullet points, cards)
    - Capability mentions
    - Product names
    - Integration mentions
    - AI/ML capabilities
    """

    # Feature indicators in text
    FEATURE_INDICATORS = [
        r"(?:we offer|features?|capabilities?|includes?|with|supports?)\s*:?\s*([^.]+)",
        r"(?:powered by|built with|using)\s+([^.]+)",
        r"(?:ai|ml|machine learning)\s+([^.]+)",
    ]

    # Common feature categories and their signals
    CATEGORY_PATTERNS = {
        "ai_models": {
            "patterns": [
                r"(?:flux|sdxl|stable diffusion|dall-?e|midjourney|imagen)",
                r"(?:gpt-?4|claude|llama|gemini|mistral)",
                r"(?:kling|sora|runway|pika|luma)",
                r"(?:whisper|eleven ?labs|voice ?ai)",
            ],
            "keywords": [
                "flux", "sdxl", "stable diffusion", "dall-e", "midjourney",
                "gpt", "claude", "llama", "gemini", "whisper", "kling", "sora",
                "runway", "pika", "luma", "imagen", "elevenlabs"
            ]
        },
        "ai_features": {
            "patterns": [
                r"(?:text[ -]to[ -](?:image|video|speech|audio))",
                r"(?:image[ -]to[ -](?:image|video|text))",
                r"(?:ai[ -](?:upscal|enhanc|generat|edit|remov))",
                r"(?:background[ -]remov|face[ -]swap|style[ -]transfer)",
                r"(?:inpaint|outpaint|img2img|controlnet)",
            ],
            "keywords": [
                "text-to-image", "text-to-video", "text-to-speech",
                "image-to-image", "ai upscaler", "ai enhancer",
                "background remover", "face swap", "style transfer",
                "inpainting", "outpainting", "img2img", "controlnet",
                "image generation", "video generation", "voice generation",
                "ai avatar", "ai headshot", "ai art"
            ]
        },
        "tools": {
            "patterns": [
                r"(?:edit(?:or|ing)?|crop|resize|compress|convert)",
                r"(?:batch|bulk|api|sdk|plugin)",
                r"(?:export|download|share|embed)",
            ],
            "keywords": [
                "editor", "cropper", "resizer", "compressor", "converter",
                "batch processing", "bulk", "api", "sdk", "plugin",
                "export", "download", "share", "embed", "watermark"
            ]
        },
        "integrations": {
            "patterns": [
                r"(?:integrat(?:es?|ion)|connect(?:s|ed)?|sync(?:s)?)\s+(?:with\s+)?(\w+)",
                r"(?:zapier|slack|discord|notion|figma|canva|photoshop)",
            ],
            "keywords": [
                "zapier", "slack", "discord", "notion", "figma", "canva",
                "photoshop", "google drive", "dropbox", "api", "webhook",
                "wordpress", "shopify", "wix"
            ]
        },
        "file_formats": {
            "patterns": [
                r"(?:png|jpg|jpeg|webp|gif|svg|pdf|mp4|mov|webm|mp3|wav)",
            ],
            "keywords": [
                "png", "jpg", "jpeg", "webp", "gif", "svg", "pdf",
                "mp4", "mov", "webm", "mp3", "wav", "heic", "raw"
            ]
        }
    }

    # HTML patterns for feature lists
    HTML_FEATURE_PATTERNS = [
        # Bullet lists
        r'<li[^>]*>([^<]{5,100})</li>',
        # Feature cards (common class names)
        r'<(?:div|article|section)[^>]*class="[^"]*(?:feature|card|benefit|capability)[^"]*"[^>]*>.*?<(?:h[2-4]|strong|b)[^>]*>([^<]+)',
        # Headlines followed by description
        r'<h[2-4][^>]*>([^<]{5,60})</h[2-4]>',
    ]

    def __init__(self):
        self.found_features: list[ExtractedFeature] = []

    def extract_from_text(self, text: str, source_page: str = "unknown") -> list[ExtractedFeature]:
        """Extract features from plain text."""
        features = []
        text_lower = text.lower()

        # Check each category
        for category, config in self.CATEGORY_PATTERNS.items():
            # Check keywords
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    # Find context around keyword
                    idx = text_lower.find(keyword.lower())
                    start = max(0, idx - 50)
                    end = min(len(text), idx + len(keyword) + 50)
                    context = text[start:end].strip()

                    feature = ExtractedFeature(
                        name=keyword,
                        category=category,
                        confidence=0.8,
                        source_page=source_page,
                        context=context
                    )
                    features.append(feature)

            # Check patterns
            for pattern in config["patterns"]:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    match = match.strip()
                    if len(match) > 2 and len(match) < 50:
                        feature = ExtractedFeature(
                            name=match,
                            category=category,
                            confidence=0.6,
                            source_page=source_page,
                        )
                        features.append(feature)

        self.found_features.extend(features)
        return features

    def extract_from_html(self, html: str, source_page: str = "unknown") -> list[ExtractedFeature]:
        """Extract features from HTML content."""
        features = []

        # First extract from plain text
        text = self._html_to_text(html)
        text_features = self.extract_from_text(text, source_page)
        features.extend(text_features)

        # Extract from HTML structure
        for pattern in self.HTML_FEATURE_PATTERNS:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                match = self._clean_text(match)

                # Skip if too short or too long
                if len(match) < 3 or len(match) > 100:
                    continue

                # Skip common non-feature items
                skip_words = ["home", "about", "contact", "login", "sign", "menu", "close", "cookie"]
                if any(w in match.lower() for w in skip_words):
                    continue

                # Categorize
                category = self._categorize_feature(match)

                feature = ExtractedFeature(
                    name=match,
                    category=category,
                    confidence=0.5,
                    source_page=source_page,
                )
                features.append(feature)

        return features

    def extract_from_features_page(self, html: str) -> list[ExtractedFeature]:
        """Extract from a dedicated features page (higher confidence)."""
        features = self.extract_from_html(html, source_page="features")

        # Boost confidence for features page
        for f in features:
            f.confidence = min(1.0, f.confidence + 0.2)

        return features

    def extract_from_pricing_page(self, html: str) -> list[ExtractedFeature]:
        """Extract features from pricing tiers."""
        features = []

        # Look for pricing tier features (checkmarks, included items)
        patterns = [
            r'<li[^>]*class="[^"]*(?:included|feature|check)[^"]*"[^>]*>([^<]+)',
            r'(?:✓|✔|☑|√)\s*([^<\n]{3,60})',
            r'<span[^>]*class="[^"]*(?:feature|benefit)[^"]*"[^>]*>([^<]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                match = self._clean_text(match)
                if len(match) > 2:
                    category = self._categorize_feature(match)
                    feature = ExtractedFeature(
                        name=match,
                        category=category,
                        confidence=0.75,
                        source_page="pricing"
                    )
                    features.append(feature)

        self.found_features.extend(features)
        return features

    def _categorize_feature(self, feature_name: str) -> str:
        """Determine category for a feature."""
        name_lower = feature_name.lower()

        for category, config in self.CATEGORY_PATTERNS.items():
            for keyword in config["keywords"]:
                if keyword.lower() in name_lower:
                    return category

        # Default category based on keywords
        if any(w in name_lower for w in ["ai", "ml", "generat", "model"]):
            return "ai_features"
        elif any(w in name_lower for w in ["integrat", "connect", "sync"]):
            return "integrations"
        elif any(w in name_lower for w in ["edit", "tool", "crop", "resize"]):
            return "tools"

        return "general"

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text."""
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_result(self) -> FeatureExtractionResult:
        """Get complete extraction result."""
        # Deduplicate by name
        seen = set()
        unique_features = []
        for f in self.found_features:
            key = f.name.lower()
            if key not in seen:
                seen.add(key)
                unique_features.append(f)

        # Sort by confidence
        unique_features.sort(key=lambda x: x.confidence, reverse=True)

        # Build categories
        categories: dict[str, list[str]] = {}
        for f in unique_features:
            if f.category not in categories:
                categories[f.category] = []
            if f.name not in categories[f.category]:
                categories[f.category].append(f.name)

        return FeatureExtractionResult(
            features=unique_features,
            feature_names=[f.name for f in unique_features],
            categories=categories,
            total_found=len(unique_features)
        )

    def get_feature_list(self) -> list[str]:
        """Get simple list of feature names."""
        return self.get_result().feature_names


def extract_features_from_html(html: str, page_type: str = "general") -> list[str]:
    """Quick function to extract features from HTML."""
    extractor = FeatureExtractor()

    if page_type == "features":
        extractor.extract_from_features_page(html)
    elif page_type == "pricing":
        extractor.extract_from_pricing_page(html)
    else:
        extractor.extract_from_html(html, page_type)

    return extractor.get_feature_list()
