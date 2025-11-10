from typing import List, Optional, Dict
from datetime import datetime
import aiohttp
import asyncio
import time
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from .base import BaseAPIClient, Market
from ..utils.logger import logger
from ..core import cache

class KalshiClient(BaseAPIClient):
    # Map our standard categories to Kalshi series tags
    CATEGORY_MAP = {
        "politics": ["POLITICS", "ELECTORAL"],
        "economy": ["ECONOMIC", "FED", "MACRO"],
        "crypto": ["CRYPTO"],
        "sports": ["SPORTS", "NFL", "NBA", "MLB", "NHL"],
    }

    def __init__(self, base_url: str, timeout: int = 30,
                 api_key_id: Optional[str] = None,
                 private_key_str: Optional[str] = None):
        super().__init__(base_url, timeout)
        self.api_key_id = api_key_id
        self.private_key_str = private_key_str
        self.token = None
        self.token_expiry = 0

    async def _make_async_request(self, session: aiohttp.ClientSession, 
                                method: str, endpoint: str, **kwargs) -> Dict:
        """Make an async HTTP request."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Async request failed for {url}: {e}")
            raise

    def _ensure_authenticated(self) -> None:
        """Ensure we have a valid JWT token."""
        if self.token and time.time() < self.token_expiry:
            return

        if not self.api_key_id or not self.private_key_str:
            logger.debug("Kalshi API credentials not provided, using public API only")
            return

        try:
            current_time = int(time.time())
            payload = {
                'iss': self.api_key_id,
                'exp': current_time + 1800,
                'iat': current_time
            }

            private_key_pem = self.private_key_str.replace('\\n', '\n')
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None,
                backend=default_backend()
            )

            signed_jwt = jwt.encode(payload, private_key, algorithm='RS256')
            self.token = signed_jwt
            self.token_expiry = current_time + 1800
            
            logger.info("Kalshi API authentication configured")
            
        except Exception as e:
            logger.error(f"Kalshi authentication failed: {e}")
            raise

    async def get_series(self) -> List[Dict]:
        """Fetch all market series from Kalshi."""
        cache_key = "kalshi_series"
        cached = cache.load_data(cache_key, max_age_hours=24)
        if cached:
            return cached

        self._ensure_authenticated()
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

        async with aiohttp.ClientSession(headers=headers) as session:
            data = await self._make_async_request(
                session, "GET", "/trading-api/v2/series"
            )
            series = data.get("series", [])
            cache.save_data(cache_key, series)
            return series

    async def get_markets_by_category(self, category: str, 
                                    limit: int = 200) -> List[Market]:
        """
        Fetch markets for a specific category.
        
        Args:
            category: Category to fetch markets for (politics, economy, crypto, sports)
            limit: Maximum number of markets to fetch
        """
        cache_key = f"kalshi_markets_{category}_{limit}"
        cached = cache.load_data(cache_key, max_age_hours=1)
        if cached:
            return [Market(**m) for m in cached]

        try:
            self._ensure_authenticated()
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

            # Get relevant series tags for category
            category_tags = self.CATEGORY_MAP.get(category.lower(), [])
            if not category_tags:
                logger.warning(f"Unknown category: {category}")
                return []

            # Get all series first
            series = await self.get_series()
            relevant_series = [
                s for s in series
                if any(tag in s.get("tags", []) for tag in category_tags)
            ]

            markets = []
            async with aiohttp.ClientSession(headers=headers) as session:
                for series_data in relevant_series:
                    series_id = series_data["id"]
                    
                    # Fetch markets in this series
                    endpoint = f"/trading-api/v2/markets"
                    params = {
                        "series_id": series_id,
                        "status": "active",
                        "limit": limit
                    }
                    
                    try:
                        data = await self._make_async_request(
                            session, "GET", endpoint, params=params
                        )
                        
                        for item in data.get("markets", []):
                            market = self._parse_market(item)
                            if market:
                                markets.append(market)
                                
                            if len(markets) >= limit:
                                break
                                
                    except Exception as e:
                        logger.error(f"Failed to fetch markets for series {series_id}: {e}")
                        continue

            # Cache the results
            cache.save_data(cache_key, [m.__dict__ for m in markets])
            logger.info(f"Fetched {len(markets)} {category} markets from Kalshi")
            return markets

        except Exception as e:
            logger.error(f"Failed to fetch {category} markets from Kalshi: {e}")
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
