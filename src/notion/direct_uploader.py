"""
Direct Notion uploader that converts collected data to database records
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from loguru import logger

from .database_manager import NotionDatabaseManager
from ..models import CollectedData
from ..config import Config


class NotionDirectUploader:
    """Uploads crypto data directly to Notion databases (no CSV files)"""
    
    def __init__(self, parent_page_id: str):
        """
        Initialize uploader
        
        Args:
            parent_page_id: Notion page ID where databases will be created
        """
        self.parent_page_id = parent_page_id
        self.db_manager = NotionDatabaseManager()
        self.setup_complete = False
        
    async def setup_databases(self) -> Dict[str, str]:
        """Setup all required Notion databases"""
        try:
            database_ids = await self.db_manager.setup_databases(self.parent_page_id)
            self.setup_complete = True
            logger.info("Notion databases setup complete")
            return database_ids
            
        except Exception as e:
            logger.error(f"Failed to setup Notion databases: {e}")
            raise
    
    async def upload_exchange_data(self, data: CollectedData) -> Dict[str, Any]:
        """
        Upload data from a single exchange to Notion databases
        
        Args:
            data: Collected data from an exchange
            
        Returns:
            Dictionary with upload results
        """
        if not self.setup_complete:
            raise ValueError("Databases not setup. Call setup_databases() first.")
            
        start_time = datetime.now(timezone.utc)
        
        try:
            # Process the collected data
            results = await self.db_manager.process_collected_data(data)
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            upload_summary = {
                "exchange": data.exchange,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "records_inserted": results,
                "total_records": sum(results.values()),
                "status": "success" if results["summary"] > 0 else "failed"
            }
            
            logger.info(f"Uploaded {data.exchange} data: {results['tickers']} tickers, "
                       f"{results['orderbooks']} orderbooks in {duration:.1f}s")
            
            return upload_summary
            
        except Exception as e:
            logger.error(f"Failed to upload {data.exchange} data: {e}")
            return {
                "exchange": data.exchange,
                "status": "error",
                "error": str(e),
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            }
    
    async def upload_all_exchanges(self, all_results: Dict[str, CollectedData]) -> Dict[str, Any]:
        """
        Upload data from all exchanges to Notion databases
        
        Args:
            all_results: Dictionary mapping exchange names to collected data
            
        Returns:
            Summary of all uploads
        """
        if not self.setup_complete:
            await self.setup_databases()
            
        start_time = datetime.now(timezone.utc)
        upload_results = {
            "start_time": start_time.isoformat(),
            "exchanges": {},
            "totals": {
                "exchanges_processed": 0,
                "exchanges_successful": 0,
                "total_tickers": 0,
                "total_orderbooks": 0,
                "total_records": 0
            }
        }
        
        # Process each exchange
        for exchange_name, data in all_results.items():
            result = await self.upload_exchange_data(data)
            upload_results["exchanges"][exchange_name] = result
            
            # Update totals
            upload_results["totals"]["exchanges_processed"] += 1
            if result.get("status") == "success":
                upload_results["totals"]["exchanges_successful"] += 1
                
                records = result.get("records_inserted", {})
                upload_results["totals"]["total_tickers"] += records.get("tickers", 0)
                upload_results["totals"]["total_orderbooks"] += records.get("orderbooks", 0)
                upload_results["totals"]["total_records"] += result.get("total_records", 0)
            
            # Rate limiting between exchanges
            await asyncio.sleep(1)
        
        end_time = datetime.now(timezone.utc)
        upload_results["end_time"] = end_time.isoformat()
        upload_results["total_duration_seconds"] = (end_time - start_time).total_seconds()
        
        # Log summary
        totals = upload_results["totals"]
        logger.info(f"Upload complete: {totals['exchanges_successful']}/{totals['exchanges_processed']} "
                   f"exchanges, {totals['total_records']} total records, "
                   f"{upload_results['total_duration_seconds']:.1f}s")
        
        return upload_results
    
    async def create_daily_summary_page(self, upload_results: Dict[str, Any]) -> str:
        """
        Create a summary page with upload results
        
        Args:
            upload_results: Results from upload_all_exchanges
            
        Returns:
            URL of the created summary page
        """
        try:
            # Create summary content
            totals = upload_results["totals"]
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            title = f"Crypto Data Collection - {date_str}"
            
            # Create blocks for the page content
            blocks = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Collection Summary"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": f"Date: {date_str}\\n"}},
                            {"text": {"content": f"Exchanges Processed: {totals['exchanges_processed']}\\n"}},
                            {"text": {"content": f"Exchanges Successful: {totals['exchanges_successful']}\\n"}},
                            {"text": {"content": f"Total Records: {totals['total_records']}\\n"}},
                            {"text": {"content": f"Duration: {upload_results['total_duration_seconds']:.1f} seconds"}}
                        ]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": "Exchange Details"}}]
                    }
                }
            ]
            
            # Add exchange details
            for exchange_name, result in upload_results["exchanges"].items():
                status_emoji = "✅" if result.get("status") == "success" else "❌"
                records = result.get("records_inserted", {})
                
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"text": {"content": f"{status_emoji} {exchange_name}: "}},
                            {"text": {"content": f"{records.get('tickers', 0)} tickers, "}},
                            {"text": {"content": f"{records.get('orderbooks', 0)} orderbooks"}}
                        ]
                    }
                })
            
            # Create the page
            response = await self.db_manager.client.pages.create(
                parent={"page_id": self.parent_page_id},
                properties={
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                children=blocks
            )
            
            logger.info(f"Created daily summary page: {title}")
            return response["url"]
            
        except Exception as e:
            logger.error(f"Failed to create daily summary page: {e}")
            return None