import time
import argparse
from .arbitrage import detector
from .utils import config, logger

def run_once():
    logger.info("Starting arbitrage detection run...")

    opportunities = detector.detect_opportunities()

    if opportunities:
        logger.info(f"\nFound {len(opportunities)} arbitrage opportunities:\n")
        for opp in opportunities:
            print(detector.format_opportunity(opp))
    else:
        logger.info("No arbitrage opportunities found")

    return len(opportunities)

def run_continuous():
    check_interval = config.get("arbitrage", "check_interval")
    logger.info(f"Starting continuous monitoring (checking every {check_interval}s)...")
    logger.info("Press Ctrl+C to stop\n")

    try:
        while True:
            count = run_once()

            logger.info(f"\nWaiting {check_interval} seconds until next check...\n")
            time.sleep(check_interval)

    except KeyboardInterrupt:
        logger.info("\nStopping arbitrage bot...")

def main():
    parser = argparse.ArgumentParser(description='Arbitrage Detection Bot for Polymarket & Kalshi')
    parser.add_argument('--once', action='store_true', help='Run detection once and exit')
    parser.add_argument('--continuous', action='store_true', help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, help='Check interval in seconds (overrides config)')

    args = parser.parse_args()

    if args.interval:
        config.config['arbitrage']['check_interval'] = args.interval

    logger.info("Arbitrage Detection Bot")
    logger.info(f"Min profit threshold: {config.get('arbitrage', 'min_profit_pct')}%")
    logger.info(f"Min liquidity: ${config.get('arbitrage', 'min_liquidity')}")
    logger.info(f"Match confidence: {config.get('matching', 'min_confidence')}\n")

    if args.continuous:
        run_continuous()
    else:
        run_once()

if __name__ == "__main__":
    main()
