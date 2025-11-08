import argparse
import asyncio
import time
import aiohttp
from src.matching.cross_platform_matcher import cross_platform_match

KALSHI_URL = "https://api.elections.kalshi.com"
POLYMARKET_URL = "https://gamma-api.polymarket.com"

async def run_once(category):
    print(f"Fetching Kalshi series for category '{category}'...")
    from src.matching.cross_platform_matcher import fetch_kalshi_series, search_polymarket
    kalshi_series = await fetch_kalshi_series(KALSHI_URL)
    checked = 0
    matched = 0
    for series in kalshi_series:
        if category and series.get("category", "").lower() != category.lower():
            continue
        title = series.get("title", "")
        if not title:
            print(f"Skipping Kalshi series (no title): {series}")
            continue
        print(f"Checking Kalshi series: {series.get('ticker','')} | {title} | {series.get('category','')}")
        # The search endpoint returns a dict with keys: 'markets', 'events', 'profiles'
        async def full_search(base_url, query):
            url = f"{base_url}/public-search?q={query}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    return await resp.json()

        search_results = await full_search(POLYMARKET_URL, title)
        checked += 1
        found_any = False
        for key in ["markets", "events", "profiles"]:
            items = search_results.get(key, [])
            if items:
                found_any = True
                print(f"  Found {len(items)} Polymarket {key} for title '{title}':")
                for item in items:
                    if key == "markets":
                        print(f"    Market: {item.get('id','')} | {item.get('question','')}")
                    elif key == "events":
                        print(f"    Event: {item.get('id','')} | {item.get('name','')}")
                    elif key == "profiles":
                        print(f"    Profile: {item.get('id','')} | {item.get('name','')}")
        if found_any:
            matched += 1
        else:
            print(f"  No Polymarket markets, events, or profiles for title '{title}'")
    print(f"Checked {checked} Kalshi series, {matched} had Polymarket matches.")

async def run_watch(category, interval):
    while True:
        await run_once(category)
        print(f"Waiting {interval} seconds before next check...")
        await asyncio.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Cross-platform market matcher")
    parser.add_argument("--category", type=str, default="Politics", help="Market category to check")
    parser.add_argument("--once", action="store_true", help="Run one-time market scan")
    parser.add_argument("--watch", type=int, metavar="SECONDS", help="Continuously check every N seconds")
    args = parser.parse_args()

    if args.once:
        asyncio.run(run_once(args.category))
    elif args.watch:
        asyncio.run(run_watch(args.category, args.watch))
    else:
        print("Specify --once for one-time scan or --watch N for continuous mode.")

if __name__ == "__main__":
    main()
