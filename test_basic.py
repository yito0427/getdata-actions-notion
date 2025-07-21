#!/usr/bin/env python3
"""
Basic test script to verify the data collection works
Run with: python test_basic.py
"""

import asyncio
import json
from datetime import datetime
import ccxt

async def test_basic_collection():
    """Test basic data collection from Binance"""
    print("Testing basic data collection...")
    
    # Create exchange instance
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'rateLimit': 1200,
    })
    
    try:
        # Load markets
        print("Loading markets...")
        await exchange.load_markets()
        print(f"Loaded {len(exchange.markets)} markets")
        
        # Test ticker fetch
        symbol = 'BTC/USDT'
        print(f"\nFetching ticker for {symbol}...")
        ticker = await exchange.fetch_ticker(symbol)
        print(f"Price: ${ticker['last']:,.2f}")
        print(f"24h Volume: {ticker['baseVolume']:,.2f} BTC")
        print(f"24h Change: {ticker['percentage']:.2f}%")
        
        # Test orderbook fetch
        print(f"\nFetching orderbook for {symbol}...")
        orderbook = await exchange.fetch_order_book(symbol, limit=5)
        print(f"Best bid: ${orderbook['bids'][0][0]:,.2f}")
        print(f"Best ask: ${orderbook['asks'][0][0]:,.2f}")
        spread = orderbook['asks'][0][0] - orderbook['bids'][0][0]
        print(f"Spread: ${spread:.2f}")
        
        # Save sample data
        sample_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "exchange": "binance",
            "symbol": symbol,
            "ticker": {
                "last": ticker['last'],
                "volume": ticker['baseVolume'],
                "change_24h": ticker['percentage']
            },
            "orderbook": {
                "best_bid": orderbook['bids'][0][0],
                "best_ask": orderbook['asks'][0][0],
                "spread": spread
            }
        }
        
        with open("sample_output.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        
        print("\n✅ Basic test successful!")
        print("Sample data saved to: sample_output.json")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
    finally:
        await exchange.close()

if __name__ == "__main__":
    asyncio.run(test_basic_collection())