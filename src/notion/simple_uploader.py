"""
Simple Notion uploader that uses existing database
既存のNotionデータベースに直接レコードを追加
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from notion_client import AsyncClient
from loguru import logger

from ..models import CollectedData, TickerData, OrderBookData
from ..config import Config


class SimpleNotionUploader:
    """既存のNotionデータベースに直接データを追加"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.client = AsyncClient(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID
        
    async def upload_ticker_data(self, tickers: List[TickerData]) -> int:
        """Upload ticker data to existing Notion database"""
        successful_uploads = 0
        
        for ticker in tickers:
            try:
                # Create page properties for the ticker
                properties = self._create_ticker_properties(ticker)
                
                # Create page in database
                await self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                
                successful_uploads += 1
                logger.info(f"Uploaded ticker: {ticker.exchange} {ticker.symbol}")
                
                # Rate limiting
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Failed to upload ticker {ticker.exchange} {ticker.symbol}: {e}")
                
        return successful_uploads
    
    def _create_ticker_properties(self, ticker: TickerData) -> Dict[str, Any]:
        """Create properties for a ticker record using existing database schema"""
        
        # Create a unique title
        title = f"{ticker.exchange} {ticker.symbol} Ticker - {ticker.timestamp.strftime('%H:%M:%S')}"
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Data Type": {
                "select": {"name": "Ticker"}
            },
            "Exchange": {
                "select": {"name": ticker.exchange}
            },
            "Collection Time": {
                "date": {"start": ticker.timestamp.isoformat()}
            },
            "Record Count": {
                "number": 1  # This is a single ticker record
            }
        }
        
        # Add available numeric data using existing fields
        if ticker.base_volume:
            properties["Avg Volume"] = {"number": ticker.base_volume}
            
        if ticker.bid and ticker.ask:
            spread_percent = ((ticker.ask - ticker.bid) / ticker.ask) * 100
            properties["Avg Spread %"] = {"number": spread_percent / 100}  # As decimal for percentage format
            
        # Use CSV File field to store ticker details as text
        ticker_details = f"Price: ${ticker.last:.2f}" if ticker.last else "Price: N/A"
        if ticker.percentage:
            ticker_details += f", Change: {ticker.percentage:.2f}%"
        if ticker.base_volume:
            ticker_details += f", Volume: {ticker.base_volume:.2f}"
            
        # Skip CSV File field for now since it expects file uploads
        # We'll store the data in other available fields
        
        properties["Status"] = {
            "select": {"name": "Success"}
        }
        
        properties["Error Count"] = {
            "number": 0
        }
            
        return properties
    
    async def upload_exchange_data(self, data: CollectedData) -> Dict[str, Any]:
        """Upload all data from one exchange"""
        start_time = datetime.now(timezone.utc)
        
        result = {
            "exchange": data.exchange,
            "start_time": start_time.isoformat(),
            "records_uploaded": 0,
            "status": "pending"
        }
        
        try:
            # Upload ticker data
            if data.tickers:
                uploaded = await self.upload_ticker_data(data.tickers)
                result["records_uploaded"] = uploaded
                
            # Create summary record
            await self._create_summary_record(data, result["records_uploaded"])
            
            end_time = datetime.now(timezone.utc)
            result["end_time"] = end_time.isoformat()
            result["duration"] = (end_time - start_time).total_seconds()
            result["status"] = "success"
            
            logger.info(f"Successfully uploaded {result['records_uploaded']} records for {data.exchange}")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Failed to upload data for {data.exchange}: {e}")
            
        return result
    
    async def _create_summary_record(self, data: CollectedData, uploaded_count: int):
        """Create a summary record for the collection"""
        title = f"📊 {data.exchange} Summary - {data.collection_timestamp.strftime('%Y-%m-%d %H:%M')}"
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Data Type": {
                "select": {"name": "Daily Summary"}
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
        
        # Add average volume if available
        if data.tickers:
            avg_volume = sum(t.base_volume or 0 for t in data.tickers) / len(data.tickers)
            properties["Avg Volume"] = {"number": avg_volume}
            
        # Add average spread if available
        if data.orderbooks:
            spreads = [ob.spread_percentage or 0 for ob in data.orderbooks]
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
            properties["Avg Spread %"] = {"number": avg_spread / 100}  # As decimal
        
        try:
            await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            logger.info(f"Created summary record for {data.exchange}")
        except Exception as e:
            logger.warning(f"Failed to create summary record: {e}")
    
    async def upload_all_exchanges(self, all_results: Dict[str, CollectedData]) -> Dict[str, Any]:
        """Upload data from all exchanges"""
        start_time = datetime.now(timezone.utc)
        
        upload_summary = {
            "start_time": start_time.isoformat(),
            "exchanges": {},
            "totals": {
                "exchanges_processed": 0,
                "exchanges_successful": 0,
                "total_records": 0
            }
        }
        
        for exchange_name, data in all_results.items():
            result = await self.upload_exchange_data(data)
            upload_summary["exchanges"][exchange_name] = result
            
            # Update totals
            upload_summary["totals"]["exchanges_processed"] += 1
            if result["status"] == "success":
                upload_summary["totals"]["exchanges_successful"] += 1
                upload_summary["totals"]["total_records"] += result.get("records_uploaded", 0)
                
            # Rate limiting between exchanges
            await asyncio.sleep(1)
            
        end_time = datetime.now(timezone.utc)
        upload_summary["end_time"] = end_time.isoformat()
        upload_summary["total_duration"] = (end_time - start_time).total_seconds()
        
        # Log final summary
        totals = upload_summary["totals"]
        logger.info(f"Upload complete: {totals['exchanges_successful']}/{totals['exchanges_processed']} "
                   f"exchanges, {totals['total_records']} total records")
        
        return upload_summary