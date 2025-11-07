#!/usr/bin/env python3
"""Debug Kalshi market data to see why prices are $0"""

from src.api import KalshiClient
from src.utils import config
import json

kalshi = KalshiClient(
    config.get("apis", "kalshi", "base_url"),
    api_key_id=config.get("apis", "kalshi", "api_key_id"),
    private_key_str=config.get("apis", "kalshi", "private_key")
)

print("Fetching Kalshi markets...")
markets = kalshi.get_markets(limit=5)

print(f"\n{'='*80}")
print(f"Found {len(markets)} markets")
print(f"{'='*80}\n")

for i, market in enumerate(markets, 1):
    print(f"\n{i}. {market.question[:100]}")
    print(f"   YES: ${market.yes_price:.3f} | NO: ${market.no_price:.3f}")
    print(f"   Liquidity: ${market.liquidity:,.0f}")
    print(f"   Volume: ${market.volume:,.0f}")

    # Show raw data to debug
    print(f"\n   Raw data snippet:")
    raw = market.raw_data
    print(f"   - status: {raw.get('status')}")
    print(f"   - yes_bid: {raw.get('yes_bid')}")
    print(f"   - yes_ask: {raw.get('yes_ask')}")
    print(f"   - no_bid: {raw.get('no_bid')}")
    print(f"   - no_ask: {raw.get('no_ask')}")
    print(f"   - last_price: {raw.get('last_price')}")
    print(f"   - open_interest: {raw.get('open_interest')}")

    if i == 3:
        print(f"\n   Full raw JSON:")
        print(json.dumps(raw, indent=2)[:500])
