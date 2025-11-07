#!/usr/bin/env python3
"""
Manual test script for the arbitrage bot.

Usage:
    python test_bot.py              # Test with real APIs
    python test_bot.py --mock       # Test with mock data (guaranteed arbitrage opportunity)
"""

import sys
import argparse
from src.api import PolymarketClient, KalshiClient, Market
from src.matching.semantic_matcher import matcher
from src.arbitrage.calculator import ArbitrageCalculator
from src.utils.config import config
from src.utils.logger import logger

def create_mock_markets():
    """Create mock markets with a guaranteed arbitrage opportunity"""
    from datetime import datetime, timedelta

    # Mock Polymarket market: "Will Bitcoin hit $100k in 2024?"
    polymarket_markets = [
        Market(
            platform="polymarket",
            market_id="mock_poly_1",
            question="Will Bitcoin reach $100,000 by end of 2024?",
            yes_price=0.35,  # 35 cents to buy YES
            no_price=0.65,   # 65 cents to buy NO
            volume=50000,
            liquidity=10000,
            end_date=datetime(2024, 12, 31),
            raw_data={"mock": True}
        )
    ]

    # Mock Kalshi market: Same question but different prices (arbitrage opportunity!)
    kalshi_markets = [
        Market(
            platform="kalshi",
            market_id="mock_kalshi_1",
            question="Bitcoin reaches $100,000 by end of 2024?",
            yes_price=0.62,  # 62 cents to buy YES
            no_price=0.38,   # 38 cents to buy NO
            volume=25000,
            liquidity=5000,
            end_date=datetime(2024, 12, 31),
            raw_data={"mock": True}
        )
    ]

    # Arbitrage calculation:
    # Strategy 1: Buy YES on Polymarket (0.35) + Buy NO on Kalshi (0.38) = 0.73 cost
    #             Profit = 1.00 - 0.73 = 0.27 = 27% profit!

    # Strategy 2: Buy NO on Polymarket (0.65) + Buy YES on Kalshi (0.62) = 1.27 cost
    #             Profit = 1.00 - 1.27 = -0.27 = -27% loss (skip this)

    return polymarket_markets, kalshi_markets

def test_real_apis():
    """Test with real API data"""
    logger.info("=" * 60)
    logger.info("TESTING WITH REAL APIs")
    logger.info("=" * 60)

    # Create API clients
    polymarket_client = PolymarketClient(
        base_url=config.get("apis", "polymarket", "base_url"),
        timeout=config.get("apis", "polymarket", "timeout")
    )

    kalshi_api_key_id = config.get("apis", "kalshi", "api_key_id") or None
    kalshi_private_key = config.get("apis", "kalshi", "private_key") or None

    kalshi_client = KalshiClient(
        base_url=config.get("apis", "kalshi", "base_url"),
        timeout=config.get("apis", "kalshi", "timeout"),
        api_key_id=kalshi_api_key_id,
        private_key_str=kalshi_private_key
    )

    # Fetch real markets
    logger.info("Fetching Polymarket markets...")
    polymarket_markets = polymarket_client.get_markets()
    logger.info(f"✓ Got {len(polymarket_markets)} Polymarket markets")

    logger.info("Fetching Kalshi markets...")
    kalshi_markets = kalshi_client.get_markets()
    logger.info(f"✓ Got {len(kalshi_markets)} Kalshi markets")

    return polymarket_markets, kalshi_markets

def test_mock_data():
    """Test with mock data that has a guaranteed arbitrage opportunity"""
    logger.info("=" * 60)
    logger.info("TESTING WITH MOCK DATA")
    logger.info("=" * 60)

    polymarket_markets, kalshi_markets = create_mock_markets()

    logger.info(f"✓ Created {len(polymarket_markets)} mock Polymarket market(s)")
    logger.info(f"✓ Created {len(kalshi_markets)} mock Kalshi market(s)")
    logger.info("")
    logger.info("Mock Market Details:")
    logger.info(f"  Polymarket: {polymarket_markets[0].question}")
    logger.info(f"    YES: ${polymarket_markets[0].yes_price:.2f}, NO: ${polymarket_markets[0].no_price:.2f}")
    logger.info(f"  Kalshi: {kalshi_markets[0].question}")
    logger.info(f"    YES: ${kalshi_markets[0].yes_price:.2f}, NO: ${kalshi_markets[0].no_price:.2f}")
    logger.info("")
    logger.info("Expected Arbitrage:")
    logger.info(f"  Buy YES on Polymarket (${polymarket_markets[0].yes_price:.2f}) + Buy NO on Kalshi (${kalshi_markets[0].no_price:.2f})")
    logger.info(f"  Total cost: ${polymarket_markets[0].yes_price + kalshi_markets[0].no_price:.2f} → Guaranteed payout: $1.00")
    logger.info(f"  Profit: ${1.0 - (polymarket_markets[0].yes_price + kalshi_markets[0].no_price):.2f} ({(1.0 - (polymarket_markets[0].yes_price + kalshi_markets[0].no_price)) * 100:.1f}%)")
    logger.info("")

    return polymarket_markets, kalshi_markets

def run_arbitrage_test(polymarket_markets, kalshi_markets):
    """Run the arbitrage detection logic"""

    # Match markets
    logger.info("=" * 60)
    logger.info("MATCHING MARKETS")
    logger.info("=" * 60)
    logger.info(f"Min confidence threshold: {config.get('matching', 'min_confidence')}")
    logger.info(f"Using semantic matching: {config.get('matching', 'use_semantic')}")
    logger.info("")

    matches = matcher.match_markets(polymarket_markets, kalshi_markets)

    if not matches:
        logger.info("No market matches found")
        logger.info("")
        logger.info("Sample markets:")
        logger.info(f"  Polymarket sample: {polymarket_markets[0].question if polymarket_markets else 'None'}")
        logger.info(f"  Kalshi sample: {kalshi_markets[0].question if kalshi_markets else 'None'}")
        return

    logger.info(f"✓ Found {len(matches)} market match(es)")
    logger.info("")

    # Calculate arbitrage opportunities
    logger.info("=" * 60)
    logger.info("CALCULATING ARBITRAGE OPPORTUNITIES")
    logger.info("=" * 60)
    logger.info(f"Min profit threshold: {config.get('arbitrage', 'min_profit_pct')}%")
    logger.info(f"Min liquidity: ${config.get('arbitrage', 'min_liquidity')}")
    logger.info("")

    calculator = ArbitrageCalculator(
        min_profit_pct=config.get("arbitrage", "min_profit_pct"),
        min_liquidity=config.get("arbitrage", "min_liquidity")
    )

    opportunities = []
    for match in matches:
        result = calculator.calculate(match.market_a, match.market_b, match.confidence)
        if result:
            opportunities.append(result)

    if not opportunities:
        logger.info("No arbitrage opportunities found")
        logger.info("")
        logger.info("Matched markets did not meet profit/liquidity thresholds:")
        for i, match in enumerate(matches[:3], 1):
            logger.info(f"\n  Match {i} (confidence: {match.confidence:.2%}):")
            logger.info(f"    {match.market_a.platform}: {match.market_a.question[:60]}...")
            logger.info(f"      YES: ${match.market_a.yes_price:.3f}, NO: ${match.market_a.no_price:.3f}")
            logger.info(f"    {match.market_b.platform}: {match.market_b.question[:60]}...")
            logger.info(f"      YES: ${match.market_b.yes_price:.3f}, NO: ${match.market_b.no_price:.3f}")
        return

    logger.info(f"✓ Found {len(opportunities)} arbitrage opportunity(ies)!")
    logger.info("")

    # Display opportunities
    for i, opp in enumerate(opportunities, 1):
        logger.info("=" * 60)
        logger.info(f"ARBITRAGE OPPORTUNITY #{i}")
        logger.info("=" * 60)

        strategy = calculator.get_strategy_description(opp)

        logger.info(f"Match Confidence: {opp.match_confidence:.1%}")
        logger.info(f"Profit: {opp.profit_pct:.2f}%")
        logger.info(f"Total Cost: ${opp.cost:.3f} → Payout: $1.00")
        logger.info("")
        logger.info(f"Market A ({opp.market_a.platform}):")
        logger.info(f"  {opp.market_a.question}")
        logger.info(f"  YES: ${opp.market_a.yes_price:.3f} | NO: ${opp.market_a.no_price:.3f}")
        logger.info(f"  Liquidity: ${opp.market_a.liquidity:,.0f}" if opp.market_a.liquidity else "  Liquidity: Unknown")
        logger.info("")
        logger.info(f"Market B ({opp.market_b.platform}):")
        logger.info(f"  {opp.market_b.question}")
        logger.info(f"  YES: ${opp.market_b.yes_price:.3f} | NO: ${opp.market_b.no_price:.3f}")
        logger.info(f"  Liquidity: ${opp.market_b.liquidity:,.0f}" if opp.market_b.liquidity else "  Liquidity: Unknown")
        logger.info("")
        logger.info("STRATEGY:")
        logger.info(f"  1. {strategy['action_a']}")
        logger.info(f"  2. {strategy['action_b']}")
        logger.info(f"  → {strategy['explanation']}")
        logger.info("")

def main():
    parser = argparse.ArgumentParser(description="Test the arbitrage bot")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real APIs")
    args = parser.parse_args()

    try:
        if args.mock:
            polymarket_markets, kalshi_markets = test_mock_data()
        else:
            polymarket_markets, kalshi_markets = test_real_apis()

        run_arbitrage_test(polymarket_markets, kalshi_markets)

        logger.info("=" * 60)
        logger.info("TEST COMPLETE")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
