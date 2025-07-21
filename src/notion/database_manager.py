"""
Notion Database Manager - Convert CSV data to Notion database records
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from notion_client import AsyncClient
from loguru import logger

from ..models import CollectedData, TickerData, OrderBookData, TradeData, OHLCVData
from ..config import Config


class NotionDatabaseManager:
    """Manages creation and updates of Notion databases for crypto data"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.client = AsyncClient(auth=Config.NOTION_API_KEY)
        
        # Database IDs for different data types
        self.database_ids = {
            "tickers": None,
            "orderbooks": None, 
            "trades": None,
            "ohlcv": None,
            "summary": None
        }
        
    async def setup_databases(self, parent_page_id: str) -> Dict[str, str]:
        """
        Create or get database IDs for all data types
        
        Args:
            parent_page_id: Parent page ID where databases will be created
            
        Returns:
            Dictionary mapping data types to database IDs
        """
        
        # Define database schemas
        databases_config = {
            "tickers": {
                "title": "Crypto Tickers",
                "description": "Real-time cryptocurrency price and volume data",
                "properties": {
                    "Name": {"title": {}},
                    "Exchange": {"select": {}},
                    "Symbol": {"select": {}},
                    "Timestamp": {"date": {}},
                    "Last Price": {"number": {"format": "number"}},
                    "Bid": {"number": {"format": "number"}},
                    "Ask": {"number": {"format": "number"}},
                    "High 24h": {"number": {"format": "number"}},
                    "Low 24h": {"number": {"format": "number"}},
                    "Volume Base": {"number": {"format": "number"}},
                    "Volume Quote": {"number": {"format": "number"}},
                    "Change %": {"number": {"format": "percent"}},
                    "Spread": {"number": {"format": "number"}},
                    "Spread %": {"number": {"format": "percent"}},
                    "VWAP": {"number": {"format": "number"}}
                }
            },
            "orderbooks": {
                "title": "Crypto OrderBooks", 
                "description": "Order book depth and spread data",
                "properties": {
                    "Name": {"title": {}},
                    "Exchange": {"select": {}},
                    "Symbol": {"select": {}},
                    "Timestamp": {"date": {}},
                    "Best Bid": {"number": {"format": "number"}},
                    "Best Ask": {"number": {"format": "number"}},
                    "Spread": {"number": {"format": "number"}},
                    "Spread %": {"number": {"format": "percent"}},
                    "Bid Depth": {"number": {"format": "number"}},
                    "Ask Depth": {"number": {"format": "number"}},
                    "Bid Count": {"number": {"format": "number"}},
                    "Ask Count": {"number": {"format": "number"}},
                    "Mid Price": {"number": {"format": "number"}},
                    "Imbalance": {"number": {"format": "number"}}
                }
            },
            "trades": {
                "title": "Crypto Trades",
                "description": "Recent trade execution data",
                "properties": {
                    "Name": {"title": {}},
                    "Exchange": {"select": {}},
                    "Symbol": {"select": {}},
                    "Timestamp": {"date": {}},
                    "Trade ID": {"rich_text": {}},
                    "Price": {"number": {"format": "number"}},
                    "Amount": {"number": {"format": "number"}},
                    "Cost": {"number": {"format": "number"}},
                    "Side": {"select": {}},
                    "Taker/Maker": {"select": {}}
                }
            },
            "ohlcv": {
                "title": "Crypto OHLCV",
                "description": "Candlestick OHLCV data for multiple timeframes",
                "properties": {
                    "Name": {"title": {}},
                    "Exchange": {"select": {}},
                    "Symbol": {"select": {}},
                    "Timeframe": {"select": {}},
                    "Timestamp": {"date": {}},
                    "Open": {"number": {"format": "number"}},
                    "High": {"number": {"format": "number"}},
                    "Low": {"number": {"format": "number"}},
                    "Close": {"number": {"format": "number"}},
                    "Volume": {"number": {"format": "number"}}
                }
            },
            "summary": {
                "title": "Data Collection Summary",
                "description": "Summary of data collection runs",
                "properties": {
                    "Name": {"title": {}},
                    "Exchange": {"select": {}},
                    "Collection Time": {"date": {}},
                    "Ticker Count": {"number": {"format": "number"}},
                    "OrderBook Count": {"number": {"format": "number"}},
                    "Trade Count": {"number": {"format": "number"}},
                    "OHLCV Count": {"number": {"format": "number"}},
                    "Error Count": {"number": {"format": "number"}},
                    "Status": {"select": {}},
                    "Duration (sec)": {"number": {"format": "number"}}
                }
            }
        }
        
        # Create databases
        for db_type, config in databases_config.items():
            db_id = await self._create_or_get_database(
                parent_page_id=parent_page_id,
                title=config["title"],
                description=config["description"],
                properties=config["properties"]
            )
            self.database_ids[db_type] = db_id
            
        logger.info(f"Setup {len(self.database_ids)} databases")
        return self.database_ids
    
    async def _create_or_get_database(
        self, 
        parent_page_id: str, 
        title: str, 
        description: str, 
        properties: Dict[str, Any]
    ) -> str:
        """Create a new database or return existing one"""
        
        try:
            # Create the database
            response = await self.client.databases.create(
                parent={
                    "type": "page_id",
                    "page_id": parent_page_id
                },
                title=[{
                    "text": {"content": title}
                }],
                properties=properties
            )
            
            logger.info(f"Created database: {title}")
            return response["id"]
            
        except Exception as e:
            logger.error(f"Failed to create database {title}: {e}")
            raise
    
    async def insert_ticker_data(self, tickers: List[TickerData]) -> int:
        """Insert ticker data into Notion database"""
        if not self.database_ids.get("tickers"):
            raise ValueError("Tickers database not initialized")
            
        successful_inserts = 0
        
        # Process in batches to avoid rate limits
        batch_size = 10
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            
            # Create batch of records
            tasks = []
            for ticker in batch:
                tasks.append(self._create_ticker_record(ticker))
                
            # Execute batch
            try:
                await asyncio.gather(*tasks)
                successful_inserts += len(batch)
                logger.info(f"Inserted {len(batch)} ticker records")
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to insert ticker batch: {e}")
                
        return successful_inserts
    
    async def _create_ticker_record(self, ticker: TickerData) -> Dict[str, Any]:
        """Create a single ticker record"""
        
        # Create title
        title = f"{ticker.exchange} {ticker.symbol} {ticker.timestamp.strftime('%H:%M:%S')}"
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Exchange": {
                "select": {"name": ticker.exchange}
            },
            "Symbol": {
                "select": {"name": ticker.symbol}
            },
            "Timestamp": {
                "date": {"start": ticker.timestamp.isoformat()}
            }
        }
        
        # Add numeric fields if available
        numeric_fields = {
            "Last Price": ticker.last,
            "Bid": ticker.bid,
            "Ask": ticker.ask,
            "High 24h": ticker.high,
            "Low 24h": ticker.low,
            "Volume Base": ticker.base_volume,
            "Volume Quote": ticker.quote_volume,
            "VWAP": ticker.vwap
        }
        
        for field_name, value in numeric_fields.items():
            if value is not None:
                properties[field_name] = {"number": value}
                
        # Calculate spread
        if ticker.bid and ticker.ask:
            spread = ticker.ask - ticker.bid
            spread_percent = (spread / ticker.ask) * 100
            properties["Spread"] = {"number": spread}
            properties["Spread %"] = {"number": spread_percent}
            
        # Change percentage
        if ticker.percentage is not None:
            properties["Change %"] = {"number": ticker.percentage / 100}
            
        return await self.client.pages.create(
            parent={"database_id": self.database_ids["tickers"]},
            properties=properties
        )
    
    async def insert_orderbook_data(self, orderbooks: List[OrderBookData]) -> int:
        """Insert orderbook data into Notion database"""
        if not self.database_ids.get("orderbooks"):
            raise ValueError("OrderBooks database not initialized")
            
        successful_inserts = 0
        batch_size = 10
        
        for i in range(0, len(orderbooks), batch_size):
            batch = orderbooks[i:i + batch_size]
            
            tasks = []
            for ob in batch:
                tasks.append(self._create_orderbook_record(ob))
                
            try:
                await asyncio.gather(*tasks)
                successful_inserts += len(batch)
                logger.info(f"Inserted {len(batch)} orderbook records")
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to insert orderbook batch: {e}")
                
        return successful_inserts
    
    async def _create_orderbook_record(self, ob: OrderBookData) -> Dict[str, Any]:
        """Create a single orderbook record"""
        
        title = f"{ob.exchange} {ob.symbol} OrderBook {ob.timestamp.strftime('%H:%M:%S')}"
        
        best_bid = ob.bids[0][0] if ob.bids else None
        best_ask = ob.asks[0][0] if ob.asks else None
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else None
        imbalance = ob.bid_depth / ob.ask_depth if ob.ask_depth and ob.ask_depth > 0 else None
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Exchange": {
                "select": {"name": ob.exchange}
            },
            "Symbol": {
                "select": {"name": ob.symbol}
            },
            "Timestamp": {
                "date": {"start": ob.timestamp.isoformat()}
            }
        }
        
        # Add numeric fields
        numeric_fields = {
            "Best Bid": best_bid,
            "Best Ask": best_ask,
            "Spread": ob.spread,
            "Bid Depth": ob.bid_depth,
            "Ask Depth": ob.ask_depth,
            "Bid Count": len(ob.bids),
            "Ask Count": len(ob.asks),
            "Mid Price": mid_price,
            "Imbalance": imbalance
        }
        
        for field_name, value in numeric_fields.items():
            if value is not None:
                properties[field_name] = {"number": value}
                
        if ob.spread_percentage is not None:
            properties["Spread %"] = {"number": ob.spread_percentage / 100}
            
        return await self.client.pages.create(
            parent={"database_id": self.database_ids["orderbooks"]},
            properties=properties
        )
    
    async def insert_summary_data(self, data: CollectedData) -> Dict[str, Any]:
        """Insert collection summary into Notion database"""
        if not self.database_ids.get("summary"):
            raise ValueError("Summary database not initialized")
            
        title = f"{data.exchange} Summary {data.collection_timestamp.strftime('%Y-%m-%d %H:%M')}"
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Exchange": {
                "select": {"name": data.exchange}
            },
            "Collection Time": {
                "date": {"start": data.collection_timestamp.isoformat()}
            },
            "Ticker Count": {
                "number": len(data.tickers)
            },
            "OrderBook Count": {
                "number": len(data.orderbooks)
            },
            "Trade Count": {
                "number": len(data.trades)
            },
            "OHLCV Count": {
                "number": len(data.ohlcv)
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
        
        return await self.client.pages.create(
            parent={"database_id": self.database_ids["summary"]},
            properties=properties
        )
    
    async def process_collected_data(self, data: CollectedData) -> Dict[str, int]:
        """
        Process all collected data and insert into appropriate databases
        
        Returns:
            Dictionary with counts of inserted records
        """
        results = {
            "tickers": 0,
            "orderbooks": 0,
            "trades": 0,
            "ohlcv": 0,
            "summary": 0
        }
        
        try:
            # Insert ticker data
            if data.tickers and self.database_ids.get("tickers"):
                results["tickers"] = await self.insert_ticker_data(data.tickers)
                
            # Insert orderbook data
            if data.orderbooks and self.database_ids.get("orderbooks"):
                results["orderbooks"] = await self.insert_orderbook_data(data.orderbooks)
                
            # Insert summary
            if self.database_ids.get("summary"):
                await self.insert_summary_data(data)
                results["summary"] = 1
                
            logger.info(f"Processed {data.exchange}: {results}")
            
        except Exception as e:
            logger.error(f"Failed to process data for {data.exchange}: {e}")
            
        return results