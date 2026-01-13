"""
AI Model/Tool Detector - Detects specific AI models, tools, and techniques.

Comprehensive detection of:
- Image generation models (Flux, SDXL, Midjourney, Kling, etc.)
- Video models (Sora, Veo, Wan, LTX, etc.)
- Tools (ComfyUI, LoRA, ControlNet, etc.)
- Techniques (frame interpolation, quantization, etc.)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DetectedItem:
    """A detected AI model/tool/technique."""
    name: str
    category: str  # model, tool, technique, effect, platform
    subcategory: str = ""  # image, video, audio, workflow
    version: str = ""
    confidence: float = 1.0
    source_text: str = ""


class AIDetector:
    """
    Detects AI models, tools, and techniques in text.

    Usage:
        detector = AIDetector()
        items = detector.detect("I'm using ComfyUI with Flux dev and LoRA")
    """

    # Comprehensive AI detection patterns
    PATTERNS = {
        # === IMAGE GENERATION MODELS ===
        "image_models": {
            "Flux AI": r"\bflux\s*(?:ai)?\b(?!\s*(?:dev|schnell|pro|kontext|1\.1))",
            "Flux Dev": r"\bflux\s*dev\b",
            "Flux Schnell": r"\bflux\s*schnell\b",
            "Flux 1.1 Pro": r"\bflux\s*1\.1\s*pro\b",
            "Flux Kontext": r"\bflux\s*kontext\b",
            "Stable Diffusion": r"\bstable\s*diffusion\b(?!\s*(?:xl|3|2|1))",
            "SDXL": r"\bsdxl\b",
            "Stable Diffusion XL": r"\bstable\s*diffusion\s*xl\b",
            "Stable Diffusion 3": r"\bstable\s*diffusion\s*3\b",
            "Midjourney": r"\bmidjourney\b",
            "Midjourney V6": r"\bmidjourney\s*v6\b",
            "DALL-E 3": r"\bdall-?e\s*3\b",
            "DALL-E 2": r"\bdall-?e\s*2\b",
            "Qwen Image": r"\bqwen\s*image\b(?!\s*\d)",
            "Qwen Image 2512": r"\bqwen[- ]?image[- ]?2512\b",
            "Qwen Image Lightning": r"\bqwen[- ]?image[- ]?lightning\b",
            "Qwen Edit": r"\bqwen\s*edit\b",
            "GPT Image 1": r"\bgpt\s*image\s*1\b",
            "Nano Banana AI": r"\bnano\s*banana\s*(?:ai)?\b",
            "Nano Banana Pro": r"\bnano\s*banana\s*pro\b",
            "Z-Image": r"\bz[- ]?image\b(?!\s*turbo)",
            "Z-Image Turbo": r"\bz[- ]?image\s*turbo\b",
            "Fooocus": r"\bfooocus\b",
            "Seedream": r"\bseedream\b",
            "Reve AI": r"\breve\s*ai\b",
            "Ideogram": r"\bideogram\b",
            "Leonardo AI": r"\bleonardo\s*ai\b",
            "Firefly": r"\bfirefly\b",
            "Adobe Firefly": r"\badobe\s*firefly\b",
        },

        # === VIDEO GENERATION MODELS ===
        "video_models": {
            "Sora": r"\bsora\b(?!\s*ai)",
            "Sora AI": r"\bsora\s*ai\b",
            "Veo": r"\bveo\b(?!\s*\d)",
            "Veo 3.1": r"\bveo\s*3\.1\b",
            "Kling AI": r"\bkling\s*(?:ai)?\b(?!\s*(?:1|2|o1))",
            "Kling 1.5": r"\bkling\s*1\.5\b",
            "Kling 1.6": r"\bkling\s*1\.6\b",
            "Kling 2.0": r"\bkling\s*2\.0\b",
            "Kling 2.1": r"\bkling\s*2\.1\b",
            "Kling 2.5 Turbo": r"\bkling\s*2\.5\s*turbo\b",
            "Kling 2.6": r"\bkling\s*2\.6\b",
            "Kling O1": r"\bkling\s*o1\b",
            "Wan AI": r"\bwan\s*(?:ai)?\b(?!\s*\d)",
            "Wan 2.2": r"\bwan\s*2\.2\b",
            "Wan 2.5": r"\bwan\s*2\.5\b",
            "LTX-2": r"\bltx[- ]?2\b",
            "LTX Video": r"\bltx\s*video\b",
            "LTXV2": r"\bltxv2\b",
            "Runway Gen-3": r"\brunway\s*gen[- ]?3\b",
            "Runway": r"\brunway\b",
            "Pika Labs": r"\bpika\s*labs\b",
            "Pika": r"\bpika\b",
            "HeyGen": r"\bheygen\b",
            "Synthesia": r"\bsynthesia\b",
            "D-ID": r"\bd-?id\b",
            "Dream Machine": r"\bdream\s*machine\b",
            "Luma Dream Machine": r"\bluma\s*dream\s*machine\b",
            "HY-Motion": r"\bhy[- ]?motion\b",
            "Stable Video": r"\bstable\s*video\b",
        },

        # === TOOLS & WORKFLOWS ===
        "tools": {
            "ComfyUI": r"\bcomfyui\b(?!\s*\d)",
            "ComfyUI Manager": r"\bcomfyui\s*manager\b",
            "Automatic1111": r"\b(?:automatic1111|a1111)\b",
            "Forge WebUI": r"\bforge\s*(?:webui)?\b",
            "InvokeAI": r"\binvokeai\b",
            "Fooocus UI": r"\bfooocus\s*ui\b",
            "Ollama": r"\bollama\b",
            "LM Studio": r"\blm\s*studio\b",
            "ControlNet": r"\bcontrolnet\b",
            "IPAdapter": r"\bipadapter[s]?\b",
            "Reactor": r"\breactor\b",
            "FaceSwap": r"\bfaceswap\b",
            "RIFE VFI": r"\brife\s*(?:vfi)?\b",
            "GIMM VFI": r"\bgimm\s*vfi\b",
            "VideoHelperSuite": r"\bvideo\s*helper\s*suite\b",
            "TTP Toolset": r"\bttp\s*toolset\b",
            "SageAttention": r"\bsage\s*attention\b",
            "Magnific": r"\bmagnific\b",
            "Topaz": r"\btopaz\b",
            "Stable Horde": r"\bstable\s*horde\b",
            "Civitai": r"\bcivitai\b",
            "Hugging Face": r"\bhugging\s*face\b",
            "Replicate": r"\breplicate\b",
        },

        # === TECHNIQUES & METHODS ===
        "techniques": {
            "LoRA": r"\blora\b(?!\s*training)",
            "LoRA Training": r"\blora\s*training\b",
            "Fine-tuning": r"\bfine[- ]?tuning\b",
            "Quantization": r"\bquantization\b",
            "FP4": r"\bfp4\b",
            "FP8": r"\bfp8\b",
            "NVFP4": r"\bnvfp4\b",
            "Distillation": r"\bdistill(?:ed|ation)?\b",
            "Frame Interpolation": r"\bframe\s*interpolation\b",
            "Multi-frame Injection": r"\bmulti[- ]?frame\s*injection\b",
            "Inpainting": r"\binpainting\b",
            "Outpainting": r"\boutpainting\b",
            "Img2Img": r"\bimg2img\b",
            "Txt2Img": r"\btxt2img\b",
            "Character Consistency": r"\bcharacter\s*consistency\b",
            "Reference Images": r"\breference\s*images\b",
            "Upscaling": r"\bupscaling\b",
            "Super Resolution": r"\bsuper\s*resolution\b",
        },

        # === EFFECTS & FILTERS ===
        "effects": {
            "Ghibli Filter": r"\bghibli\s*(?:filter|style|effect)?\b",
            "Anime Style": r"\banime\s*(?:filter|style|effect)\b",
            "Cartoon Style": r"\bcartoon\s*(?:filter|style|effect)\b",
            "Pixel Art": r"\bpixel\s*art\b",
            "Wimmelbilder": r"\bwimmelbilder?\b",
            "Psychedelic": r"\bpsychedelic\b",
            "Beauty Filter": r"\bbeauty\s*filter\b",
            "Skin Smoothing": r"\bskin\s*smooth(?:ing)?\b",
            "Sepia": r"\bsepia\b",
            "Vintage": r"\bvintage\b",
            "Retro": r"\bretro\b",
            "Cyberpunk": r"\bcyberpunk\b",
            "Neon": r"\bneon\b",
            "Watercolor": r"\bwatercolor\b",
            "Oil Painting": r"\boil\s*painting\b",
            "Sketch": r"\bsketch\b",
            "Pop Art": r"\bpop\s*art\b",
        },

        # === PLATFORMS & SERVICES ===
        "platforms": {
            "ChatGPT": r"\bchatgpt\b",
            "Claude": r"\bclaude\b",
            "Grok": r"\bgrok\b",
            "Gemini": r"\bgemini\b",
            "Perplexity": r"\bperplexity\b",
            "Anthropic": r"\banthropic\b",
            "OpenAI": r"\bopenai\b",
            "Google AI": r"\bgoogle\s*ai\b",
            "Microsoft Copilot": r"\b(?:microsoft\s*)?copilot\b",
            "GitHub Copilot": r"\bgithub\s*copilot\b",
        },
    }

    def __init__(self):
        self.compiled_patterns = self._compile_patterns()

    def _compile_patterns(self) -> dict:
        """Compile all regex patterns."""
        compiled = {}
        for category, patterns in self.PATTERNS.items():
            compiled[category] = {}
            for name, pattern in patterns.items():
                compiled[category][name] = re.compile(pattern, re.IGNORECASE)
        return compiled

    def detect(self, text: str) -> list[DetectedItem]:
        """
        Detect AI models/tools/techniques in text.

        Args:
            text: Text to analyze

        Returns:
            List of DetectedItem objects
        """
        detected = []
        seen = set()

        for category, patterns in self.compiled_patterns.items():
            for name, pattern in patterns.items():
                if pattern.search(text):
                    # Avoid duplicates
                    key = name.lower()
                    if key not in seen:
                        seen.add(key)

                        # Determine subcategory
                        if "image" in category:
                            subcategory = "image"
                        elif "video" in category:
                            subcategory = "video"
                        elif "tool" in category:
                            subcategory = "workflow"
                        else:
                            subcategory = ""

                        detected.append(DetectedItem(
                            name=name,
                            category=category.replace("_models", "").replace("_", " "),
                            subcategory=subcategory,
                            source_text=text[:100],
                        ))

        return detected

    def detect_in_posts(self, posts: list[dict]) -> dict[str, list[str]]:
        """
        Detect AI items across multiple posts.

        Args:
            posts: List of dicts with 'title', 'body', 'url' keys

        Returns:
            Dict mapping post URL to list of detected item names
        """
        results = {}

        for post in posts:
            text = f"{post.get('title', '')} {post.get('body', '')}"
            detected = self.detect(text)
            url = post.get('url', 'unknown')
            results[url] = [d.name for d in detected]

        return results

    def get_all_known_items(self) -> list[str]:
        """Get list of all detectable item names."""
        items = []
        for category, patterns in self.PATTERNS.items():
            items.extend(patterns.keys())
        return items

    def categorize_items(self, items: list[str]) -> dict[str, list[str]]:
        """Categorize a list of items by type."""
        categorized = {
            "models": [],
            "tools": [],
            "techniques": [],
            "effects": [],
            "platforms": [],
            "unknown": [],
        }

        all_patterns = {}
        for category, patterns in self.PATTERNS.items():
            for name in patterns.keys():
                all_patterns[name.lower()] = category

        for item in items:
            item_lower = item.lower()
            found = False

            for name, category in all_patterns.items():
                if name in item_lower or item_lower in name:
                    cat_key = category.replace("_models", "").rstrip("s")
                    if cat_key + "s" in categorized:
                        categorized[cat_key + "s"].append(item)
                    else:
                        categorized["unknown"].append(item)
                    found = True
                    break

            if not found:
                categorized["unknown"].append(item)

        return categorized


def detect_ai_items(text: str) -> list[str]:
    """Quick function to detect AI items in text."""
    detector = AIDetector()
    detected = detector.detect(text)
    return [d.name for d in detected]


def get_ai_model_list() -> list[str]:
    """Get list of all known AI models."""
    detector = AIDetector()
    items = []
    for category in ["image_models", "video_models"]:
        items.extend(detector.PATTERNS.get(category, {}).keys())
    return items


def get_ai_tool_list() -> list[str]:
    """Get list of all known AI tools."""
    detector = AIDetector()
    return list(detector.PATTERNS.get("tools", {}).keys())
