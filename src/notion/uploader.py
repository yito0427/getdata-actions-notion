"""
Notion uploader that combines CSV writing and Notion upload
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from loguru import logger

from .client import NotionClient
from ..utils.csv_writer import CSVWriter
from ..models import CollectedData


class NotionUploader:
    """Handles CSV creation and Notion upload"""
    
    def __init__(self):
        """Initialize uploader"""
        self.csv_writer = CSVWriter()
        self.notion_client = NotionClient()
        
    async def process_and_upload(self, data: CollectedData) -> Dict[str, Any]:
        """
        Process collected data: save to CSV and upload to Notion
        
        Args:
            data: Collected data from an exchange
            
        Returns:
            Dictionary with file paths and Notion URLs
        """
        results = {
            "exchange": data.exchange,
            "csv_files": {},
            "notion_entries": []
        }
        
        try:
            # Save data to CSV files
            csv_files = self.csv_writer.save_collected_data(data)
            results["csv_files"] = csv_files
            
            # Upload each CSV file to Notion
            for data_type, file_path in csv_files.items():
                if data_type == "summary":
                    continue  # Skip summary for individual uploads
                    
                # Calculate summary stats
                summary_stats = self._calculate_summary_stats(data, data_type)
                
                # Create Notion entry with CSV attachment
                notion_response = await self.notion_client.create_data_entry(
                    exchange=data.exchange,
                    data_type=data_type,
                    csv_file_path=Path(file_path),
                    summary_stats=summary_stats,
                    collected_data=data
                )
                
                results["notion_entries"].append({
                    "type": data_type,
                    "notion_id": notion_response["id"],
                    "url": notion_response["url"]
                })
                
                logger.info(f"Uploaded {data_type} for {data.exchange} to Notion")
                
        except Exception as e:
            logger.error(f"Failed to process {data.exchange}: {e}")
            results["error"] = str(e)
            
        return results
    
    async def process_all_exchanges(self, all_results: Dict[str, CollectedData]) -> Dict[str, Any]:
        """
        Process data from all exchanges
        
        Args:
            all_results: Dictionary of exchange name to collected data
            
        Returns:
            Summary of all uploads
        """
        upload_results = {
            "date": datetime.utcnow().strftime("%Y%m%d"),
            "exchanges": {},
            "daily_summary": None
        }
        
        # Process each exchange
        for exchange_name, data in all_results.items():
            result = await self.process_and_upload(data)
            upload_results["exchanges"][exchange_name] = result
            
        # Create daily summary
        try:
            summary_file = self.csv_writer.create_daily_summary(all_results)
            
            # Upload daily summary to Notion
            summary_response = await self.notion_client.create_daily_summary_entry(
                date=upload_results["date"],
                summary_csv_path=summary_file,
                all_results=all_results
            )
            
            upload_results["daily_summary"] = {
                "csv_file": str(summary_file),
                "notion_id": summary_response["id"],
                "url": summary_response["url"]
            }
            
            logger.info("Created and uploaded daily summary")
            
        except Exception as e:
            logger.error(f"Failed to create daily summary: {e}")
            upload_results["daily_summary_error"] = str(e)
            
        return upload_results
    
    def _calculate_summary_stats(self, data: CollectedData, data_type: str) -> Dict[str, Any]:
        """Calculate summary statistics for each data type"""
        stats = {}
        
        if data_type == "tickers":
            stats["record_count"] = len(data.tickers)
            if data.tickers:
                stats["unique_symbols"] = len(set(t.symbol for t in data.tickers))
                stats["avg_volume"] = sum(t.base_volume or 0 for t in data.tickers) / len(data.tickers)
                
        elif data_type == "orderbooks":
            stats["record_count"] = len(data.orderbooks)
            if data.orderbooks:
                stats["unique_symbols"] = len(set(ob.symbol for ob in data.orderbooks))
                spreads = [ob.spread_percentage for ob in data.orderbooks if ob.spread_percentage]
                stats["avg_spread_percent"] = sum(spreads) / len(spreads) if spreads else 0
                
        elif data_type == "trades":
            stats["record_count"] = len(data.trades)
            if data.trades:
                stats["unique_symbols"] = len(set(t.symbol for t in data.trades))
                stats["total_volume"] = sum(t.amount or 0 for t in data.trades)
                
        elif data_type == "ohlcv":
            stats["record_count"] = len(data.ohlcv)
            if data.ohlcv:
                stats["unique_symbols"] = len(set(o.symbol for o in data.ohlcv))
                stats["timeframes"] = list(set(o.timeframe for o in data.ohlcv))
                
        return stats
    
    async def setup_notion_database(self):
        """Setup or verify Notion database schema"""
        await self.notion_client.setup_database()