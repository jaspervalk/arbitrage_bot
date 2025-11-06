import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.base import Market
from src.matching import SemanticMatcher
from src.arbitrage.calculator import ArbitrageCalculator
from src.arbitrage.detector import ArbitrageDetector
from src.utils import logger

def create_mock_market(platform, market_id, question, yes_price, no_price, liquidity=5000):
    return Market(
        platform=platform,
        market_id=market_id,
        question=question,
        yes_price=yes_price,
        no_price=no_price,
        liquidity=liquidity,
        volume=1000,
        end_date=None,
        raw_data={}
    )

def simulate_full_detection():
    logger.info("Running full arbitrage detection simulation...")
    logger.info("=" * 70 + "\n")

    polymarket_markets = [
        create_mock_market('polymarket', 'pm1', 'Will Trump win the 2024 election?', 0.52, 0.48, 100000),
        create_mock_market('polymarket', 'pm2', 'Bitcoin above $100k by end of 2025?', 0.45, 0.55, 50000),
        create_mock_market('polymarket', 'pm3', 'Fed cuts rates in Q1 2025?', 0.40, 0.60, 30000),
        create_mock_market('polymarket', 'pm4', 'Ukraine peace deal in 2025?', 0.25, 0.75, 20000),
        create_mock_market('polymarket', 'pm5', 'AI reaches AGI in 2025?', 0.08, 0.92, 15000),
    ]

    kalshi_markets = [
        create_mock_market('kalshi', 'k1', 'Trump wins 2024 presidential election', 0.45, 0.55, 80000),
        create_mock_market('kalshi', 'k2', 'BTC price above $100,000 by Dec 31 2025', 0.42, 0.58, 45000),
        create_mock_market('kalshi', 'k3', 'Federal Reserve rate cut Q1 2025', 0.38, 0.62, 25000),
        create_mock_market('kalshi', 'k4', 'Russia Ukraine ceasefire 2025', 0.30, 0.70, 18000),
        create_mock_market('kalshi', 'k5', 'Artificial General Intelligence achieved 2025', 0.12, 0.88, 10000),
    ]

    logger.info(f"Simulating with {len(polymarket_markets)} Polymarket markets")
    logger.info(f"and {len(kalshi_markets)} Kalshi markets\n")

    matcher = SemanticMatcher(min_confidence=0.7, use_semantic=False)
    matches = matcher.match_markets(polymarket_markets, kalshi_markets)

    logger.info(f"Found {len(matches)} market matches\n")

    calculator = ArbitrageCalculator(min_profit_pct=2.0, min_liquidity=1000)
    detector_instance = ArbitrageDetector()

    opportunities = []
    for match in matches:
        result = calculator.calculate(match.market_a, match.market_b, match.confidence)
        if result:
            opportunities.append(result)

    opportunities.sort(key=lambda x: x.profit_pct, reverse=True)

    if opportunities:
        logger.info(f"Found {len(opportunities)} arbitrage opportunities:\n")
        for i, opp in enumerate(opportunities, 1):
            logger.info(f"\nOpportunity #{i}:")
            print(detector_instance.format_opportunity(opp))
    else:
        logger.info("No arbitrage opportunities found in simulation")

    return len(opportunities)

if __name__ == "__main__":
    count = simulate_full_detection()
    logger.info(f"\n\nSimulation complete: {count} opportunities detected")
