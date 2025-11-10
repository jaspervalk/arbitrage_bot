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
    cross_reference = []
    for series in kalshi_series:
        if category and series.get("category", "").lower() != category.lower():
            continue
        title = series.get("title", "")
        if not title:
            print(f"Skipping Kalshi series (no title): {series}")
            continue
        print(f"Checking Kalshi series: {series.get('ticker','')} | {title} | {series.get('category','')}")
        async def full_search(base_url, query):
            url = f"{base_url}/public-search?q={query}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    resp.raise_for_status()
                    return await resp.json()

        try:
            search_results = await full_search(POLYMARKET_URL, title)
        except aiohttp.ClientResponseError as e:
            print(f"  Polymarket search failed for title '{title}': {e.status} {e.message}")
            checked += 1
            print(f"  No Polymarket markets, events, or profiles for title '{title}' (API error)")
            continue
        except Exception as e:
            print(f"  Polymarket search failed for title '{title}': {e}")
            checked += 1
            print(f"  No Polymarket markets, events, or profiles for title '{title}' (API error)")
            continue
        checked += 1
        found_any = False
        for key in ["markets", "events", "profiles"]:
            items = search_results.get(key, [])
            if items:
                found_any = True
                print(f"  Found {len(items)} Polymarket {key} for title '{title}':")
                for item in items:
                    if key == "markets":
                        print(f"    Market: {item.get('id','')} | {item.get('question','')}" )
                    elif key == "events":
                        event_id = item.get('id','')
                        event_title = item.get('name','')
                        ticker = None
                        event_data = None
                        market_list = []
                        if event_id:
                            event_url = f"https://gamma-api.polymarket.com/events/{event_id}"
                            async with aiohttp.ClientSession() as session:
                                try:
                                    async with session.get(event_url) as event_resp:
                                        event_resp.raise_for_status()
                                        event_data = await event_resp.json()
                                        ticker = event_data.get('ticker') or event_data.get('name')
                                        market_list = event_data.get('markets', [])
                                except Exception as e:
                                    print(f"      Error fetching event details for {event_id}: {e}")
                        print(f"    Event: {event_id} | {ticker if ticker else event_title}")
                        open_markets = [m for m in market_list if m.get('active', True) and not m.get('closed', False)]
                        print(f"      Open markets for event {event_id}: {len(open_markets)}")
                        for market in open_markets:
                            market_id = market.get('id', '')
                            question = market.get('question', '')
                            volume = market.get('volume', market.get('volumeNum', 0))
                            outcomes = market.get('outcomes', [])
                            outcome_prices = market.get('outcomePrices', [])
                            last_volume = market.get('volume24hr', 0)
                            # Parse outcomes and prices if they are JSON strings
                            import json as _json
                            if isinstance(outcomes, str):
                                try:
                                    outcomes = _json.loads(outcomes)
                                except:
                                    pass
                            if isinstance(outcome_prices, str):
                                try:
                                    outcome_prices = _json.loads(outcome_prices)
                                except:
                                    pass
                            print(f"        Market: {market_id} | {question}")
                            print(f"          Volume: {volume}")
                            print(f"          Last 24hr Volume: {last_volume}")
                            print(f"          Outcomes: {outcomes}")
                            print(f"          Prices: {outcome_prices}")
                        # Save standardized info for cross referencing
                        cross_reference.append({
                            "kalshi_series": series,
                            "polymarket_event": event_data if event_data else item,
                            "polymarket_markets": open_markets
                        })
                    elif key == "profiles":
                        print(f"    Profile: {item.get('id','')} | {item.get('name','')}")
        if found_any:
            matched += 1
        else:
            print(f"  No Polymarket markets, events, or profiles for title '{title}'")
    # Output standardized cross-reference data
    import json
    print("\nStandardized cross-reference data:")
    print(json.dumps(cross_reference, indent=2, default=str))
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
