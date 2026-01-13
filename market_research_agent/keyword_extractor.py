"""
Keyword Extractor module - Extracts and scores keywords using TF-IDF.

Extracts seed keywords from:
- Page titles and headings
- Feature lists
- Meta descriptions
- Pricing tier names
- Integration names

Scores keywords using TF-IDF and filters by relevance.
"""

import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional
from .models import Keyword, Intent
from .extractor import ExtractedContent


# Common English stop words
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
    'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'or', 'that',
    'the', 'to', 'was', 'were', 'will', 'with', 'this', 'they', 'we',
    'you', 'your', 'our', 'their', 'what', 'which', 'who', 'when',
    'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'can', 'could', 'should', 'would', 'may', 'might', 'must',
    'shall', 'get', 'got', 'have', 'had', 'do', 'does', 'did',
    'about', 'after', 'before', 'into', 'through', 'during',
    'above', 'below', 'between', 'under', 'again', 'further',
    'then', 'once', 'here', 'there', 'any', 'also', 'even',
}

# Intent classification patterns
INTENT_PATTERNS = {
    Intent.TRANSACTIONAL: [
        r'\bbuy\b', r'\bpurchase\b', r'\border\b', r'\bsubscribe\b',
        r'\bsign\s*up\b', r'\bget\s+started\b', r'\bdownload\b',
        r'\bprice\b', r'\bpricing\b', r'\bcost\b', r'\bdiscount\b',
    ],
    Intent.COMMERCIAL: [
        r'\bbest\b', r'\btop\b', r'\breview\b', r'\bcompare\b',
        r'\bvs\b', r'\balternative\b', r'\bcomparison\b',
        r'\bcheap\b', r'\baffordable\b', r'\bpremium\b',
    ],
    Intent.INFORMATIONAL: [
        r'\bhow\s+to\b', r'\bwhat\s+is\b', r'\bguide\b', r'\btutorial\b',
        r'\blearn\b', r'\bexplain\b', r'\bdefinition\b', r'\bexample\b',
        r'\btips\b', r'\bsteps\b', r'\bbenefits\b',
    ],
    Intent.NAVIGATIONAL: [
        r'\blogin\b', r'\bsign\s*in\b', r'\bdashboard\b', r'\baccount\b',
        r'\bsupport\b', r'\bcontact\b', r'\bdocs\b', r'\bhelp\b',
    ],
}


@dataclass
class KeywordCandidate:
    """A keyword candidate before final scoring."""
    phrase: str
    source: str
    frequency: int = 1
    importance_weight: float = 1.0


class KeywordExtractor:
    """
    Extracts and scores keywords from website content.

    Usage:
        extractor = KeywordExtractor()
        keywords = extractor.extract(content)
    """

    # Source weights (higher = more important)
    SOURCE_WEIGHTS = {
        "title": 3.0,
        "h1": 2.5,
        "h2": 2.0,
        "h3": 1.5,
        "meta_description": 2.0,
        "feature": 2.5,
        "pricing": 1.5,
        "integration": 1.8,
        "cta": 1.5,
        "bullet": 1.0,
    }

    def __init__(
        self,
        min_word_length: int = 3,
        max_phrase_words: int = 4,
        min_frequency: int = 1,
    ):
        self.min_word_length = min_word_length
        self.max_phrase_words = max_phrase_words
        self.min_frequency = min_frequency
        self.document_frequencies: Counter = Counter()
        self.total_documents = 0

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        # Remove special characters, keep alphanumeric and spaces
        text = re.sub(r'[^\w\s-]', ' ', text.lower())
        # Split and filter
        words = text.split()
        return [w for w in words if len(w) >= self.min_word_length and w not in STOP_WORDS]

    def extract_ngrams(self, words: list[str], n: int) -> list[str]:
        """Extract n-grams from word list."""
        if len(words) < n:
            return []
        return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

    def extract_phrases(self, text: str) -> list[str]:
        """Extract meaningful phrases (1-4 grams) from text."""
        words = self.tokenize(text)
        phrases = []

        # Add unigrams, bigrams, trigrams, and 4-grams
        for n in range(1, min(self.max_phrase_words + 1, len(words) + 1)):
            ngrams = self.extract_ngrams(words, n)
            phrases.extend(ngrams)

        return phrases

    def classify_intent(self, phrase: str) -> Intent:
        """Classify search intent of a phrase."""
        phrase_lower = phrase.lower()

        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, phrase_lower):
                    return intent

        return Intent.INFORMATIONAL  # Default

    def calculate_tfidf(self, term_frequency: int, doc_frequency: int, total_docs: int) -> float:
        """Calculate TF-IDF score."""
        if doc_frequency == 0 or total_docs == 0:
            return 0.0

        tf = 1 + math.log(term_frequency) if term_frequency > 0 else 0
        idf = math.log(total_docs / doc_frequency)
        return tf * idf

    def extract_from_content(self, content: ExtractedContent) -> list[KeywordCandidate]:
        """Extract keyword candidates from all content sources."""
        candidates: list[KeywordCandidate] = []

        # Extract from title
        if content.meta.title:
            for phrase in self.extract_phrases(content.meta.title):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="title",
                    importance_weight=self.SOURCE_WEIGHTS["title"]
                ))

        # Extract from meta description
        if content.meta.description:
            for phrase in self.extract_phrases(content.meta.description):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="meta_description",
                    importance_weight=self.SOURCE_WEIGHTS["meta_description"]
                ))

        # Extract from H1 headings
        for h1 in content.h1:
            for phrase in self.extract_phrases(h1):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="h1",
                    importance_weight=self.SOURCE_WEIGHTS["h1"]
                ))

        # Extract from H2 headings
        for h2 in content.h2:
            for phrase in self.extract_phrases(h2):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="h2",
                    importance_weight=self.SOURCE_WEIGHTS["h2"]
                ))

        # Extract from H3 headings
        for h3 in content.h3:
            for phrase in self.extract_phrases(h3):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="h3",
                    importance_weight=self.SOURCE_WEIGHTS["h3"]
                ))

        # Extract from features (high value)
        for feature in content.features:
            for phrase in self.extract_phrases(feature):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="feature",
                    importance_weight=self.SOURCE_WEIGHTS["feature"]
                ))

        # Extract from pricing tiers
        for tier in content.pricing_tiers:
            for phrase in self.extract_phrases(tier.tier):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="pricing",
                    importance_weight=self.SOURCE_WEIGHTS["pricing"]
                ))

        # Extract from integrations
        for integration in content.integrations:
            candidates.append(KeywordCandidate(
                phrase=integration.lower(),
                source="integration",
                importance_weight=self.SOURCE_WEIGHTS["integration"]
            ))

        # Extract from CTAs
        for cta in content.ctas:
            for phrase in self.extract_phrases(cta):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="cta",
                    importance_weight=self.SOURCE_WEIGHTS["cta"]
                ))

        # Extract from bullet points
        for bullet in content.bullet_points:
            for phrase in self.extract_phrases(bullet):
                candidates.append(KeywordCandidate(
                    phrase=phrase,
                    source="bullet",
                    importance_weight=self.SOURCE_WEIGHTS["bullet"]
                ))

        return candidates

    def aggregate_candidates(self, candidates: list[KeywordCandidate]) -> dict[str, KeywordCandidate]:
        """Aggregate duplicate candidates, summing weights and frequencies."""
        aggregated: dict[str, KeywordCandidate] = {}

        for candidate in candidates:
            key = candidate.phrase
            if key in aggregated:
                aggregated[key].frequency += 1
                aggregated[key].importance_weight = max(
                    aggregated[key].importance_weight,
                    candidate.importance_weight
                )
            else:
                aggregated[key] = KeywordCandidate(
                    phrase=candidate.phrase,
                    source=candidate.source,
                    frequency=1,
                    importance_weight=candidate.importance_weight
                )

        return aggregated

    def score_candidates(self, aggregated: dict[str, KeywordCandidate]) -> list[Keyword]:
        """Score aggregated candidates and return Keywords."""
        keywords = []
        total_candidates = len(aggregated)

        # Calculate document frequencies (for TF-IDF approximation)
        phrase_counts = Counter(c.frequency for c in aggregated.values())

        for phrase, candidate in aggregated.items():
            # Skip very common phrases
            if candidate.frequency > total_candidates * 0.5:
                continue

            # Calculate TF-IDF score
            tfidf = self.calculate_tfidf(
                candidate.frequency,
                phrase_counts.get(candidate.frequency, 1),
                total_candidates
            )

            # Apply importance weight
            final_score = tfidf * candidate.importance_weight

            # Boost multi-word phrases (usually more specific)
            word_count = len(phrase.split())
            if word_count >= 2:
                final_score *= 1.2
            if word_count >= 3:
                final_score *= 1.1

            keyword = Keyword(
                keyword=phrase,
                source=candidate.source,
                intent=self.classify_intent(phrase),
                tfidf_score=final_score
            )
            keywords.append(keyword)

        # Sort by TF-IDF score
        keywords.sort(key=lambda k: k.tfidf_score, reverse=True)

        return keywords

    def extract(self, content: ExtractedContent, top_n: int = 200) -> list[Keyword]:
        """
        Extract and score keywords from content.

        Args:
            content: Extracted content from website
            top_n: Maximum number of keywords to return

        Returns:
            List of Keyword objects sorted by score
        """
        # Extract candidates
        candidates = self.extract_from_content(content)

        # Aggregate duplicates
        aggregated = self.aggregate_candidates(candidates)

        # Score and rank
        keywords = self.score_candidates(aggregated)

        return keywords[:top_n]


def expand_keywords(seed_keywords: list[Keyword], site_type: str) -> list[str]:
    """
    Generate expanded keyword variations for research.

    Args:
        seed_keywords: Base keywords extracted from site
        site_type: Type of site (SaaS, e-commerce, etc.)

    Returns:
        List of expanded search queries
    """
    expanded = []

    # Common modifiers by intent
    informational_modifiers = [
        "how to {}", "what is {}", "{} guide", "{} tutorial",
        "{} explained", "{} examples", "{} tips", "{} best practices",
    ]

    commercial_modifiers = [
        "best {}", "top {}", "{} review", "{} comparison",
        "{} vs", "{} alternative", "{} software", "{} tool",
    ]

    transactional_modifiers = [
        "{} pricing", "{} free trial", "buy {}",
        "{} discount", "{} coupon", "{} demo",
    ]

    for keyword in seed_keywords[:50]:  # Limit to top 50
        base = keyword.keyword

        # Add base keyword
        expanded.append(base)

        # Add modified versions based on intent
        if keyword.intent == Intent.INFORMATIONAL:
            for modifier in informational_modifiers[:3]:
                expanded.append(modifier.format(base))

        elif keyword.intent == Intent.COMMERCIAL:
            for modifier in commercial_modifiers[:3]:
                expanded.append(modifier.format(base))

        elif keyword.intent == Intent.TRANSACTIONAL:
            for modifier in transactional_modifiers[:3]:
                expanded.append(modifier.format(base))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in expanded:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique[:200]


def filter_brand_keywords(keywords: list[Keyword], brand_names: list[str]) -> list[Keyword]:
    """Filter out branded keywords unless explicitly wanted."""
    filtered = []
    brand_lower = [b.lower() for b in brand_names]

    for keyword in keywords:
        kw_lower = keyword.keyword.lower()
        is_branded = any(brand in kw_lower for brand in brand_lower)

        if not is_branded:
            filtered.append(keyword)

    return filtered
