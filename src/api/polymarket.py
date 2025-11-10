from typing import List, Optional, Dict
from datetime import datetime
import aiohttp
import json
from .base import BaseAPIClient, Market
from ..utils.logger import logger
from ..core import cache

class PolymarketClient(BaseAPIClient):
    # Map our standard categories to Polymarket tags/keywords
    CATEGORY_MAP = {
        "politics": ["election", "politics", "president", "congress", "senate"],
        "economy": ["gdp", "cpi", "inflation", "rate", "fed", "recession"],
        "crypto": ["bitcoin", "ethereum", "crypto", "btc", "eth"],
        "sports": ["nfl", "nba", "mlb", "nhl", "sports", "football", "basketball"],
    }

    def __init__(self, base_url: str, timeout: int = 30):
        super().__init__(base_url, timeout)
        self.graphql_url = f"{base_url}/graphql"

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

    async def _make_graphql_request(self, session: aiohttp.ClientSession,
                                  query: str, variables: Dict = None) -> Dict:
        """Make an async GraphQL request."""
        try:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            async with session.post(self.graphql_url, json=payload) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"GraphQL request failed: {e}")
            raise

    async def get_markets_by_category(self, category: str,
                                    limit: int = 100) -> List[Market]:
        """
        Fetch markets for a specific category using the GraphQL API.
        
        Args:
            category: Category to fetch markets for (politics, economy, crypto, sports)
            limit: Maximum number of markets to fetch
        """
        cache_key = f"polymarket_markets_{category}_{limit}"
        cached = cache.load_data(cache_key, max_age_hours=1)
        if cached:
            return [Market(**m) for m in cached]

        try:
            keywords = self.CATEGORY_MAP.get(category.lower(), [])
            if not keywords:
                logger.warning(f"Unknown category: {category}")
                return []

            # GraphQL query for markets with category filtering
            query = """
            query GetMarkets($keyword: String!) {
                markets(
                    where: { 
                        question_contains_nocase: $keyword,
                        closed: false
                    }
                    first: 100,
                    orderBy: liquidityNum,
                    orderDirection: desc
                ) {
                    id
                    question
                    outcomePrices
                    liquidity
                    volumeNum
                    endDate
                }
            }
            """

            markets = []
            async with aiohttp.ClientSession() as session:
                # Query for each keyword in the category
                for keyword in keywords:
                    try:
                        result = await self._make_graphql_request(
                            session, 
                            query, 
                            variables={"keyword": keyword}
                        )

                        if result.get("errors"):
                            logger.error(f"GraphQL error: {result['errors']}")
                            continue

                        market_data = result.get("data", {}).get("markets", [])
                        for item in market_data:
                            market = self._parse_market(item)
                            if market:
                                markets.append(market)

                    except Exception as e:
                        logger.error(f"Failed to fetch markets for keyword '{keyword}': {e}")
                        continue

            # Remove duplicates based on market_id
            unique_markets = list({m.market_id: m for m in markets}.values())
            markets = sorted(unique_markets, key=lambda x: x.liquidity or 0, reverse=True)[:limit]

            # Cache the results
            cache.save_data(cache_key, [m.__dict__ for m in markets])
            logger.info(f"Fetched {len(markets)} {category} markets from Polymarket")
            return markets

        except Exception as e:
            logger.error(f"Failed to fetch {category} markets from Polymarket: {e}")
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
