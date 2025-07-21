# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**getdata-actions-notion** is a cryptocurrency data collection system that uses public APIs (no authentication required) to gather market data from 102+ exchanges and stores it in Notion via GitHub Actions.

## Project Purpose

このリポジトリは、認証不要の公開APIを使用して102の仮想通貨取引所から最大限のデータを収集し、GitHub Actions経由で定期的にNotionデータベースに保存するシステムです。

## Current Implementation

- ✅ CCXT library integration for 102+ exchanges
- ✅ Async data collection with rate limiting
- ✅ Error handling and retry mechanisms
- ✅ Multi-exchange concurrent processing
- ✅ Data models for ticker, orderbook, trades, OHLCV
- 🚧 Notion API integration (pending)
- 🚧 GitHub Actions workflow (pending)

## Architecture

```
getdata-actions-notion/
├── .github/
│   └── workflows/               # GitHub Actions (to be implemented)
├── src/
│   ├── collectors/
│   │   ├── base.py            # Base collector class with CCXT integration
│   │   └── manager.py         # Multi-exchange concurrent manager
│   ├── notion/                # Notion API integration (to be implemented)
│   ├── models.py              # Pydantic models for all data types
│   ├── config.py              # Configuration management
│   └── main.py                # Entry point with CLI interface
├── tests/                     # Test suite (to be implemented)
├── pyproject.toml             # Poetry dependencies
├── Makefile                   # Development automation
├── .env.example               # Environment template (NEVER commit .env!)
└── .gitignore                 # Strict security rules
```

## Development Setup

```bash
# Install dependencies with Poetry
poetry install

# Setup environment variables
cp .env.example .env
# Edit .env to add your Notion API credentials

# Run in test mode (no Notion required)
poetry run python -m src.main --test
```

## Common Development Commands

```bash
# Test data collection from 2 exchanges
poetry run python -m src.main --test

# Collect from specific exchanges
poetry run python -m src.main --test --exchanges binance,kraken,bitflyer

# Run with priority exchanges (requires Notion)
poetry run python -m src.main --priority-only

# Format code
make format

# Run linters
make lint

# Run tests
make test
```

## Key Implementation Details

### Data Collection Architecture
- **BaseCollector**: Abstract base class using CCXT for all exchange interactions
- **ExchangeCollectorManager**: Handles concurrent collection from multiple exchanges
- **Rate Limiting**: Built-in rate limiting per exchange with configurable limits
- **Error Handling**: Retry mechanism with exponential backoff using tenacity
- **Async Processing**: Full async/await implementation for maximum performance

### Data Models (Pydantic)
- `TickerData`: Price, volume, 24h stats
- `OrderBookData`: Bids, asks, spread, depth
- `TradeData`: Recent trades with price/amount
- `OHLCVData`: Candlestick data for multiple timeframes
- `ExchangeStatus`: Exchange operational status
- `CollectedData`: Container for all collected data

### Configuration
- Environment-based configuration via python-dotenv
- Exchange-specific settings (rate limits, capabilities)
- Configurable collection intervals and data types
- Priority exchange list for optimized collection

## Security Considerations

- **NEVER** commit `.env` files
- Store Notion API keys in environment variables only
- Use GitHub Secrets for production deployment
- Comprehensive `.gitignore` to prevent accidental commits

## Testing Strategy

```bash
# Test without Notion (safe for development)
poetry run python -m src.main --test

# Test specific functionality
poetry run python -m src.main --test --exchanges binance --limit 1

# Check output in ./output directory
ls -la output/
```

## Important Notes

- CCXT library chosen over pybotters for 102+ exchange support
- Async implementation allows concurrent data collection
- Rate limiting prevents API bans
- Error handling ensures partial failures don't stop collection
- Modular design allows easy addition of new data types