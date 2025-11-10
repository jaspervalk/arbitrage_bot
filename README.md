# Cross-Platform Market Matcher

This module allows you to compare and log markets, events, and profiles between Kalshi and Polymarket using their public APIs.

### How to Run

**One-time scan:**
```bash
python cross_platform_runner.py --once --category Politics
```

**Continuous monitoring (every 60 seconds):**
```bash
python cross_platform_runner.py --watch 60 --category Politics
```

You can change the category (e.g., "Economy", "Crypto", "Sports") as needed.

**What it does:**
- Fetches all Kalshi series for the given category
- For each series, searches Polymarket for related markets, events, and profiles using the series title
- Logs all checked markets, events, and profiles, including reasons for non-matches

This is useful for research, debugging, and monitoring cross-platform market overlap.
# Arbitrage Bot

Automated arbitrage detection bot for prediction markets (Polymarket & Kalshi) made by Jasper Buffet, Mark Burry and Duco Munger.

## Features

- Real-time market data from Polymarket and Kalshi
- Fuzzy text matching to find equivalent markets across platforms
- Automatic arbitrage opportunity detection (2%+ profit threshold)
- Discord webhook notifications
- Price validation and liquidity filtering

## Setup

1. Install dependencies:
```bash
cd arbitrage_bot
pip install -r requirements.txt
```

2. Configure credentials in `.env`:
```bash
KALSHI_API_KEY_ID=your_api_key_id
KALSHI_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
```

3. Adjust settings in `config.yaml`:
```yaml
arbitrage:
  min_profit_pct: 2.0      # Minimum 2% profit to report
  min_liquidity: 500       # Minimum $500 liquidity
  check_interval: 30       # Check every 30 seconds

matching:
  min_confidence: 0.65     # 65% similarity threshold
```

## Usage

### Test with Mock Data
See a guaranteed 27% arbitrage opportunity:
```bash
python test_bot.py --mock
```

### Test with Real APIs
Fetch live markets and check for opportunities:
```bash
python test_bot.py
```

### Run Continuous Monitoring
Check for opportunities every 30 seconds:
```bash
python -m src.main --continuous
```

Or run once:
```bash
python -m src.main --once
```

## How It Works

1. **Fetch Markets**: Retrieves active markets from Polymarket and Kalshi
2. **Match Markets**: Uses fuzzy text matching to find equivalent markets
3. **Calculate Arbitrage**: Checks if buying YES on one platform + NO on another guarantees profit
4. **Notify**: Sends Discord notification when opportunities are found

### Example Arbitrage

If the same event has different prices on each platform:

- **Polymarket**: YES = $0.35, NO = $0.65
- **Kalshi**: YES = $0.62, NO = $0.38

**Strategy**: Buy YES on Polymarket ($0.35) + Buy NO on Kalshi ($0.38)
- **Cost**: $0.73
- **Payout**: $1.00 (guaranteed)
- **Profit**: $0.27 (27%)

No matter the outcome, one position pays $1.00!

## Project Structure

```
arbitrage_bot/
├── config.yaml              # Configuration settings
├── .env                     # API credentials (not in git)
├── test_bot.py             # Testing script
├── src/
│   ├── main.py             # Entry point
│   ├── api/
│   │   ├── polymarket.py   # Polymarket API client
│   │   └── kalshi.py       # Kalshi API client (JWT auth)
│   ├── matching/
│   │   ├── semantic_matcher.py  # Market matching logic
│   │   └── normalizer.py        # Text normalization
│   ├── arbitrage/
│   │   ├── detector.py     # Orchestrates detection
│   │   └── calculator.py   # Arbitrage math
│   └── utils/
│       ├── config.py       # Config loader
│       ├── logger.py       # Logging
│       └── notifier.py     # Discord notifications
```

## Current Status

The bot is **fully functional** but currently finds 0 opportunities because:
- Polymarket focuses on politics, economics, crypto
- Kalshi currently only has sports betting markets
- No overlap = no arbitrage opportunities

The bot will automatically detect opportunities when the platforms offer the same events.

## Security

- `.env` file is in `.gitignore` (never commit credentials!)
- API keys stored as environment variables
- RSA private key authentication for Kalshi
