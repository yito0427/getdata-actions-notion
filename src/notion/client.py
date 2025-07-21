"""
Notion API client for uploading CSV files and creating database entries
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import aiohttp
from notion_client import AsyncClient
from loguru import logger

from ..models import CollectedData
from ..config import Config


class NotionClient:
    """Notion API client for data storage"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.client = AsyncClient(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID
        
    async def upload_csv_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Upload a CSV file to Notion
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            File object with URL and expiry time
        """
        # Get file info
        file_size = file_path.stat().st_size
        file_name = file_path.name
        
        if file_size > 20 * 1024 * 1024:  # 20MB
            # Use multipart upload for large files
            return await self._multipart_upload(file_path)
        else:
            # Simple upload for small files
            return await self._simple_upload(file_path)
    
    async def _simple_upload(self, file_path: Path) -> Dict[str, Any]:
        """Simple upload for files < 20MB"""
        # Note: Notion API file upload is not yet available in the Python SDK
        # For now, we'll store file path reference
        return {
            "url": f"file://{file_path.absolute()}",
            "name": file_path.name,
            "size": file_path.stat().st_size
        }
    
    async def _multipart_upload(self, file_path: Path) -> Dict[str, Any]:
        """Multipart upload for large files"""
        # Implementation for large files (if needed)
        raise NotImplementedError("Large file upload not yet implemented")
    
    async def create_data_entry(
        self, 
        exchange: str,
        data_type: str,
        csv_file_path: Path,
        summary_stats: Dict[str, Any],
        collected_data: CollectedData
    ) -> Dict[str, Any]:
        """
        Create a database entry with CSV file attachment and summary data
        
        Args:
            exchange: Exchange name
            data_type: Type of data (tickers, orderbooks, trades, ohlcv)
            csv_file_path: Path to the CSV file
            summary_stats: Summary statistics
            collected_data: Original collected data
        """
        # Upload CSV file first
        file_info = await self.upload_csv_file(csv_file_path)
        
        # Create title for the entry
        timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        title = f"{exchange} - {data_type} - {timestamp_str}"
        
        # Prepare properties
        properties = {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            },
            "Exchange": {
                "select": {
                    "name": exchange
                }
            },
            "Data Type": {
                "select": {
                    "name": data_type
                }
            },
            "Collection Time": {
                "date": {
                    "start": collected_data.collection_timestamp.isoformat()
                }
            },
            "CSV File": {
                "rich_text": [
                    {
                        "text": {
                            "content": csv_file_path.name
                        }
                    }
                ]
            },
            "Record Count": {
                "number": summary_stats.get("record_count", 0)
            },
            "File Size (KB)": {
                "number": csv_file_path.stat().st_size / 1024
            },
            "Status": {
                "select": {
                    "name": "Success" if not collected_data.errors else "Partial Failure"
                }
            }
        }
        
        # Add data-specific properties
        if data_type == "tickers" and collected_data.tickers:
            # Add average price, volume etc.
            avg_volume = sum(t.base_volume or 0 for t in collected_data.tickers) / len(collected_data.tickers)
            properties["Avg Volume"] = {"number": avg_volume}
            
        elif data_type == "orderbooks" and collected_data.orderbooks:
            # Add average spread
            avg_spread = sum(ob.spread_percentage or 0 for ob in collected_data.orderbooks) / len(collected_data.orderbooks)
            properties["Avg Spread %"] = {"number": avg_spread}
        
        # Create the database entry
        response = await self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
        
        logger.info(f"Created Notion entry: {title}")
        return response
    
    async def create_daily_summary_entry(
        self,
        date: str,
        summary_csv_path: Path,
        all_results: Dict[str, CollectedData]
    ) -> Dict[str, Any]:
        """
        Create a daily summary entry with aggregated statistics
        """
        # Upload summary CSV
        file_info = await self.upload_csv_file(summary_csv_path)
        
        # Calculate totals
        total_exchanges = len(all_results)
        total_tickers = sum(len(data.tickers) for data in all_results.values())
        total_orderbooks = sum(len(data.orderbooks) for data in all_results.values())
        total_trades = sum(len(data.trades) for data in all_results.values())
        total_errors = sum(len(data.errors) for data in all_results.values())
        
        title = f"Daily Summary - {date} - {total_exchanges} Exchanges"
        
        properties = {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Data Type": {
                "select": {"name": "Daily Summary"}
            },
            "Collection Time": {
                "date": {"start": datetime.now(timezone.utc).isoformat()}
            },
            "CSV File": {
                "rich_text": [{
                    "text": {"content": summary_csv_path.name}
                }]
            },
            "Exchange Count": {
                "number": total_exchanges
            },
            "Total Tickers": {
                "number": total_tickers
            },
            "Total OrderBooks": {
                "number": total_orderbooks
            },
            "Total Trades": {
                "number": total_trades
            },
            "Error Count": {
                "number": total_errors
            },
            "Status": {
                "select": {
                    "name": "Success" if total_errors == 0 else "Partial Failure"
                }
            }
        }
        
        response = await self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
        
        logger.info(f"Created daily summary entry: {title}")
        return response
    
    async def setup_database(self) -> Dict[str, Any]:
        """
        Setup or verify the Notion database schema
        """
        # Get current database schema
        database = await self.client.databases.retrieve(self.database_id)
        
        # Define required properties
        required_properties = {
            "Exchange": {"select": {}},
            "Data Type": {"select": {}},
            "Collection Time": {"date": {}},
            "CSV File": {"rich_text": {}},
            "Record Count": {"number": {"format": "number"}},
            "File Size (KB)": {"number": {"format": "number"}},
            "Status": {"select": {}},
            "Exchange Count": {"number": {"format": "number"}},
            "Total Tickers": {"number": {"format": "number"}},
            "Total OrderBooks": {"number": {"format": "number"}},
            "Total Trades": {"number": {"format": "number"}},
            "Error Count": {"number": {"format": "number"}},
            "Avg Volume": {"number": {"format": "number"}},
            "Avg Spread %": {"number": {"format": "percent"}}
        }
        
        # Update database schema if needed
        existing_props = database["properties"]
        props_to_add = {}
        
        for prop_name, prop_config in required_properties.items():
            if prop_name not in existing_props:
                props_to_add[prop_name] = prop_config
        
        if props_to_add:
            logger.info(f"Adding {len(props_to_add)} properties to database")
            await self.client.databases.update(
                database_id=self.database_id,
                properties=props_to_add
            )
        
        logger.info("Database schema verified")
        return database