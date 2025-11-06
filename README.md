# Arbitrage Detection Bot

Automatische detectie van arbitrage kansen tussen Polymarket en Kalshi prediction markets.

## Installatie

```bash
pip install -r requirements.txt
```

## Configuratie

1. Kopieer `.env.example` naar `.env`:
```bash
cp .env.example .env
```

2. Vul optionele credentials in `.env`:
```
KALSHI_EMAIL=your_email
KALSHI_PASSWORD=your_password
DISCORD_WEBHOOK=your_webhook_url
```

3. Pas `config.yaml` aan naar wens (min profit, liquidity thresholds, etc.)

## Gebruik

### Eenmalige scan
```bash
python -m src.main --once
```

### Continue monitoring
```bash
python -m src.main --continuous
```

### Custom check interval
```bash
python -m src.main --continuous --interval 60
```

## Hoe het werkt

1. **API Clients**: Haalt markets op van Polymarket en Kalshi
2. **Text Normalization**: Normaliseert market vragen voor matching
3. **Semantic Matching**: Matcht vergelijkbare markets met fuzzy + semantic similarity
4. **Arbitrage Calculation**: Berekent of combined probabilities < 100% zijn
5. **Alert**: Logt gevonden opportunities

## Project Structuur

```
arbitrage_bot/
├── src/
│   ├── api/              # API clients
│   ├── matching/         # Market matching logic
│   ├── arbitrage/        # Arbitrage calculation
│   ├── utils/            # Config & logging
│   └── main.py          # Entry point
├── tests/               # Tests
├── config.yaml          # Configuration
└── requirements.txt     # Dependencies
```

## Testing

Test API clients:
```bash
python tests/test_api_clients.py
```

## Notes

- Demo API wordt gebruikt voor Kalshi (geen authenticatie nodig)
- Semantic matching gebruikt sentence-transformers model
- Minimum profit threshold voorkomt false positives
- Caching voorkomt rate limiting

