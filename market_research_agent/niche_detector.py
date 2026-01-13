"""
Niche Detector - Automatically classify a website's industry and niche.

Analyzes site content to determine:
- Industry category (AI, SaaS, E-commerce, etc.)
- Specific niche within that industry
- Target audience
- Business model
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class NicheResult:
    """Detected niche information."""
    primary_niche: str  # Main niche description
    industry: str  # Broader industry category
    sub_niches: list[str] = field(default_factory=list)
    confidence: float = 0.0
    target_audience: str = ""
    business_model: str = ""  # "saas", "marketplace", "agency", etc.
    signals_found: list[str] = field(default_factory=list)


class NicheDetector:
    """
    Detect website niche based on content analysis.

    Uses signal matching to classify sites into industries and niches.
    """

    # Industry definitions with signals
    INDUSTRIES = {
        "ai_image_video": {
            "name": "AI Image/Video Generation",
            "signals": [
                "text-to-image", "text-to-video", "image generation",
                "video generation", "ai art", "stable diffusion", "flux",
                "midjourney", "dall-e", "sdxl", "comfyui", "img2img",
                "inpainting", "outpainting", "upscale", "enhance",
                "background remov", "face swap", "ai avatar", "ai headshot",
                "generative ai", "diffusion model", "kling", "sora", "runway"
            ],
            "niche_template": "AI {focus} platform",
            "focus_signals": {
                "image": ["image generation", "text-to-image", "img2img", "stable diffusion"],
                "video": ["video generation", "text-to-video", "kling", "sora", "runway"],
                "avatar": ["ai avatar", "ai headshot", "face swap", "talking head"],
                "art": ["ai art", "digital art", "artistic", "style transfer"],
                "editing": ["edit", "enhance", "upscale", "remove background"],
            }
        },
        "ai_audio_voice": {
            "name": "AI Audio/Voice",
            "signals": [
                "text-to-speech", "voice clone", "voice generation",
                "speech synthesis", "ai voice", "elevenlabs", "whisper",
                "transcription", "voice over", "audio generation",
                "music generation", "podcast", "audiobook"
            ],
            "niche_template": "AI {focus} platform",
            "focus_signals": {
                "voice": ["voice clone", "voice generation", "text-to-speech"],
                "music": ["music generation", "ai music", "audio generation"],
                "transcription": ["transcription", "speech-to-text", "whisper"],
            }
        },
        "ai_writing": {
            "name": "AI Writing/Content",
            "signals": [
                "ai writing", "content generation", "copywriting",
                "gpt", "claude", "chatbot", "ai assistant",
                "blog writing", "seo content", "ai writer",
                "text generation", "llm", "language model"
            ],
            "niche_template": "AI {focus} platform",
            "focus_signals": {
                "writing": ["ai writing", "content generation", "ai writer"],
                "chat": ["chatbot", "ai assistant", "conversational"],
                "seo": ["seo content", "blog writing", "marketing"],
            }
        },
        "ai_dev_tools": {
            "name": "AI Developer Tools",
            "signals": [
                "api", "sdk", "developer", "integration",
                "embedding", "fine-tune", "model training",
                "inference", "deployment", "ml ops", "ai infrastructure"
            ],
            "niche_template": "AI {focus} for developers",
            "focus_signals": {
                "api": ["api", "sdk", "integration"],
                "training": ["fine-tune", "model training", "ml ops"],
                "infrastructure": ["inference", "deployment", "ai infrastructure"],
            }
        },
        "saas_general": {
            "name": "SaaS",
            "signals": [
                "saas", "subscription", "monthly", "annual",
                "enterprise", "team", "collaboration", "workflow",
                "productivity", "project management", "crm"
            ],
            "niche_template": "{focus} SaaS platform",
            "focus_signals": {
                "productivity": ["productivity", "workflow", "automation"],
                "collaboration": ["team", "collaboration", "workspace"],
                "crm": ["crm", "sales", "customer"],
            }
        },
        "ecommerce": {
            "name": "E-commerce",
            "signals": [
                "shop", "store", "buy", "cart", "checkout",
                "product", "shipping", "order", "payment"
            ],
            "niche_template": "{focus} e-commerce platform",
            "focus_signals": {
                "marketplace": ["marketplace", "sellers", "vendors"],
                "digital": ["digital", "download", "license"],
                "physical": ["shipping", "inventory", "warehouse"],
            }
        },
        "design_creative": {
            "name": "Design & Creative Tools",
            "signals": [
                "design", "creative", "graphic", "canvas",
                "template", "logo", "brand", "visual",
                "figma", "canva", "photoshop", "illustrator"
            ],
            "niche_template": "{focus} design platform",
            "focus_signals": {
                "graphic": ["graphic design", "visual", "canvas"],
                "brand": ["brand", "logo", "identity"],
                "template": ["template", "preset", "mockup"],
            }
        },
        "marketing": {
            "name": "Marketing & Analytics",
            "signals": [
                "marketing", "analytics", "seo", "ads",
                "campaign", "conversion", "traffic", "growth",
                "social media", "email marketing", "automation"
            ],
            "niche_template": "{focus} marketing platform",
            "focus_signals": {
                "seo": ["seo", "search", "keywords"],
                "social": ["social media", "instagram", "tiktok"],
                "email": ["email marketing", "newsletter", "automation"],
            }
        }
    }

    # Business model signals
    BUSINESS_MODELS = {
        "saas": ["subscription", "monthly", "annual", "plan", "tier", "pro", "enterprise"],
        "marketplace": ["marketplace", "sellers", "vendors", "listing", "commission"],
        "freemium": ["free", "freemium", "free tier", "free plan", "credits"],
        "pay_per_use": ["pay per", "credit", "usage-based", "per image", "per video"],
        "agency": ["agency", "service", "custom", "bespoke", "consultation"],
        "api_platform": ["api", "developer", "sdk", "integration", "webhook"],
    }

    # Target audience signals
    AUDIENCES = {
        "developers": ["developer", "api", "sdk", "code", "engineer", "technical"],
        "designers": ["designer", "creative", "artist", "visual", "design"],
        "marketers": ["marketer", "marketing", "growth", "campaign", "ads"],
        "businesses": ["business", "enterprise", "team", "company", "organization"],
        "creators": ["creator", "influencer", "content", "youtube", "tiktok"],
        "consumers": ["personal", "individual", "hobby", "fun", "easy"],
    }

    def __init__(self):
        self.signals_found: list[str] = []
        self.industry_scores: dict[str, float] = {}

    def detect(
        self,
        homepage_text: str = "",
        features_text: str = "",
        pricing_text: str = "",
        about_text: str = "",
        site_title: str = "",
        site_description: str = ""
    ) -> NicheResult:
        """
        Detect niche from site content.

        Args:
            homepage_text: Plain text from homepage
            features_text: Plain text from features page
            pricing_text: Plain text from pricing page
            about_text: Plain text from about page
            site_title: Site title
            site_description: Meta description

        Returns:
            NicheResult with detected niche information
        """
        # Combine all text
        all_text = " ".join([
            site_title,
            site_description,
            homepage_text,
            features_text,
            pricing_text,
            about_text
        ]).lower()

        # Score each industry
        self.industry_scores = {}
        for industry_key, config in self.INDUSTRIES.items():
            score = 0
            signals = []
            for signal in config["signals"]:
                if signal.lower() in all_text:
                    score += 1
                    signals.append(signal)

            if score > 0:
                self.industry_scores[industry_key] = score
                self.signals_found.extend(signals)

        # Find best industry
        if not self.industry_scores:
            return NicheResult(
                primary_niche="Unknown",
                industry="Unknown",
                confidence=0.0
            )

        best_industry = max(self.industry_scores, key=self.industry_scores.get)
        best_score = self.industry_scores[best_industry]
        config = self.INDUSTRIES[best_industry]

        # Calculate confidence (normalize by number of signals)
        max_signals = len(config["signals"])
        confidence = min(1.0, best_score / (max_signals * 0.3))

        # Determine focus within industry
        focus = self._detect_focus(all_text, config.get("focus_signals", {}))

        # Build niche string
        if focus:
            primary_niche = config["niche_template"].format(focus=focus)
        else:
            primary_niche = config["name"]

        # Detect business model
        business_model = self._detect_business_model(all_text)

        # Detect target audience
        target_audience = self._detect_audience(all_text)

        # Find sub-niches (other industries with some signals)
        sub_niches = []
        for ind_key, score in sorted(self.industry_scores.items(), key=lambda x: x[1], reverse=True):
            if ind_key != best_industry and score > 1:
                sub_niches.append(self.INDUSTRIES[ind_key]["name"])

        return NicheResult(
            primary_niche=primary_niche,
            industry=config["name"],
            sub_niches=sub_niches[:3],
            confidence=confidence,
            target_audience=target_audience,
            business_model=business_model,
            signals_found=list(set(self.signals_found))
        )

    def _detect_focus(self, text: str, focus_signals: dict) -> str:
        """Detect specific focus within industry."""
        if not focus_signals:
            return ""

        focus_scores = {}
        for focus, signals in focus_signals.items():
            score = sum(1 for s in signals if s.lower() in text)
            if score > 0:
                focus_scores[focus] = score

        if focus_scores:
            best_focus = max(focus_scores, key=focus_scores.get)
            return best_focus.replace("_", " ").title()

        return ""

    def _detect_business_model(self, text: str) -> str:
        """Detect business model from content."""
        model_scores = {}
        for model, signals in self.BUSINESS_MODELS.items():
            score = sum(1 for s in signals if s.lower() in text)
            if score > 0:
                model_scores[model] = score

        if model_scores:
            return max(model_scores, key=model_scores.get)
        return "unknown"

    def _detect_audience(self, text: str) -> str:
        """Detect target audience from content."""
        audience_scores = {}
        for audience, signals in self.AUDIENCES.items():
            score = sum(1 for s in signals if s.lower() in text)
            if score > 0:
                audience_scores[audience] = score

        if audience_scores:
            top_audiences = sorted(audience_scores.items(), key=lambda x: x[1], reverse=True)[:2]
            return ", ".join(a[0] for a in top_audiences)
        return "general"

    def detect_from_features(self, features: list[str]) -> NicheResult:
        """Detect niche from extracted feature list."""
        feature_text = " ".join(features)
        return self.detect(features_text=feature_text)


def detect_niche(text: str) -> NicheResult:
    """Quick function to detect niche from text."""
    detector = NicheDetector()
    return detector.detect(homepage_text=text)


def detect_niche_from_features(features: list[str]) -> NicheResult:
    """Quick function to detect niche from feature list."""
    detector = NicheDetector()
    return detector.detect_from_features(features)
