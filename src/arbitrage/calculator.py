from typing import Optional, Dict
from ..api.base import Market

class ArbitrageResult:
    def __init__(self, market_a: Market, market_b: Market, profit_pct: float,
                 strategy: str, cost: float, match_confidence: float):
        self.market_a = market_a
        self.market_b = market_b
        self.profit_pct = profit_pct
        self.strategy = strategy
        self.cost = cost
        self.match_confidence = match_confidence

    def __repr__(self):
        return (f"ArbitrageResult(profit={self.profit_pct:.2f}%, "
                f"strategy={self.strategy}, cost={self.cost:.3f})")

class ArbitrageCalculator:
    def __init__(self, min_profit_pct: float = 2.0, min_liquidity: float = 100):
        self.min_profit_pct = min_profit_pct
        self.min_liquidity = min_liquidity

    def calculate(self, market_a: Market, market_b: Market,
                  match_confidence: float) -> Optional[ArbitrageResult]:

        # Reject markets with invalid prices (must have real bids/asks)
        if market_a.yes_price <= 0 or market_a.no_price <= 0:
            return None
        if market_b.yes_price <= 0 or market_b.no_price <= 0:
            return None

        # Reject markets with prices that don't sum close to 1.0 (invalid data)
        sum_a = market_a.yes_price + market_a.no_price
        sum_b = market_b.yes_price + market_b.no_price
        if sum_a < 0.95 or sum_a > 1.05 or sum_b < 0.95 or sum_b > 1.05:
            return None

        if market_a.liquidity and market_a.liquidity < self.min_liquidity:
            return None
        if market_b.liquidity and market_b.liquidity < self.min_liquidity:
            return None

        scenarios = [
            ('yes_a_no_b', market_a.yes_price + market_b.no_price),
            ('no_a_yes_b', market_a.no_price + market_b.yes_price),
        ]

        best_scenario = None
        best_profit = -float('inf')

        for strategy, cost in scenarios:
            profit = 1.0 - cost
            profit_pct = profit * 100

            if profit_pct > best_profit:
                best_profit = profit_pct
                best_scenario = (strategy, cost)

        if best_profit >= self.min_profit_pct:
            strategy, cost = best_scenario
            return ArbitrageResult(
                market_a=market_a,
                market_b=market_b,
                profit_pct=best_profit,
                strategy=strategy,
                cost=cost,
                match_confidence=match_confidence
            )

        return None

    def get_strategy_description(self, result: ArbitrageResult) -> Dict[str, str]:
        if result.strategy == 'yes_a_no_b':
            return {
                'action_a': f"Buy Yes on {result.market_a.platform} ({result.market_a.yes_price:.3f})",
                'action_b': f"Buy No on {result.market_b.platform} ({result.market_b.no_price:.3f})",
                'explanation': "If event happens, profit from A. If not, profit from B."
            }
        else:
            return {
                'action_a': f"Buy No on {result.market_a.platform} ({result.market_a.no_price:.3f})",
                'action_b': f"Buy Yes on {result.market_b.platform} ({result.market_b.yes_price:.3f})",
                'explanation': "If event happens, profit from B. If not, profit from A."
            }

calculator = ArbitrageCalculator()
