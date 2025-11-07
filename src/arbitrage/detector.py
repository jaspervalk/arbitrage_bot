from typing import List
from ..api import PolymarketClient, KalshiClient
from ..matching import matcher
from .calculator import calculator, ArbitrageResult
from ..utils import config, logger

class ArbitrageDetector:
    def __init__(self):
        self.polymarket = PolymarketClient(
            base_url=config.get("apis", "polymarket", "base_url"),
            timeout=config.get("apis", "polymarket", "timeout")
        )

        kalshi_api_key_id = config.get("apis", "kalshi", "api_key_id") or None
        kalshi_private_key = config.get("apis", "kalshi", "private_key") or None

        self.kalshi = KalshiClient(
            base_url=config.get("apis", "kalshi", "base_url"),
            timeout=config.get("apis", "kalshi", "timeout"),
            api_key_id=kalshi_api_key_id,
            private_key_str=kalshi_private_key
        )

        self.min_profit = config.get("arbitrage", "min_profit_pct")

    def detect_opportunities(self) -> List[ArbitrageResult]:
        logger.info("Fetching markets from both platforms...")

        polymarket_markets = self.polymarket.get_markets(limit=100)
        kalshi_markets = self.kalshi.get_markets(limit=200)

        if not polymarket_markets:
            logger.warning("No markets fetched from Polymarket")
        if not kalshi_markets:
            logger.warning("No markets fetched from Kalshi")

        if not polymarket_markets or not kalshi_markets:
            return []

        logger.info("Matching markets...")
        matches = matcher.match_markets(polymarket_markets, kalshi_markets)

        opportunities = []
        for match in matches:
            result = calculator.calculate(
                match.market_a,
                match.market_b,
                match.confidence
            )

            if result:
                opportunities.append(result)

        opportunities.sort(key=lambda x: x.profit_pct, reverse=True)

        return opportunities

    def format_opportunity(self, opp: ArbitrageResult) -> str:
        strategy = calculator.get_strategy_description(opp)

        lines = [
            "\n" + "=" * 70,
            "ARBITRAGE OPPORTUNITY FOUND",
            "=" * 70,
            f"Match Confidence: {opp.match_confidence * 100:.1f}%",
            f"\n{opp.market_a.platform.upper()}: \"{opp.market_a.question}\"",
            f"  Yes: {opp.market_a.yes_price:.3f} | No: {opp.market_a.no_price:.3f}",
            f"  Liquidity: ${opp.market_a.liquidity:,.0f}" if opp.market_a.liquidity else "",
            f"\n{opp.market_b.platform.upper()}: \"{opp.market_b.question}\"",
            f"  Yes: {opp.market_b.yes_price:.3f} | No: {opp.market_b.no_price:.3f}",
            f"  Liquidity: ${opp.market_b.liquidity:,.0f}" if opp.market_b.liquidity else "",
            f"\nSTRATEGY:",
            f"  1. {strategy['action_a']}",
            f"  2. {strategy['action_b']}",
            f"  {strategy['explanation']}",
            f"\nTotal Cost: {opp.cost:.3f}",
            f"Guaranteed Profit: {1.0 - opp.cost:.3f} ({opp.profit_pct:.2f}%)",
            "=" * 70
        ]

        return "\n".join(line for line in lines if line is not None)

detector = ArbitrageDetector()
