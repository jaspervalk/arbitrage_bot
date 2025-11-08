import aiohttp
from typing import List, Dict, Any

async def fetch_kalshi_series(base_url: str) -> List[Dict[str, Any]]:
    url = f"{base_url}/trade-api/v2/series"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("series", [])

async def search_polymarket(base_url: str, query: str) -> List[Dict[str, Any]]:
    url = f"{base_url}/public-search?q={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("markets", [])

async def cross_platform_match(kalshi_base_url: str, polymarket_base_url: str, category: str = None) -> List[Dict[str, Any]]:
    kalshi_series = await fetch_kalshi_series(kalshi_base_url)
    results = []
    for series in kalshi_series:
        if category and series.get("category", "").lower() != category.lower():
            continue
        # Use ticker, title, or description as keywords
        keywords = series.get("ticker", "")
        if not keywords:
            keywords = series.get("title", "")
        if not keywords:
            continue
        polymarket_markets = await search_polymarket(polymarket_base_url, keywords)
        for market in polymarket_markets:
            results.append({
                "kalshi_series": series,
                "polymarket_market": market
            })
    return results

# Example usage:
# import asyncio
# matches = asyncio.run(cross_platform_match(
#     kalshi_base_url="https://api.elections.kalshi.com",
#     polymarket_base_url="https://gamma-api.polymarket.com",
#     category="Politics"
# ))
# print(matches)
