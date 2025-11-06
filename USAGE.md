# Arbitrage Bot Usage Guide

## Quick Start

### 1. Installatie
```bash
cd arbitrage_bot
pip install -r requirements.txt
```

### 2. Configuratie
```bash
cp .env.example .env
```

Pas `config.yaml` aan indien nodig:
- `min_profit_pct`: Minimum profit percentage (default: 2.0%)
- `min_liquidity`: Minimum market liquidity (default: $100)
- `min_confidence`: Minimum match confidence (default: 0.8)
- `check_interval`: Seconds between checks (default: 30)

### 3. Gebruik

**Eenmalige scan:**
```bash
python3 -m src.main --once
```

**Continue monitoring:**
```bash
python3 -m src.main --continuous
```

**Met custom interval (60 seconden):**
```bash
python3 -m src.main --continuous --interval 60
```

## Testing

### Test API Clients
Test of beide APIs bereikbaar zijn:
```bash
python3 tests/test_api_clients.py
```

Output: Sample markets van beide platforms

### Test Arbitrage Logic
Test de arbitrage calculatie met mock data:
```bash
python3 tests/test_arbitrage_logic.py
```

Output: 5/5 tests passed

### Test Full Simulation
Run complete simulation met mock markets:
```bash
python3 tests/test_full_simulation.py
```

Output: Complete arbitrage opportunities met details

### Test Market Matching
Test de matching logic:
```bash
python3 tests/test_matching.py
```

## Output Format

Wanneer arbitrage wordt gevonden:
```
======================================================================
ARBITRAGE OPPORTUNITY FOUND
======================================================================
Match Confidence: 70.8%

POLYMARKET: "Will Trump win the 2024 election?"
  Yes: 0.520 | No: 0.480
  Liquidity: $100,000

KALSHI: "Trump wins 2024 presidential election"
  Yes: 0.450 | No: 0.550
  Liquidity: $80,000

STRATEGY:
  1. Buy No on polymarket (0.480)
  2. Buy Yes on kalshi (0.450)
  If event happens, profit from B. If not, profit from A.

Total Cost: 0.930
Guaranteed Profit: 0.070 (7.00%)
======================================================================
```

## Configuration Details

### API Configuration
```yaml
apis:
  polymarket:
    base_url: "https://gamma-api.polymarket.com"
    timeout: 30
  kalshi:
    base_url: "https://demo-api.kalshi.co"  # Demo API
    timeout: 30
```

Voor production Kalshi API:
- Wijzig base_url naar `https://trading-api.kalshi.com`
- Voeg credentials toe in `.env`:
  ```
  KALSHI_EMAIL=your_email
  KALSHI_PASSWORD=your_password
  ```

### Matching Configuration
```yaml
matching:
  min_confidence: 0.8      # 0.0 - 1.0
  use_semantic: true       # Gebruik semantic embeddings
  semantic_model: "all-MiniLM-L6-v2"
```

### Arbitrage Configuration
```yaml
arbitrage:
  min_profit_pct: 2.0      # Minimum profit percentage
  min_liquidity: 100       # Minimum market liquidity
  check_interval: 30       # Seconds between checks
```

## Troubleshooting

### Semantic model errors
Als je errors ziet over sentence-transformers:
```bash
pip install --upgrade tqdm sentence-transformers
```

Of disable semantic matching in config.yaml:
```yaml
matching:
  use_semantic: false
```

### No matches found
- Verlaag `min_confidence` in config.yaml (bijv. 0.6)
- Check of markets actueel zijn (niet gesloten/expired)
- Demo Kalshi API heeft beperkte markets (sport focus)
- Gebruik production Kalshi API voor betere overlap

### Rate limiting
- Verhoog `check_interval` in config.yaml
- Caching is al geïmplementeerd (10 sec TTL)

## Notes

- Demo mode gebruikt Kalshi demo API (geen auth nodig)
- Semantic matching vereist sentence-transformers model download (eerste keer ~80MB)
- Markets worden gecached om API calls te minimaliseren
- Liquidity check voorkomt illiquide markets
- Date context matching voorkomt false positives tussen verschillende jaren

## Production Checklist

Voor echte trading:
1. Switch naar Kalshi production API
2. Voeg Kalshi credentials toe in `.env`
3. Test grondig met kleine bedragen
4. Monitor voor false positives
5. Overweeg Discord/Telegram notifications
6. Implementeer database voor opportunity tracking
7. Check fees van beide platforms
8. Test execution snelheid (arbitrage kan snel verdwijnen)
