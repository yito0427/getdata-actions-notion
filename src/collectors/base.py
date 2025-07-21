"""
Base collector class for cryptocurrency exchanges
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import ccxt.async_support as ccxt
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from ..models import (
    TickerData, OrderBookData, TradeData, 
    OHLCVData, ExchangeStatus, MarketInfo, 
    ExchangeInfo, CollectedData
)
from ..config import Config


class BaseCollector(ABC):
    """Base class for exchange data collectors"""
    
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.exchange: Optional[ccxt.Exchange] = None
        self.config = Config.get_exchange_config(exchange_name)
        self.symbols = Config.get_symbols()
        self.collected_data = CollectedData(
            exchange=exchange_name,
            collection_timestamp=datetime.utcnow()
        )
        
    async def initialize(self):
        """Initialize exchange connection"""
        try:
            # Get exchange class dynamically
            exchange_class = getattr(ccxt, self.exchange_name)
            self.exchange = exchange_class({
                'enableRateLimit': True,
                'rateLimit': self.config.get('rate_limit', 100),
                'timeout': 30000,  # 30 seconds
            })
            
            # Load markets
            await self.exchange.load_markets()
            logger.info(f"Initialized {self.exchange_name} with {len(self.exchange.markets)} markets")
            
            # Store exchange info
            self.collected_data.exchange_info = self._get_exchange_info()
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_name}: {e}")
            self.collected_data.errors.append({
                "type": "initialization",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            raise
    
    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            
    def _get_exchange_info(self) -> ExchangeInfo:
        """Get exchange information"""
        return ExchangeInfo(
            name=self.exchange_name,
            countries=getattr(self.exchange, 'countries', []),
            urls=getattr(self.exchange, 'urls', {}),
            has={
                'fetchTicker': self.exchange.has.get('fetchTicker', False),
                'fetchTickers': self.exchange.has.get('fetchTickers', False),
                'fetchOrderBook': self.exchange.has.get('fetchOrderBook', False),
                'fetchTrades': self.exchange.has.get('fetchTrades', False),
                'fetchOHLCV': self.exchange.has.get('fetchOHLCV', False),
            },
            timeframes=getattr(self.exchange, 'timeframes', {}),
            rate_limit=getattr(self.exchange, 'rateLimit', None)
        )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_ticker(self, symbol: str) -> Optional[TickerData]:
        """Fetch ticker data for a symbol"""
        try:
            if not self.exchange.has['fetchTicker']:
                return None
                
            ticker = await self.exchange.fetch_ticker(symbol)
            
            return TickerData(
                exchange=self.exchange_name,
                symbol=symbol,
                timestamp=datetime.utcnow(),
                last=ticker.get('last'),
                bid=ticker.get('bid'),
                ask=ticker.get('ask'),
                high=ticker.get('high'),
                low=ticker.get('low'),
                open=ticker.get('open'),
                close=ticker.get('close'),
                base_volume=ticker.get('baseVolume'),
                quote_volume=ticker.get('quoteVolume'),
                percentage=ticker.get('percentage'),
                change=ticker.get('change'),
                vwap=ticker.get('vwap'),
                bid_volume=ticker.get('bidVolume'),
                ask_volume=ticker.get('askVolume')
            )
            
        except Exception as e:
            logger.warning(f"Failed to fetch ticker for {symbol} on {self.exchange_name}: {e}")
            self.collected_data.errors.append({
                "type": "ticker",
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_orderbook(self, symbol: str, limit: int = 20) -> Optional[OrderBookData]:
        """Fetch orderbook data for a symbol"""
        try:
            if not self.exchange.has['fetchOrderBook']:
                return None
                
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            
            # Calculate spread
            best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
            best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0
            spread = best_ask - best_bid if best_bid and best_ask else None
            spread_percentage = (spread / best_ask * 100) if spread and best_ask else None
            
            # Calculate depth
            bid_depth = sum(order[1] for order in orderbook['bids'])
            ask_depth = sum(order[1] for order in orderbook['asks'])
            
            return OrderBookData(
                exchange=self.exchange_name,
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bids=orderbook['bids'][:limit],
                asks=orderbook['asks'][:limit],
                spread=spread,
                spread_percentage=spread_percentage,
                bid_depth=bid_depth,
                ask_depth=ask_depth
            )
            
        except Exception as e:
            logger.warning(f"Failed to fetch orderbook for {symbol} on {self.exchange_name}: {e}")
            self.collected_data.errors.append({
                "type": "orderbook",
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_trades(self, symbol: str, limit: int = 50) -> List[TradeData]:
        """Fetch recent trades for a symbol"""
        trades_list = []
        try:
            if not self.exchange.has['fetchTrades']:
                return trades_list
                
            trades = await self.exchange.fetch_trades(symbol, limit=limit)
            
            for trade in trades:
                trades_list.append(TradeData(
                    exchange=self.exchange_name,
                    symbol=symbol,
                    timestamp=datetime.fromtimestamp(trade['timestamp'] / 1000),
                    trade_id=trade.get('id'),
                    price=trade['price'],
                    amount=trade['amount'],
                    cost=trade.get('cost'),
                    side=trade.get('side'),
                    taker_or_maker=trade.get('takerOrMaker')
                ))
                
        except Exception as e:
            logger.warning(f"Failed to fetch trades for {symbol} on {self.exchange_name}: {e}")
            self.collected_data.errors.append({
                "type": "trades",
                "symbol": symbol,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return trades_list
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[OHLCVData]:
        """Fetch OHLCV data for a symbol"""
        ohlcv_list = []
        try:
            if not self.exchange.has['fetchOHLCV']:
                return ohlcv_list
                
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            for candle in ohlcv:
                ohlcv_list.append(OHLCVData(
                    exchange=self.exchange_name,
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=datetime.fromtimestamp(candle[0] / 1000),
                    open=candle[1],
                    high=candle[2],
                    low=candle[3],
                    close=candle[4],
                    volume=candle[5]
                ))
                
        except Exception as e:
            logger.warning(f"Failed to fetch OHLCV for {symbol} on {self.exchange_name}: {e}")
            self.collected_data.errors.append({
                "type": "ohlcv",
                "symbol": symbol,
                "timeframe": timeframe,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        return ohlcv_list
    
    async def fetch_exchange_status(self) -> Optional[ExchangeStatus]:
        """Fetch exchange status"""
        try:
            if hasattr(self.exchange, 'fetch_status'):
                status = await self.exchange.fetch_status()
                return ExchangeStatus(
                    exchange=self.exchange_name,
                    timestamp=datetime.utcnow(),
                    status=status.get('status', 'unknown'),
                    updated=datetime.fromtimestamp(status['updated'] / 1000) if status.get('updated') else None,
                    eta=datetime.fromtimestamp(status['eta'] / 1000) if status.get('eta') else None,
                    url=status.get('url')
                )
        except Exception as e:
            logger.warning(f"Failed to fetch status for {self.exchange_name}: {e}")
            
        return None
    
    def _filter_valid_symbols(self, symbols: List[str]) -> List[str]:
        """Filter symbols that are valid for this exchange"""
        valid_symbols = []
        for symbol in symbols:
            if symbol in self.exchange.markets:
                valid_symbols.append(symbol)
            else:
                # Try alternative formats
                alternatives = [
                    symbol.replace('/', ''),  # BTCUSDT
                    symbol.replace('/', '-'),  # BTC-USDT
                    symbol.replace('/', '_'),  # BTC_USDT
                ]
                for alt in alternatives:
                    if alt in self.exchange.markets:
                        valid_symbols.append(alt)
                        break
                        
        return valid_symbols
    
    async def collect_all_data(self) -> CollectedData:
        """Collect all available data from the exchange"""
        try:
            # Initialize if not already done
            if not self.exchange:
                await self.initialize()
                
            # Filter valid symbols
            valid_symbols = self._filter_valid_symbols(self.symbols)
            
            if not valid_symbols:
                logger.warning(f"No valid symbols found for {self.exchange_name}")
                self.collected_data.warnings.append(f"No valid symbols found from: {self.symbols}")
                return self.collected_data
                
            logger.info(f"Collecting data for {len(valid_symbols)} symbols on {self.exchange_name}")
            
            # Collect exchange status
            if Config.COLLECT_EXCHANGE_STATUS:
                status = await self.fetch_exchange_status()
                if status:
                    self.collected_data.exchange_status = status
            
            # Collect data for each symbol
            tasks = []
            for symbol in valid_symbols:
                if Config.COLLECT_TICKER:
                    tasks.append(self._collect_ticker(symbol))
                if Config.COLLECT_ORDERBOOK:
                    tasks.append(self._collect_orderbook(symbol))
                if Config.COLLECT_TRADES:
                    tasks.append(self._collect_trades(symbol))
                if Config.COLLECT_OHLCV:
                    for timeframe in Config.OHLCV_TIMEFRAMES:
                        if timeframe in self.exchange.timeframes:
                            tasks.append(self._collect_ohlcv(symbol, timeframe))
                            
            # Execute all tasks concurrently
            await asyncio.gather(*tasks)
            
            logger.info(f"Completed data collection for {self.exchange_name}: "
                       f"{len(self.collected_data.tickers)} tickers, "
                       f"{len(self.collected_data.orderbooks)} orderbooks, "
                       f"{len(self.collected_data.trades)} trades, "
                       f"{len(self.collected_data.ohlcv)} OHLCV")
            
        except Exception as e:
            logger.error(f"Failed to collect data from {self.exchange_name}: {e}")
            self.collected_data.errors.append({
                "type": "general",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        finally:
            await self.close()
            
        return self.collected_data
    
    async def _collect_ticker(self, symbol: str):
        """Helper to collect ticker data"""
        ticker = await self.fetch_ticker(symbol)
        if ticker:
            self.collected_data.tickers.append(ticker)
            
    async def _collect_orderbook(self, symbol: str):
        """Helper to collect orderbook data"""
        orderbook = await self.fetch_orderbook(
            symbol, 
            limit=self.config.get('orderbook_limit', 20)
        )
        if orderbook:
            self.collected_data.orderbooks.append(orderbook)
            
    async def _collect_trades(self, symbol: str):
        """Helper to collect trades data"""
        trades = await self.fetch_trades(symbol)
        self.collected_data.trades.extend(trades)
        
    async def _collect_ohlcv(self, symbol: str, timeframe: str):
        """Helper to collect OHLCV data"""
        ohlcv = await self.fetch_ohlcv(symbol, timeframe)
        self.collected_data.ohlcv.extend(ohlcv)