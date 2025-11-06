from typing import List, Optional
from datetime import datetime
from .base import BaseAPIClient, Market
from ..utils.logger import logger
import time

class KalshiClient(BaseAPIClient):
    def __init__(self, base_url: str, timeout: int = 30, email: Optional[str] = None, password: Optional[str] = None):
        super().__init__(base_url, timeout)
        self.email = email
        self.password = password
        self.token = None
        self.token_expiry = 0

    def _ensure_authenticated(self) -> None:
        if self.token and time.time() < self.token_expiry:
            return

        if not self.email or not self.password:
            logger.warning("Kalshi credentials not provided, using public API only")
            return

        try:
            response = self._make_request(
                "POST",
                "/trade-api/v2/login",
                json={"email": self.email, "password": self.password}
            )
            self.token = response.get("token")
            self.token_expiry = time.time() + 3600
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            logger.info("Successfully authenticated with Kalshi")
        except Exception as e:
            logger.error(f"Failed to authenticate with Kalshi: {e}")

    def get_markets(self, limit: int = 200, status: str = "open") -> List[Market]:
        cache_key = f"kalshi_markets_{limit}_{status}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        try:
            self._ensure_authenticated()

            endpoint = "/trade-api/v2/markets"
            params = {
                "limit": limit,
                "status": status
            }

            data = self._make_request("GET", endpoint, params=params)
            market_data = data.get("markets", [])

            markets = []
            for item in market_data:
                try:
                    market = self._parse_market(item)
                    if market:
                        markets.append(market)
                except Exception as e:
                    logger.warning(f"Failed to parse Kalshi market: {e}")
                    continue

            self._set_cache(cache_key, markets)
            logger.info(f"Fetched {len(markets)} markets from Kalshi")
            return markets

        except Exception as e:
            logger.error(f"Failed to fetch Kalshi markets: {e}")
            return []

    def _parse_market(self, data: dict) -> Optional[Market]:
        try:
            title = data.get("title", "")
            if not title:
                return None

            if data.get("status") != "active":
                return None

            yes_bid = float(data.get("yes_bid", 0)) / 100.0
            no_bid = float(data.get("no_bid", 0)) / 100.0
            yes_ask = float(data.get("yes_ask", 0)) / 100.0
            no_ask = float(data.get("no_ask", 0)) / 100.0

            yes_price = (yes_bid + yes_ask) / 2 if (yes_bid > 0 or yes_ask > 0) else 0
            no_price = (no_bid + no_ask) / 2 if (no_bid > 0 or no_ask > 0) else 0

            if yes_price == 0 and no_price == 0:
                return None

            if yes_price == 0 and no_price > 0:
                yes_price = 1 - no_price
            elif no_price == 0 and yes_price > 0:
                no_price = 1 - yes_price

            close_time_str = data.get("close_time")
            end_date = None
            if close_time_str:
                try:
                    end_date = datetime.fromisoformat(close_time_str.replace("Z", "+00:00"))
                except:
                    pass

            volume = float(data.get("volume", 0))
            open_interest = float(data.get("open_interest", 0))
            liquidity = volume + open_interest

            return Market(
                platform="kalshi",
                market_id=data.get("ticker", ""),
                question=title,
                yes_price=yes_price,
                no_price=no_price,
                liquidity=liquidity,
                volume=volume,
                end_date=end_date,
                raw_data=data
            )
        except Exception as e:
            logger.warning(f"Error parsing Kalshi market: {e}")
            return None
