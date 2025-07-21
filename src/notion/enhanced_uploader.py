"""
Enhanced Notion uploader that stores actual cryptocurrency data
実際の仮想通貨データを保存する拡張Notionアップローダー
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from notion_client import AsyncClient
from loguru import logger

from ..models import CollectedData, TickerData, OrderBookData, TradeData
from ..config import Config


class EnhancedNotionUploader:
    """拡張版Notionアップローダー - 実データをJSON形式で保存"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.client = AsyncClient(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID
        
    async def upload_ticker_data(self, tickers: List[TickerData]) -> int:
        """Upload ticker data with full details to Notion database"""
        successful_uploads = 0
        
        for ticker in tickers:
            try:
                # Create properties with actual data
                properties = self._create_enhanced_ticker_properties(ticker)
                
                # Create page in database
                await self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                
                successful_uploads += 1
                logger.info(f"Uploaded ticker with full data: {ticker.exchange} {ticker.symbol} Price: ${ticker.last}")
                
                # Rate limiting
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Failed to upload ticker {ticker.exchange} {ticker.symbol}: {e}")
                
        return successful_uploads
    
    def _create_enhanced_ticker_properties(self, ticker: TickerData) -> Dict[str, Any]:
        """Create properties with actual cryptocurrency data"""
        
        # Create a descriptive title with key metrics
        title = f"{ticker.exchange} {ticker.symbol} | ${ticker.last:.2f} | {ticker.percentage:.2f}%" if ticker.last else f"{ticker.exchange} {ticker.symbol}"
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Data Type": {
                "select": {"name": "Ticker Detail"}
            },
            "Exchange": {
                "select": {"name": ticker.exchange}
            },
            "Collection Time": {
                "date": {"start": ticker.timestamp.isoformat()}
            },
            "Record Count": {
                "number": 1
            },
            "Status": {
                "select": {"name": "Success"}
            },
            "Error Count": {
                "number": 0
            }
        }
        
        # Store actual values in available numeric fields
        if ticker.last:
            properties["Avg Volume"] = {"number": ticker.last}  # Repurpose for price
            
        if ticker.percentage:
            properties["Avg Spread %"] = {"number": abs(ticker.percentage) / 100}  # Store change %
        
        # Add raw data as rich text (if the database supports it)
        # This will be stored in the page content
        
        return properties
    
    async def upload_exchange_data(self, data: CollectedData) -> Dict[str, Any]:
        """Upload all data from one exchange with full details"""
        start_time = datetime.now(timezone.utc)
        
        result = {
            "exchange": data.exchange,
            "start_time": start_time.isoformat(),
            "records_uploaded": 0,
            "raw_data_saved": False,
            "status": "pending"
        }
        
        try:
            # Upload individual ticker data
            if data.tickers:
                uploaded = 0
                for ticker in data.tickers:
                    try:
                        properties = self._create_enhanced_ticker_properties(ticker)
                        
                        # Create comprehensive data object for storage
                        ticker_data = {
                            "symbol": ticker.symbol,
                            "exchange": ticker.exchange,
                            "timestamp": ticker.timestamp.isoformat(),
                            "price": {
                                "last": ticker.last,
                                "bid": ticker.bid,
                                "ask": ticker.ask,
                                "high": ticker.high,
                                "low": ticker.low,
                                "open": ticker.open,
                                "close": ticker.close,
                                "vwap": ticker.vwap
                            },
                            "volume": {
                                "base": ticker.base_volume,
                                "quote": ticker.quote_volume,
                                "bid_volume": ticker.bid_volume,
                                "ask_volume": ticker.ask_volume
                            },
                            "change": {
                                "percentage": ticker.percentage,
                                "absolute": ticker.change
                            },
                            "spread": {
                                "value": ticker.ask - ticker.bid if ticker.ask and ticker.bid else None,
                                "percentage": ((ticker.ask - ticker.bid) / ticker.ask * 100) if ticker.ask and ticker.bid else None
                            }
                        }
                        
                        json_data = json.dumps(ticker_data, ensure_ascii=False, indent=2)
                        
                        # Create page with data
                        page = await self.client.pages.create(
                            parent={"database_id": self.database_id},
                            properties=properties,
                            children=[
                                {
                                    "object": "block",
                                    "type": "code",
                                    "code": {
                                        "rich_text": [{
                                            "type": "text",
                                            "text": {"content": json_data}
                                        }],
                                        "language": "json"
                                    }
                                }
                            ]
                        )
                        
                        uploaded += 1
                        await asyncio.sleep(0.3)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Failed to upload ticker: {e}")
                
                result["records_uploaded"] = uploaded
                result["raw_data_saved"] = True
                
            # Create comprehensive summary with all data
            await self._create_comprehensive_summary(data, result["records_uploaded"])
            
            end_time = datetime.now(timezone.utc)
            result["end_time"] = end_time.isoformat()
            result["duration"] = (end_time - start_time).total_seconds()
            result["status"] = "success"
            
            logger.info(f"Successfully uploaded {result['records_uploaded']} records with full data for {data.exchange}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Failed to upload data for {data.exchange}: {e}")
            
        return result
    
    async def _create_comprehensive_summary(self, data: CollectedData, uploaded_count: int):
        """Create a comprehensive summary with all collected data"""
        title = f"📊 {data.exchange} Full Data Export - {data.collection_timestamp.strftime('%Y-%m-%d %H:%M')}"
        
        # Prepare comprehensive data for export
        export_data = {
            "exchange": data.exchange,
            "collection_timestamp": data.collection_timestamp.isoformat(),
            "summary": {
                "total_tickers": len(data.tickers),
                "total_orderbooks": len(data.orderbooks),
                "total_trades": len(data.trades),
                "total_ohlcv": len(data.ohlcv),
                "errors": len(data.errors),
                "uploaded_records": uploaded_count
            },
            "tickers": [
                {
                    "symbol": t.symbol,
                    "last": t.last,
                    "bid": t.bid,
                    "ask": t.ask,
                    "high": t.high,
                    "low": t.low,
                    "volume": t.base_volume,
                    "change_percent": t.percentage,
                    "timestamp": t.timestamp.isoformat()
                }
                for t in data.tickers
            ],
            "orderbooks": [
                {
                    "symbol": ob.symbol,
                    "best_bid": ob.bids[0][0] if ob.bids else None,
                    "best_ask": ob.asks[0][0] if ob.asks else None,
                    "spread": ob.spread,
                    "spread_percent": ob.spread_percentage,
                    "bid_depth": ob.bid_depth,
                    "ask_depth": ob.ask_depth,
                    "timestamp": ob.timestamp.isoformat()
                }
                for ob in data.orderbooks
            ],
            "errors": [
                {
                    "symbol": e.symbol,
                    "data_type": e.data_type,
                    "error": e.error,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in data.errors
            ]
        }
        
        json_export = json.dumps(export_data, ensure_ascii=False, indent=2)
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Data Type": {
                "select": {"name": "Full Export"}
            },
            "Exchange": {
                "select": {"name": data.exchange}
            },
            "Collection Time": {
                "date": {"start": data.collection_timestamp.isoformat()}
            },
            "Record Count": {
                "number": uploaded_count
            },
            "Total Tickers": {
                "number": len(data.tickers)
            },
            "Total OrderBooks": {
                "number": len(data.orderbooks)
            },
            "Total Trades": {
                "number": len(data.trades)
            },
            "Error Count": {
                "number": len(data.errors)
            },
            "Status": {
                "select": {
                    "name": "Success" if len(data.errors) == 0 else "Partial Failure"
                }
            }
        }
        
        # Calculate and add metrics
        if data.tickers:
            # Average price across all symbols
            avg_prices = [t.last for t in data.tickers if t.last]
            if avg_prices:
                properties["Avg Volume"] = {"number": sum(avg_prices) / len(avg_prices)}
            
            # Average volume
            volumes = [t.base_volume for t in data.tickers if t.base_volume]
            if volumes:
                avg_volume = sum(volumes) / len(volumes)
                # Store in a text field or description
                
        try:
            # Create summary page with full JSON export
            await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "📊 Complete Data Export"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "text": {
                                    "content": f"Full cryptocurrency data collected from {data.exchange} at {data.collection_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                                }
                            }]
                        }
                    },
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": json_export[:2000]}  # Notion has limits
                            }],
                            "language": "json"
                        }
                    },
                    {
                        "object": "block",
                        "type": "callout",
                        "callout": {
                            "rich_text": [{
                                "text": {
                                    "content": f"💾 This data can be exported to CSV. Total records: {uploaded_count}"
                                }
                            }],
                            "icon": {"emoji": "💾"}
                        }
                    }
                ]
            )
            logger.info(f"Created comprehensive data export for {data.exchange}")
        except Exception as e:
            logger.warning(f"Failed to create comprehensive summary: {e}")