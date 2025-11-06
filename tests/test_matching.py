import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api import PolymarketClient, KalshiClient
from src.matching import SemanticMatcher
from src.utils import config, logger

def test_matching():
    logger.info("Testing market matching with lower threshold...")

    poly_client = PolymarketClient(config.get("apis", "polymarket", "base_url"))
    kalshi_client = KalshiClient(config.get("apis", "kalshi", "base_url"))

    poly_markets = poly_client.get_markets(limit=50)
    kalshi_markets = kalshi_client.get_markets(limit=100)

    logger.info(f"\nPolymarket sample questions:")
    for m in poly_markets[:10]:
        logger.info(f"  - {m.question}")

    logger.info(f"\nKalshi sample questions:")
    for m in kalshi_markets[:10]:
        logger.info(f"  - {m.question}")

    matcher = SemanticMatcher(min_confidence=0.5, use_semantic=False)
    matches = matcher.match_markets(poly_markets, kalshi_markets)

    if matches:
        logger.info(f"\nFound {len(matches)} matches with confidence >= 0.5:")
        for match in matches[:10]:
            logger.info(f"\nMatch confidence: {match.confidence:.2f}")
            logger.info(f"  Polymarket: {match.market_a.question}")
            logger.info(f"  Kalshi: {match.market_b.question}")
            logger.info(f"  Fuzzy score: {match.fuzzy_score:.1f}")
    else:
        logger.info("\nNo matches found even with 0.5 threshold")

if __name__ == "__main__":
    test_matching()
