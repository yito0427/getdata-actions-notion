"""
Configuration for cryptocurrency data collection
"""

from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration settings"""
    
    # Notion Configuration
    NOTION_API_KEY = os.getenv("NOTION_API_KEY") or os.getenv("NOTION_API_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "crypto_data_collector.log")
    
    # Data Collection
    MAX_CONCURRENT_EXCHANGES = int(os.getenv("MAX_CONCURRENT_EXCHANGES", "10"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "5"))
    RATE_LIMIT_PER_SECOND = int(os.getenv("RATE_LIMIT_PER_SECOND", "10"))
    
    # Collection Intervals (seconds)
    TICKER_INTERVAL = int(os.getenv("TICKER_INTERVAL", "60"))
    ORDERBOOK_INTERVAL = int(os.getenv("ORDERBOOK_INTERVAL", "300"))
    TRADES_INTERVAL = int(os.getenv("TRADES_INTERVAL", "300"))
    
    # Exchange Configuration
    EXCHANGES = os.getenv("EXCHANGES", "").split(",") if os.getenv("EXCHANGES") else []
    SYMBOLS = os.getenv("SYMBOLS", "").split(",") if os.getenv("SYMBOLS") else []
    
    # Default symbols if not specified
    DEFAULT_SYMBOLS = [
        "BTC/USDT",
        "ETH/USDT",
        "BTC/USD",
        "ETH/USD",
        "BTC/JPY",
        "ETH/JPY",
    ]
    
    # データ収集の優先順位設定
    # 優先度の高い取引所（流動性が高く、安定している）
    PRIORITY_EXCHANGES = [
        "binance",
        "coinbase",
        "kraken",
        "bitfinex",
        "bitstamp",
        "okx",
        "bybit",
        "kucoin",
        "gate",
        "huobi",
        "bitflyer",  # 日本
        "coincheck",  # 日本
        "zaif",  # 日本
        "bitbank",  # 日本
    ]
    
    # 取引所ごとの設定
    EXCHANGE_CONFIGS: Dict[str, Dict[str, Any]] = {
        "binance": {
            "rate_limit": 1200,  # requests per minute
            "has_orderbook": True,
            "has_trades": True,
            "has_ohlcv": True,
            "orderbook_limit": 100,  # 板情報の深度
        },
        "coinbase": {
            "rate_limit": 10,  # requests per second
            "has_orderbook": True,
            "has_trades": True,
            "has_ohlcv": True,
            "orderbook_limit": 50,
        },
        "bitflyer": {
            "rate_limit": 500,  # requests per minute
            "has_orderbook": True,
            "has_trades": True,
            "has_ohlcv": False,
            "orderbook_limit": 20,
        },
        # デフォルト設定
        "default": {
            "rate_limit": 100,
            "has_orderbook": True,
            "has_trades": True,
            "has_ohlcv": True,
            "orderbook_limit": 20,
        }
    }
    
    # 収集するデータタイプ
    COLLECT_TICKER = True
    COLLECT_ORDERBOOK = True
    COLLECT_TRADES = True
    COLLECT_OHLCV = True
    COLLECT_EXCHANGE_STATUS = True
    
    # OHLCV timeframes to collect
    OHLCV_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    @classmethod
    def get_exchange_config(cls, exchange_name: str) -> Dict[str, Any]:
        """Get configuration for specific exchange"""
        return cls.EXCHANGE_CONFIGS.get(
            exchange_name, 
            cls.EXCHANGE_CONFIGS["default"]
        )
    
    @classmethod
    def get_symbols(cls) -> List[str]:
        """Get symbols to collect"""
        return cls.SYMBOLS if cls.SYMBOLS else cls.DEFAULT_SYMBOLS
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        if not cls.NOTION_API_KEY:
            raise ValueError("NOTION_API_KEY is required")
        if not cls.NOTION_DATABASE_ID:
            raise ValueError("NOTION_DATABASE_ID is required")
        return True