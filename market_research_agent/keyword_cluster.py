"""
Keyword Clustering - Groups related keywords into clusters.

Uses:
- String similarity
- Common word matching
- Semantic grouping (model families, tool types, etc.)

Helps identify themes and reduce noise from similar keywords.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from difflib import SequenceMatcher
from collections import defaultdict


@dataclass
class KeywordCluster:
    """A cluster of related keywords."""
    name: str  # Cluster name/theme
    keywords: list[str] = field(default_factory=list)
    representative: str = ""  # Best representative keyword
    total_score: float = 0.0
    avg_score: float = 0.0
    category: str = ""  # model, tool, technique, effect
    sources: list[str] = field(default_factory=list)


class KeywordClusterer:
    """
    Clusters related keywords together.

    Usage:
        clusterer = KeywordClusterer()
        clusters = clusterer.cluster(keywords)
    """

    # Known keyword families for semantic grouping
    KEYWORD_FAMILIES = {
        "flux": ["flux ai", "flux dev", "flux schnell", "flux pro", "flux kontext", "flux 1.1"],
        "kling": ["kling ai", "kling 1.5", "kling 1.6", "kling 2.0", "kling 2.1", "kling 2.5", "kling o1"],
        "wan": ["wan ai", "wan 2.2", "wan 2.5"],
        "stable_diffusion": ["stable diffusion", "sdxl", "sd 1.5", "sd 2.1", "sd3", "sd xl"],
        "qwen": ["qwen image", "qwen edit", "qwen 2512", "qwen lightning"],
        "comfyui": ["comfyui", "comfy ui", "comfyui manager", "comfyui workflow"],
        "lora": ["lora", "lora training", "lora fine-tuning", "distilled lora"],
        "controlnet": ["controlnet", "control net", "controlnet image"],
        "upscaler": ["upscaler", "upscaling", "image upscaler", "video upscaler", "ai upscaler"],
        "background": ["background remover", "background removal", "remove background", "add background"],
        "z_image": ["z-image", "z image", "z-image turbo", "zimage"],
        "ltx": ["ltx", "ltx-2", "ltx2", "ltxv2", "ltx video"],
        "rife": ["rife", "rife vfi", "rife 49", "frame interpolation"],
        "face": ["faceswap", "face swap", "reactor", "face detection"],
    }

    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold

    def normalize(self, text: str) -> str:
        """Normalize text for comparison."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(self, a: str, b: str) -> float:
        """Calculate similarity between two strings."""
        a_norm = self.normalize(a)
        b_norm = self.normalize(b)

        if a_norm == b_norm:
            return 1.0

        # Check word overlap
        words_a = set(a_norm.split())
        words_b = set(b_norm.split())
        if words_a and words_b:
            overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
            if overlap > 0.5:
                return 0.7 + (overlap * 0.3)

        # Sequence matching
        return SequenceMatcher(None, a_norm, b_norm).ratio()

    def find_family(self, keyword: str) -> Optional[str]:
        """Find which keyword family a keyword belongs to."""
        keyword_norm = self.normalize(keyword)

        for family_name, family_keywords in self.KEYWORD_FAMILIES.items():
            for fk in family_keywords:
                if self.normalize(fk) in keyword_norm or keyword_norm in self.normalize(fk):
                    return family_name
                if self.calculate_similarity(keyword_norm, self.normalize(fk)) > 0.8:
                    return family_name

        return None

    def cluster(
        self,
        keywords: list[dict],
        min_cluster_size: int = 2
    ) -> list[KeywordCluster]:
        """
        Cluster keywords by similarity and family.

        Args:
            keywords: List of dicts with 'keyword', 'score', 'source' keys
            min_cluster_size: Minimum keywords to form a cluster

        Returns:
            List of KeywordCluster objects
        """
        # First, group by known families
        family_groups = defaultdict(list)
        unassigned = []

        for kw_data in keywords:
            keyword = kw_data.get("keyword", "")
            family = self.find_family(keyword)

            if family:
                family_groups[family].append(kw_data)
            else:
                unassigned.append(kw_data)

        clusters = []

        # Create clusters from families
        for family_name, items in family_groups.items():
            if len(items) >= min_cluster_size:
                cluster = KeywordCluster(
                    name=family_name.replace("_", " ").title(),
                    keywords=[i["keyword"] for i in items],
                    representative=items[0]["keyword"],  # Highest scored
                    total_score=sum(i.get("score", 0) for i in items),
                    avg_score=sum(i.get("score", 0) for i in items) / len(items),
                    sources=list(set(i.get("source", "") for i in items)),
                )
                clusters.append(cluster)
            else:
                unassigned.extend(items)

        # Cluster remaining by similarity
        similarity_clusters = self._cluster_by_similarity(unassigned, min_cluster_size)
        clusters.extend(similarity_clusters)

        # Sort by total score
        clusters.sort(key=lambda c: c.total_score, reverse=True)

        return clusters

    def _cluster_by_similarity(
        self,
        keywords: list[dict],
        min_cluster_size: int
    ) -> list[KeywordCluster]:
        """Cluster unassigned keywords by string similarity."""
        if not keywords:
            return []

        clusters = []
        used = set()

        for i, kw_data in enumerate(keywords):
            if i in used:
                continue

            keyword = kw_data.get("keyword", "")
            cluster_items = [kw_data]
            used.add(i)

            # Find similar keywords
            for j, other_data in enumerate(keywords):
                if j in used:
                    continue

                other = other_data.get("keyword", "")
                similarity = self.calculate_similarity(keyword, other)

                if similarity >= self.similarity_threshold:
                    cluster_items.append(other_data)
                    used.add(j)

            if len(cluster_items) >= min_cluster_size:
                # Create cluster name from common words
                all_words = []
                for item in cluster_items:
                    all_words.extend(self.normalize(item["keyword"]).split())

                word_counts = defaultdict(int)
                for word in all_words:
                    if len(word) > 2:
                        word_counts[word] += 1

                common_word = max(word_counts, key=word_counts.get) if word_counts else keyword[:20]

                cluster = KeywordCluster(
                    name=common_word.title(),
                    keywords=[i["keyword"] for i in cluster_items],
                    representative=cluster_items[0]["keyword"],
                    total_score=sum(i.get("score", 0) for i in cluster_items),
                    avg_score=sum(i.get("score", 0) for i in cluster_items) / len(cluster_items),
                    sources=list(set(i.get("source", "") for i in cluster_items)),
                )
                clusters.append(cluster)

        return clusters

    def format_clusters(self, clusters: list[KeywordCluster]) -> str:
        """Format clusters as readable text."""
        lines = []

        lines.append("=" * 50)
        lines.append("KEYWORD CLUSTERS")
        lines.append("=" * 50)
        lines.append(f"Total clusters: {len(clusters)}")
        lines.append(f"Total keywords: {sum(len(c.keywords) for c in clusters)}")
        lines.append("")

        for i, cluster in enumerate(clusters[:15], 1):
            lines.append(f"{i}. {cluster.name} ({len(cluster.keywords)} keywords)")
            lines.append(f"   Representative: {cluster.representative}")
            lines.append(f"   Avg Score: {cluster.avg_score:.1f}")
            lines.append(f"   Keywords: {', '.join(cluster.keywords[:5])}")
            if len(cluster.keywords) > 5:
                lines.append(f"             +{len(cluster.keywords) - 5} more")
            lines.append("")

        return "\n".join(lines)


def cluster_keywords(keywords: list[str], scores: Optional[dict] = None) -> list[KeywordCluster]:
    """
    Quick function to cluster a list of keywords.

    Args:
        keywords: List of keyword strings
        scores: Optional dict mapping keyword -> score

    Returns:
        List of KeywordCluster
    """
    clusterer = KeywordClusterer()
    keyword_data = [
        {"keyword": kw, "score": scores.get(kw, 50) if scores else 50}
        for kw in keywords
    ]
    return clusterer.cluster(keyword_data)
