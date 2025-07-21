"""
CSV writer for cryptocurrency data
日別・取引所別・情報別にCSVファイルを保存
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from loguru import logger

from ..models import CollectedData, TickerData, OrderBookData, TradeData, OHLCVData


class CSVWriter:
    """CSV形式でデータを保存するクラス"""
    
    def __init__(self, base_dir: str = "data"):
        """
        Initialize CSV writer
        
        Args:
            base_dir: Base directory for CSV files
        """
        self.base_dir = Path(base_dir)
        self.date_str = datetime.utcnow().strftime("%Y%m%d")
        
    def save_collected_data(self, data: CollectedData) -> Dict[str, str]:
        """
        Save collected data to CSV files
        
        Returns:
            Dictionary of saved file paths
        """
        saved_files = {}
        
        # Create directory structure: data/YYYYMMDD/exchange_name/
        exchange_dir = self.base_dir / self.date_str / data.exchange
        exchange_dir.mkdir(parents=True, exist_ok=True)
        
        # Save tickers
        if data.tickers:
            ticker_file = self._save_tickers(data.tickers, exchange_dir)
            saved_files['tickers'] = str(ticker_file)
            
        # Save orderbooks
        if data.orderbooks:
            orderbook_file = self._save_orderbooks(data.orderbooks, exchange_dir)
            saved_files['orderbooks'] = str(orderbook_file)
            
        # Save trades
        if data.trades:
            trades_file = self._save_trades(data.trades, exchange_dir)
            saved_files['trades'] = str(trades_file)
            
        # Save OHLCV
        if data.ohlcv:
            ohlcv_file = self._save_ohlcv(data.ohlcv, exchange_dir)
            saved_files['ohlcv'] = str(ohlcv_file)
            
        # Save summary
        summary_file = self._save_summary(data, exchange_dir)
        saved_files['summary'] = str(summary_file)
        
        logger.info(f"Saved {len(saved_files)} CSV files for {data.exchange}")
        return saved_files
    
    def _save_tickers(self, tickers: List[TickerData], exchange_dir: Path) -> Path:
        """Save ticker data to CSV"""
        timestamp = datetime.utcnow().strftime("%H%M%S")
        filename = f"{self.date_str}_{exchange_dir.name}_tickers_{timestamp}.csv"
        filepath = exchange_dir / filename
        
        # Convert to DataFrame
        df_data = []
        for ticker in tickers:
            df_data.append({
                'timestamp': ticker.timestamp.isoformat(),
                'symbol': ticker.symbol,
                'last': ticker.last,
                'bid': ticker.bid,
                'ask': ticker.ask,
                'high_24h': ticker.high,
                'low_24h': ticker.low,
                'open_24h': ticker.open,
                'volume_base': ticker.base_volume,
                'volume_quote': ticker.quote_volume,
                'change_percent': ticker.percentage,
                'change_amount': ticker.change,
                'vwap': ticker.vwap,
                'spread': ticker.ask - ticker.bid if ticker.ask and ticker.bid else None,
                'spread_percent': ((ticker.ask - ticker.bid) / ticker.ask * 100) if ticker.ask and ticker.bid else None
            })
            
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Saved {len(tickers)} tickers to {filepath}")
        return filepath
    
    def _save_orderbooks(self, orderbooks: List[OrderBookData], exchange_dir: Path) -> Path:
        """Save orderbook data to CSV"""
        timestamp = datetime.utcnow().strftime("%H%M%S")
        filename = f"{self.date_str}_{exchange_dir.name}_orderbooks_{timestamp}.csv"
        filepath = exchange_dir / filename
        
        # Convert to DataFrame
        df_data = []
        for ob in orderbooks:
            best_bid = ob.bids[0][0] if ob.bids else None
            best_ask = ob.asks[0][0] if ob.asks else None
            
            df_data.append({
                'timestamp': ob.timestamp.isoformat(),
                'symbol': ob.symbol,
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': ob.spread,
                'spread_percent': ob.spread_percentage,
                'bid_depth': ob.bid_depth,
                'ask_depth': ob.ask_depth,
                'bid_count': len(ob.bids),
                'ask_count': len(ob.asks),
                'mid_price': (best_bid + best_ask) / 2 if best_bid and best_ask else None,
                'imbalance': ob.bid_depth / ob.ask_depth if ob.ask_depth else None,
                # Top 5 levels
                'bid_1_price': ob.bids[0][0] if len(ob.bids) > 0 else None,
                'bid_1_size': ob.bids[0][1] if len(ob.bids) > 0 else None,
                'bid_2_price': ob.bids[1][0] if len(ob.bids) > 1 else None,
                'bid_2_size': ob.bids[1][1] if len(ob.bids) > 1 else None,
                'bid_3_price': ob.bids[2][0] if len(ob.bids) > 2 else None,
                'bid_3_size': ob.bids[2][1] if len(ob.bids) > 2 else None,
                'ask_1_price': ob.asks[0][0] if len(ob.asks) > 0 else None,
                'ask_1_size': ob.asks[0][1] if len(ob.asks) > 0 else None,
                'ask_2_price': ob.asks[1][0] if len(ob.asks) > 1 else None,
                'ask_2_size': ob.asks[1][1] if len(ob.asks) > 1 else None,
                'ask_3_price': ob.asks[2][0] if len(ob.asks) > 2 else None,
                'ask_3_size': ob.asks[2][1] if len(ob.asks) > 2 else None,
            })
            
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Saved {len(orderbooks)} orderbooks to {filepath}")
        return filepath
    
    def _save_trades(self, trades: List[TradeData], exchange_dir: Path) -> Path:
        """Save trade data to CSV"""
        timestamp = datetime.utcnow().strftime("%H%M%S")
        filename = f"{self.date_str}_{exchange_dir.name}_trades_{timestamp}.csv"
        filepath = exchange_dir / filename
        
        # Convert to DataFrame
        df_data = []
        for trade in trades:
            df_data.append({
                'timestamp': trade.timestamp.isoformat(),
                'symbol': trade.symbol,
                'trade_id': trade.trade_id,
                'price': trade.price,
                'amount': trade.amount,
                'cost': trade.cost,
                'side': trade.side,
                'taker_or_maker': trade.taker_or_maker
            })
            
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Saved {len(trades)} trades to {filepath}")
        return filepath
    
    def _save_ohlcv(self, ohlcv_data: List[OHLCVData], exchange_dir: Path) -> Path:
        """Save OHLCV data to CSV"""
        timestamp = datetime.utcnow().strftime("%H%M%S")
        filename = f"{self.date_str}_{exchange_dir.name}_ohlcv_{timestamp}.csv"
        filepath = exchange_dir / filename
        
        # Convert to DataFrame
        df_data = []
        for candle in ohlcv_data:
            df_data.append({
                'timestamp': candle.timestamp.isoformat(),
                'symbol': candle.symbol,
                'timeframe': candle.timeframe,
                'open': candle.open,
                'high': candle.high,
                'low': candle.low,
                'close': candle.close,
                'volume': candle.volume
            })
            
        df = pd.DataFrame(df_data)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Saved {len(ohlcv_data)} OHLCV records to {filepath}")
        return filepath
    
    def _save_summary(self, data: CollectedData, exchange_dir: Path) -> Path:
        """Save collection summary to CSV"""
        timestamp = datetime.utcnow().strftime("%H%M%S")
        filename = f"{self.date_str}_{exchange_dir.name}_summary_{timestamp}.csv"
        filepath = exchange_dir / filename
        
        # Create summary data
        summary = {
            'collection_timestamp': data.collection_timestamp.isoformat(),
            'exchange': data.exchange,
            'ticker_count': len(data.tickers),
            'orderbook_count': len(data.orderbooks),
            'trade_count': len(data.trades),
            'ohlcv_count': len(data.ohlcv),
            'error_count': len(data.errors),
            'warning_count': len(data.warnings),
            'status': data.exchange_status.status if data.exchange_status else 'unknown',
            'markets_count': len(data.markets) if data.markets else 0,
        }
        
        # Add error details if any
        if data.errors:
            summary['error_types'] = ', '.join([e.get('type', 'unknown') for e in data.errors[:5]])
            
        # Save as single row CSV
        df = pd.DataFrame([summary])
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        logger.info(f"Saved summary to {filepath}")
        return filepath
    
    def create_daily_summary(self, all_results: Dict[str, CollectedData]) -> Path:
        """Create a daily summary CSV combining all exchanges"""
        summary_dir = self.base_dir / self.date_str
        summary_file = summary_dir / f"{self.date_str}_all_exchanges_summary.csv"
        
        summary_data = []
        for exchange_name, data in all_results.items():
            summary_data.append({
                'date': self.date_str,
                'exchange': exchange_name,
                'collection_time': data.collection_timestamp.isoformat(),
                'ticker_count': len(data.tickers),
                'orderbook_count': len(data.orderbooks),
                'trade_count': len(data.trades),
                'ohlcv_count': len(data.ohlcv),
                'error_count': len(data.errors),
                'status': 'success' if len(data.errors) == 0 else 'partial_failure',
                'unique_symbols': len(set(t.symbol for t in data.tickers))
            })
            
        df = pd.DataFrame(summary_data)
        df.to_csv(summary_file, index=False, encoding='utf-8-sig')
        
        logger.info(f"Created daily summary: {summary_file}")
        return summary_file