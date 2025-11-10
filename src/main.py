import asyncio
import time
import argparse
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from .api import KalshiClient, PolymarketClient, Market
from .utils import config, logger, notifier
from .core import cache, knowledge_base
from .arbitrage import detector

CATEGORIES = ["politics", "economy", "crypto", "sports"]
DATA_DIR = Path("data")

async def fetch_markets_for_category(
    kalshi: KalshiClient,
    polymarket: PolymarketClient,
    category: str,
    limit: int = 100
) -> List[Market]:
    """
    Fetch markets from both platforms for a specific category.
    
    Args:
        kalshi: Kalshi API client
        polymarket: Polymarket API client
        category: Category to fetch markets for
        limit: Maximum markets per platform
    """
    try:
        # Fetch from both platforms concurrently
        kalshi_markets, poly_markets = await asyncio.gather(
            kalshi.get_markets_by_category(category, limit),
            polymarket.get_markets_by_category(category, limit)
        )
        
        return kalshi_markets + poly_markets
        
    except Exception as e:
        logger.error(f"Failed to fetch markets for category {category}: {e}")
        return []

async def update_all_markets() -> Dict[str, List[Market]]:
    """
    Fetch and cache markets from all platforms, organized by category.
    Updates semantic embeddings for all markets.
    """
    try:
        # Initialize API clients
        kalshi = KalshiClient(
            base_url=config.get("apis", "kalshi", "base_url"),
            timeout=config.get("apis", "kalshi", "timeout"),
            api_key_id=config.get("apis", "kalshi", "api_key_id"),
            private_key_str=config.get("apis", "kalshi", "private_key")
        )
        
        polymarket = PolymarketClient(
            base_url=config.get("apis", "polymarket", "base_url"),
            timeout=config.get("apis", "polymarket", "timeout")
        )

        # Ensure data directory exists
        DATA_DIR.mkdir(exist_ok=True)
        
        markets_by_category = {}
        all_markets = []
        
        # Fetch markets for each category concurrently
        for category in CATEGORIES:
            markets = await fetch_markets_for_category(
                kalshi, polymarket, category
            )
            markets_by_category[category] = markets
            all_markets.extend(markets)
            
            # Cache category markets
            cache.save_data(
                f"{category}_markets.json",
                [m.__dict__ for m in markets]
            )
            
            logger.info(
                f"Cached {len(markets)} {category} markets "
                f"({len([m for m in markets if m.platform == 'kalshi'])} Kalshi, "
                f"{len([m for m in markets if m.platform == 'polymarket'])} Polymarket)"
            )
            
        # Cache combined markets
        cache.save_data(
            "combined_markets.json",
            [m.__dict__ for m in all_markets]
        )
        
        # Update semantic embeddings
        knowledge_base.update_embeddings(all_markets)
        logger.info(f"Updated semantic embeddings for {len(all_markets)} markets")
        
        return markets_by_category
        
    except Exception as e:
        logger.error(f"Failed to update markets: {e}")
        return {}

def get_cached_markets(category: str = None) -> List[Market]:
    """
    Get cached markets, optionally filtered by category.
    
    Args:
        category: Optional category to filter by
    """
    try:
        if category:
            cached = cache.load_data(f"{category}_markets.json")
            if cached:
                return [Market(**m) for m in cached]
        else:
            cached = cache.load_data("combined_markets.json")
            if cached:
                return [Market(**m) for m in cached]
                
        return []
        
    except Exception as e:
        logger.error(f"Failed to load cached markets: {e}")
        return []

async def run_once():
    """Run one iteration of market updates and arbitrage detection."""
    logger.info("Starting market data update and arbitrage detection...")
    
    start_time = datetime.now()
    markets = await update_all_markets()
    update_duration = (datetime.now() - start_time).total_seconds()
    
    total_markets = sum(len(m) for m in markets.values())
    logger.info(f"Market update complete - Fetched {total_markets} markets in {update_duration:.1f}s")
    
    opportunities = detector.detect_opportunities()
    
    if opportunities:
        logger.info(f"\nFound {len(opportunities)} arbitrage opportunities:\n")
        for opp in opportunities:
            formatted_opp = detector.format_opportunity(opp)
            print(formatted_opp)
            notifier.send_arbitrage_opportunity(formatted_opp)
    else:
        logger.info("No arbitrage opportunities found")
    
    return len(opportunities)

async def run_continuous():
    """Run continuous market updates and arbitrage detection."""
    check_interval = config.get("arbitrage", "check_interval")
    logger.info(f"Starting continuous monitoring (checking every {check_interval}s)...")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        while True:
            await run_once()
            logger.info(f"\nWaiting {check_interval} seconds until next check...\n")
            await asyncio.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("\nStopping arbitrage bot...")

def main():
    """Main entry point for the arbitrage bot."""
    parser = argparse.ArgumentParser(
        description='Arbitrage Detection Bot for Polymarket & Kalshi'
    )
    parser.add_argument(
        '--once', 
        action='store_true',
        help='Run detection once and exit'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run continuous monitoring'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Check interval in seconds (overrides config)'
    )
    parser.add_argument(
        '--update-only',
        action='store_true',
        help='Only update market data without checking for arbitrage'
    )
    parser.add_argument(
        '--category',
        choices=CATEGORIES,
        help='Only process specific market category'
    )

    args = parser.parse_args()

    if args.interval:
        config.config['arbitrage']['check_interval'] = args.interval

    logger.info("Arbitrage Detection Bot")
    logger.info(f"Min profit threshold: {config.get('arbitrage', 'min_profit_pct')}%")
    logger.info(f"Min liquidity: ${config.get('arbitrage', 'min_liquidity')}")
    logger.info(f"Match confidence: {config.get('matching', 'min_confidence')}")
    if args.category:
        logger.info(f"Processing category: {args.category}")
    logger.info("")

    try:
        if args.continuous:
            asyncio.run(run_continuous())
        else:
            asyncio.run(run_once())
            
    except KeyboardInterrupt:
        logger.info("\nStopping arbitrage bot...")
        
if __name__ == "__main__":
    main()
