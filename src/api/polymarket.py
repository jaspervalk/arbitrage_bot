from typing import List, Optional
from datetime import datetime
from .base import BaseAPIClient, Market
from ..utils.logger import logger

class PolymarketClient(BaseAPIClient):
    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__(base_url, timeout)

    def get_markets(self, limit: int = 100, active_only: bool = True) -> List[Market]:
        cache_key = f"polymarket_markets_{limit}_{active_only}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            endpoint = "/markets"
            params = {
                "limit": limit,
                "closed": "false" if active_only else None
            }
            params = {k: v for k, v in params.items() if v is not None}

            data = self._make_request("GET", endpoint, params=params)

            markets = []
            for item in data:
                try:
                    market = self._parse_market(item)
                    if market:
                        markets.append(market)
                except Exception as e:
                    logger.warning(f"Failed to parse Polymarket market: {e}")
                    continue

            self._set_cache(cache_key, markets)
            logger.info(f"Fetched {len(markets)} markets from Polymarket")
            return markets

        except Exception as e:
            logger.error(f"Failed to fetch Polymarket markets: {e}")
            return []

    def _parse_market(self, data: dict) -> Optional[Market]:
        try:
            question = data.get("question", "")
            if not question:
                return None

            if data.get("closed", False):
                return None

            outcome_prices_str = data.get("outcomePrices", "[]")
            if isinstance(outcome_prices_str, str):
                import json
                outcome_prices = json.loads(outcome_prices_str)
            else:
                outcome_prices = outcome_prices_str

            if len(outcome_prices) != 2:
                return None

            yes_price = float(outcome_prices[0])
            no_price = float(outcome_prices[1])

            if yes_price == 0 and no_price == 0:
                return None

            end_date_str = data.get("endDate")
            end_date = None
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                except:
                    pass

            return Market(
                platform="polymarket",
                market_id=data.get("conditionId", ""),
                question=question,
                yes_price=yes_price,
                no_price=no_price,
                liquidity=float(data.get("liquidityNum", 0)),
                volume=float(data.get("volumeNum", 0)),
                end_date=end_date,
                raw_data=data
            )
        except Exception as e:
            logger.warning(f"Error parsing Polymarket market: {e}")
            return None
