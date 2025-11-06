from typing import List, Tuple, Optional
from rapidfuzz import fuzz
from ..api.base import Market
from .normalizer import normalizer
from ..utils.logger import logger

class MatchResult:
    def __init__(self, market_a: Market, market_b: Market, confidence: float,
                 fuzzy_score: float, semantic_score: float = 0.0):
        self.market_a = market_a
        self.market_b = market_b
        self.confidence = confidence
        self.fuzzy_score = fuzzy_score
        self.semantic_score = semantic_score

    def __repr__(self):
        return (f"MatchResult(confidence={self.confidence:.2f}, "
                f"fuzzy={self.fuzzy_score:.2f}, semantic={self.semantic_score:.2f})")

class SemanticMatcher:
    def __init__(self, min_confidence: float = 0.8, use_semantic: bool = True):
        self.min_confidence = min_confidence
        self.use_semantic = use_semantic
        self.embedder = None

        if use_semantic:
            try:
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded semantic embedding model")
            except Exception as e:
                logger.warning(f"Failed to load semantic model: {e}")
                self.use_semantic = False

    def match_markets(self, markets_a: List[Market], markets_b: List[Market]) -> List[MatchResult]:
        matches = []

        for market_a in markets_a:
            best_match = None
            best_confidence = 0

            for market_b in markets_b:
                result = self._calculate_match(market_a, market_b)

                if result and result.confidence > best_confidence:
                    best_confidence = result.confidence
                    best_match = result

            if best_match and best_match.confidence >= self.min_confidence:
                matches.append(best_match)

        logger.info(f"Found {len(matches)} market matches (min confidence: {self.min_confidence})")
        return matches

    def _calculate_match(self, market_a: Market, market_b: Market) -> Optional[MatchResult]:
        text_a = market_a.question
        text_b = market_b.question

        norm_a = normalizer.normalize(text_a)
        norm_b = normalizer.normalize(text_b)

        if norm_a == norm_b:
            return MatchResult(market_a, market_b, 1.0, 100.0)

        fuzzy_score = fuzz.token_sort_ratio(norm_a, norm_b)

        date_a = normalizer.extract_date_context(text_a)
        date_b = normalizer.extract_date_context(text_b)

        if date_a['has_date'] and date_b['has_date']:
            if date_a['years'] != date_b['years']:
                return None

        semantic_score = 0.0
        if self.use_semantic and self.embedder:
            try:
                embeddings = self.embedder.encode([norm_a, norm_b])
                from numpy import dot
                from numpy.linalg import norm
                semantic_score = dot(embeddings[0], embeddings[1]) / (norm(embeddings[0]) * norm(embeddings[1]))
                semantic_score = float(semantic_score) * 100
            except Exception as e:
                logger.warning(f"Semantic scoring failed: {e}")

        if self.use_semantic and semantic_score > 0:
            confidence = (fuzzy_score * 0.4 + semantic_score * 0.6) / 100
        else:
            confidence = fuzzy_score / 100

        return MatchResult(market_a, market_b, confidence, fuzzy_score, semantic_score)

matcher = SemanticMatcher()
