import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api import PolymarketClient, KalshiClient
from src.utils import config, logger
import json

def test_polymarket():
    logger.info("Testing Polymarket API client...")

    base_url = config.get("apis", "polymarket", "base_url")
    client = PolymarketClient(base_url)

    markets = client.get_markets(limit=10)

    logger.info(f"Retrieved {len(markets)} markets from Polymarket")

    if markets:
        logger.info("\nSample Polymarket markets:")
        for i, market in enumerate(markets[:3], 1):
            logger.info(f"\n{i}. {market.question}")
            logger.info(f"   Yes: {market.yes_price:.3f} | No: {market.no_price:.3f}")
            logger.info(f"   Liquidity: ${market.liquidity:,.0f}")
            logger.info(f"   Market ID: {market.market_id}")

    return markets

def test_kalshi():
    logger.info("\nTesting Kalshi API client...")

    base_url = config.get("apis", "kalshi", "base_url")
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")

    client = KalshiClient(base_url, email=email, password=password)

    markets = client.get_markets(limit=10)

    logger.info(f"Retrieved {len(markets)} markets from Kalshi")

    if markets:
        logger.info("\nSample Kalshi markets:")
        for i, market in enumerate(markets[:3], 1):
            logger.info(f"\n{i}. {market.question}")
            logger.info(f"   Yes: {market.yes_price:.3f} | No: {market.no_price:.3f}")
            logger.info(f"   Liquidity: ${market.liquidity:,.0f}")
            logger.info(f"   Market ID: {market.market_id}")

    return markets

def save_sample_data(polymarket_markets, kalshi_markets):
    sample_data = {
        "polymarket": [m.raw_data for m in polymarket_markets[:5]],
        "kalshi": [m.raw_data for m in kalshi_markets[:5]]
    }

    with open("tests/sample_markets.json", "w") as f:
        json.dump(sample_data, f, indent=2, default=str)

    logger.info("\nSaved sample market data to tests/sample_markets.json")

if __name__ == "__main__":
    try:
        polymarket_markets = test_polymarket()
        kalshi_markets = test_kalshi()

        if polymarket_markets and kalshi_markets:
            save_sample_data(polymarket_markets, kalshi_markets)
            logger.info("\nAPI client tests completed successfully")
        else:
            logger.warning("\nSome API clients failed to retrieve data")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
