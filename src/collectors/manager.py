"""
Manager for coordinating data collection from multiple exchanges
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
import ccxt
from loguru import logger

from .base import BaseCollector
from ..models import CollectedData
from ..config import Config


class ExchangeCollectorManager:
    """Manages data collection from multiple exchanges"""
    
    def __init__(self, exchanges: Optional[List[str]] = None):
        """
        Initialize the manager
        
        Args:
            exchanges: List of exchange names to collect from. 
                      If None, will use all available exchanges.
        """
        self.exchanges = exchanges or self._get_available_exchanges()
        self.collectors: List[BaseCollector] = []
        self.results: Dict[str, CollectedData] = {}
        
    def _get_available_exchanges(self) -> List[str]:
        """Get list of all available exchanges from ccxt"""
        # Get all ccxt exchanges
        all_exchanges = ccxt.exchanges
        
        # Filter based on priority if configured
        if Config.PRIORITY_EXCHANGES:
            # Start with priority exchanges that are available
            priority = [ex for ex in Config.PRIORITY_EXCHANGES if ex in all_exchanges]
            # Add remaining exchanges
            remaining = [ex for ex in all_exchanges if ex not in priority]
            return priority + remaining
        
        return all_exchanges
    
    async def collect_from_exchange(self, exchange_name: str) -> Optional[CollectedData]:
        """Collect data from a single exchange"""
        try:
            logger.info(f"Starting collection from {exchange_name}")
            collector = BaseCollector(exchange_name)
            result = await collector.collect_all_data()
            return result
            
        except Exception as e:
            logger.error(f"Failed to collect from {exchange_name}: {e}")
            # Return empty result with error
            return CollectedData(
                exchange=exchange_name,
                collection_timestamp=datetime.utcnow(),
                errors=[{
                    "type": "collection_failed",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }]
            )
    
    async def collect_all(self, max_concurrent: Optional[int] = None) -> Dict[str, CollectedData]:
        """
        Collect data from all configured exchanges
        
        Args:
            max_concurrent: Maximum number of concurrent connections
            
        Returns:
            Dictionary mapping exchange names to collected data
        """
        max_concurrent = max_concurrent or Config.MAX_CONCURRENT_EXCHANGES
        
        logger.info(f"Starting data collection from {len(self.exchanges)} exchanges "
                   f"with max {max_concurrent} concurrent connections")
        
        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def collect_with_semaphore(exchange: str):
            async with semaphore:
                return exchange, await self.collect_from_exchange(exchange)
        
        # Collect from all exchanges concurrently
        tasks = [collect_with_semaphore(exchange) for exchange in self.exchanges]
        results = await asyncio.gather(*tasks)
        
        # Store results
        for exchange_name, data in results:
            if data:
                self.results[exchange_name] = data
                
        # Log summary
        successful = sum(1 for data in self.results.values() if not data.errors)
        failed = len(self.results) - successful
        
        logger.info(f"Collection completed: {successful} successful, {failed} failed")
        
        return self.results
    
    async def collect_from_priority_exchanges(self, limit: int = 10) -> Dict[str, CollectedData]:
        """Collect data from priority exchanges only"""
        priority_exchanges = Config.PRIORITY_EXCHANGES[:limit]
        
        # Filter to only available exchanges
        available_priority = [ex for ex in priority_exchanges if ex in ccxt.exchanges]
        
        logger.info(f"Collecting from {len(available_priority)} priority exchanges")
        
        # Create temporary instance with limited exchanges
        temp_manager = ExchangeCollectorManager(available_priority)
        return await temp_manager.collect_all()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of collection results"""
        total_tickers = 0
        total_orderbooks = 0
        total_trades = 0
        total_ohlcv = 0
        total_errors = 0
        
        for data in self.results.values():
            total_tickers += len(data.tickers)
            total_orderbooks += len(data.orderbooks)
            total_trades += len(data.trades)
            total_ohlcv += len(data.ohlcv)
            total_errors += len(data.errors)
            
        return {
            "exchanges_collected": len(self.results),
            "total_tickers": total_tickers,
            "total_orderbooks": total_orderbooks,
            "total_trades": total_trades,
            "total_ohlcv": total_ohlcv,
            "total_errors": total_errors,
            "collection_timestamp": datetime.utcnow().isoformat()
        }
    
    def get_errors_summary(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get summary of all errors by exchange"""
        errors_by_exchange = {}
        
        for exchange_name, data in self.results.items():
            if data.errors:
                errors_by_exchange[exchange_name] = data.errors
                
        return errors_by_exchange