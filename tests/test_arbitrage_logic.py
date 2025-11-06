import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.base import Market
from src.arbitrage.calculator import ArbitrageCalculator
from src.utils import logger

def create_mock_market(platform, question, yes_price, no_price, liquidity=1000):
    return Market(
        platform=platform,
        market_id=f"test_{platform}",
        question=question,
        yes_price=yes_price,
        no_price=no_price,
        liquidity=liquidity,
        volume=500,
        end_date=None,
        raw_data={}
    )

def test_arbitrage_detection():
    logger.info("Testing arbitrage detection logic with mock markets...\n")

    calculator = ArbitrageCalculator(min_profit_pct=1.0, min_liquidity=100)

    test_cases = [
        {
            'name': 'Clear arbitrage opportunity',
            'market_a': create_mock_market('polymarket', 'Will Trump win 2024?', 0.52, 0.48, 10000),
            'market_b': create_mock_market('kalshi', 'Trump 2024 Victory', 0.45, 0.55, 8000),
            'expected_arb': True
        },
        {
            'name': 'Efficient market (minimal arbitrage)',
            'market_a': create_mock_market('polymarket', 'Bitcoin above $100k?', 0.50, 0.50, 10000),
            'market_b': create_mock_market('kalshi', 'BTC $100k+', 0.49, 0.51, 8000),
            'expected_arb': True
        },
        {
            'name': 'Mispriced markets (good arbitrage)',
            'market_a': create_mock_market('polymarket', 'Fed rate cut 2025?', 0.40, 0.60, 5000),
            'market_b': create_mock_market('kalshi', 'Fed cuts rates 2025', 0.42, 0.58, 6000),
            'expected_arb': True
        },
        {
            'name': 'Low liquidity (should be rejected)',
            'market_a': create_mock_market('polymarket', 'Some event', 0.40, 0.60, 50),
            'market_b': create_mock_market('kalshi', 'Same event', 0.42, 0.58, 6000),
            'expected_arb': False
        },
        {
            'name': 'Small profit margin (below threshold)',
            'market_a': create_mock_market('polymarket', 'Event A', 0.495, 0.505, 10000),
            'market_b': create_mock_market('kalshi', 'Event A', 0.49, 0.51, 10000),
            'expected_arb': False
        }
    ]

    passed = 0
    for i, test in enumerate(test_cases, 1):
        logger.info(f"Test {i}: {test['name']}")
        logger.info(f"  Market A: Yes={test['market_a'].yes_price:.3f}, No={test['market_a'].no_price:.3f}")
        logger.info(f"  Market B: Yes={test['market_b'].yes_price:.3f}, No={test['market_b'].no_price:.3f}")

        result = calculator.calculate(test['market_a'], test['market_b'], match_confidence=1.0)

        has_arb = result is not None
        expected = test['expected_arb']

        if has_arb:
            logger.info(f"  Result: ARBITRAGE FOUND - {result.profit_pct:.2f}% profit")
            logger.info(f"  Strategy: {result.strategy}, Cost: {result.cost:.3f}")
        else:
            logger.info(f"  Result: No arbitrage")

        if has_arb == expected:
            logger.info(f"  Status: PASS\n")
            passed += 1
        else:
            logger.info(f"  Status: FAIL (expected arbitrage={expected})\n")

    logger.info(f"Test Results: {passed}/{len(test_cases)} passed")

if __name__ == "__main__":
    test_arbitrage_detection()
