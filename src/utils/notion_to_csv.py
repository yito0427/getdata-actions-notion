"""
Notion to CSV Exporter - Extract cryptocurrency data from Notion database
Notionデータベースから仮想通貨データをCSVにエクスポート
"""

import csv
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from notion_client import AsyncClient
from loguru import logger

from ..config import Config


class NotionToCSVExporter:
    """NotionデータベースからCSVにデータをエクスポート"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.client = AsyncClient(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID
        
    async def export_ticker_data(self, start_date: Optional[datetime] = None, 
                                end_date: Optional[datetime] = None,
                                exchanges: Optional[List[str]] = None) -> str:
        """Export ticker data from Notion to CSV"""
        
        # Build filter
        filter_conditions = []
        
        # Filter by data type
        filter_conditions.append({
            "property": "Data Type",
            "select": {
                "equals": "Ticker Detail"
            }
        })
        
        # Date filter
        if start_date:
            filter_conditions.append({
                "property": "Collection Time",
                "date": {
                    "on_or_after": start_date.isoformat()
                }
            })
            
        if end_date:
            filter_conditions.append({
                "property": "Collection Time",
                "date": {
                    "on_or_before": end_date.isoformat()
                }
            })
        
        # Exchange filter
        if exchanges:
            exchange_filters = []
            for exchange in exchanges:
                exchange_filters.append({
                    "property": "Exchange",
                    "select": {"equals": exchange}
                })
            
            if len(exchange_filters) > 1:
                filter_conditions.append({
                    "or": exchange_filters
                })
            else:
                filter_conditions.extend(exchange_filters)
        
        # Combine filters
        filter_query = None
        if filter_conditions:
            if len(filter_conditions) > 1:
                filter_query = {"and": filter_conditions}
            else:
                filter_query = filter_conditions[0]
        
        # Query Notion database
        results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            try:
                response = await self.client.databases.query(
                    database_id=self.database_id,
                    filter=filter_query,
                    start_cursor=start_cursor,
                    page_size=100
                )
                
                results.extend(response["results"])
                has_more = response["has_more"]
                start_cursor = response.get("next_cursor")
                
                logger.info(f"Fetched {len(response['results'])} records from Notion")
                
                # Rate limiting
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Failed to query Notion database: {e}")
                break
        
        # Extract and process data
        ticker_data = []
        
        for page in results:
            try:
                # Extract properties
                props = page["properties"]
                
                # Basic info
                name = self._get_title(props.get("Name", {}))
                exchange = self._get_select(props.get("Exchange", {}))
                collection_time = self._get_date(props.get("Collection Time", {}))
                
                # Try to extract price from title or Avg Volume field
                price = self._get_number(props.get("Avg Volume", {}))  # Repurposed field
                change_percent = self._get_number(props.get("Avg Spread %", {})) * 100  # Convert back
                
                # Extract symbol and actual price from title
                symbol = "UNKNOWN"
                actual_price = None
                
                if name:
                    # Parse title format: "EXCHANGE SYMBOL | $PRICE | CHANGE%"
                    parts = name.split("|")
                    if len(parts) >= 2:
                        # Extract symbol
                        symbol_parts = parts[0].strip().split()
                        if len(symbol_parts) >= 2:
                            symbol = symbol_parts[1]
                        
                        # Extract price
                        price_part = parts[1].strip()
                        if price_part.startswith("$"):
                            try:
                                actual_price = float(price_part[1:])
                            except:
                                pass
                
                # Get JSON data from page content if available
                page_content = await self._get_page_content(page["id"])
                json_data = self._extract_json_from_content(page_content)
                
                if json_data:
                    # Use JSON data if available
                    ticker_data.append({
                        "timestamp": collection_time or datetime.now().isoformat(),
                        "exchange": exchange or json_data.get("exchange", "UNKNOWN"),
                        "symbol": json_data.get("symbol", symbol),
                        "price": json_data.get("price", {}).get("last", actual_price or price),
                        "bid": json_data.get("price", {}).get("bid"),
                        "ask": json_data.get("price", {}).get("ask"),
                        "high": json_data.get("price", {}).get("high"),
                        "low": json_data.get("price", {}).get("low"),
                        "open": json_data.get("price", {}).get("open"),
                        "close": json_data.get("price", {}).get("close"),
                        "vwap": json_data.get("price", {}).get("vwap"),
                        "base_volume": json_data.get("volume", {}).get("base"),
                        "quote_volume": json_data.get("volume", {}).get("quote"),
                        "change_percent": json_data.get("change", {}).get("percentage", change_percent),
                        "change_absolute": json_data.get("change", {}).get("absolute"),
                        "spread": json_data.get("spread", {}).get("value"),
                        "spread_percent": json_data.get("spread", {}).get("percentage")
                    })
                else:
                    # Fallback to basic data
                    ticker_data.append({
                        "timestamp": collection_time or datetime.now().isoformat(),
                        "exchange": exchange or "UNKNOWN",
                        "symbol": symbol,
                        "price": actual_price or price or 0,
                        "bid": None,
                        "ask": None,
                        "high": None,
                        "low": None,
                        "open": None,
                        "close": None,
                        "vwap": None,
                        "base_volume": None,
                        "quote_volume": None,
                        "change_percent": change_percent,
                        "change_absolute": None,
                        "spread": None,
                        "spread_percent": None
                    })
                    
            except Exception as e:
                logger.error(f"Failed to process page: {e}")
                continue
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("exports")
        output_dir.mkdir(exist_ok=True)
        
        csv_file = output_dir / f"notion_ticker_export_{timestamp}.csv"
        
        if ticker_data:
            # Write CSV
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    "timestamp", "exchange", "symbol", "price", "bid", "ask",
                    "high", "low", "open", "close", "vwap", "base_volume",
                    "quote_volume", "change_percent", "change_absolute",
                    "spread", "spread_percent"
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(ticker_data)
            
            logger.info(f"Exported {len(ticker_data)} ticker records to {csv_file}")
            return str(csv_file)
        else:
            logger.warning("No ticker data found to export")
            return ""
    
    async def _get_page_content(self, page_id: str) -> List[Dict[str, Any]]:
        """Get page content blocks"""
        try:
            response = await self.client.blocks.children.list(block_id=page_id)
            return response.get("results", [])
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return []
    
    def _extract_json_from_content(self, blocks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract JSON data from page content blocks"""
        for block in blocks:
            if block.get("type") == "code" and block.get("code", {}).get("language") == "json":
                rich_text = block.get("code", {}).get("rich_text", [])
                if rich_text:
                    json_text = "".join([rt.get("text", {}).get("content", "") for rt in rich_text])
                    try:
                        return json.loads(json_text)
                    except:
                        pass
        return None
    
    def _get_title(self, prop: Dict[str, Any]) -> Optional[str]:
        """Extract title from property"""
        title = prop.get("title", [])
        if title:
            return title[0].get("text", {}).get("content")
        return None
    
    def _get_select(self, prop: Dict[str, Any]) -> Optional[str]:
        """Extract select value from property"""
        select = prop.get("select")
        if select:
            return select.get("name")
        return None
    
    def _get_number(self, prop: Dict[str, Any]) -> Optional[float]:
        """Extract number from property"""
        return prop.get("number", 0)
    
    def _get_date(self, prop: Dict[str, Any]) -> Optional[str]:
        """Extract date from property"""
        date = prop.get("date")
        if date:
            return date.get("start")
        return None
    
    async def export_all_data(self, output_format: str = "csv") -> Dict[str, str]:
        """Export all cryptocurrency data from Notion"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("exports") / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        
        exports = {}
        
        # Export ticker data
        ticker_file = await self.export_ticker_data()
        if ticker_file:
            exports["tickers"] = ticker_file
        
        # Export summary data
        summary_file = await self._export_summary_data(output_dir)
        if summary_file:
            exports["summary"] = summary_file
        
        # Create master export file with all data
        master_file = output_dir / f"crypto_data_export_{timestamp}.json"
        
        # Collect all data
        all_data = {
            "export_timestamp": datetime.now().isoformat(),
            "database_id": self.database_id,
            "files": exports,
            "statistics": await self._calculate_statistics()
        }
        
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        exports["master"] = str(master_file)
        
        logger.info(f"Complete export saved to {output_dir}")
        return exports
    
    async def _export_summary_data(self, output_dir: Path) -> Optional[str]:
        """Export summary/aggregate data"""
        # Query for summary records
        try:
            response = await self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Data Type",
                    "select": {"equals": "Daily Summary"}
                }
            )
            
            summaries = []
            for page in response["results"]:
                props = page["properties"]
                summaries.append({
                    "timestamp": self._get_date(props.get("Collection Time", {})),
                    "exchange": self._get_select(props.get("Exchange", {})),
                    "total_tickers": self._get_number(props.get("Total Tickers", {})),
                    "total_orderbooks": self._get_number(props.get("Total OrderBooks", {})),
                    "total_trades": self._get_number(props.get("Total Trades", {})),
                    "errors": self._get_number(props.get("Error Count", {})),
                    "status": self._get_select(props.get("Status", {}))
                })
            
            if summaries:
                csv_file = output_dir / "daily_summaries.csv"
                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ["timestamp", "exchange", "total_tickers", 
                                "total_orderbooks", "total_trades", "errors", "status"]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(summaries)
                
                return str(csv_file)
                
        except Exception as e:
            logger.error(f"Failed to export summary data: {e}")
        
        return None
    
    async def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from the database"""
        stats = {
            "total_records": 0,
            "exchanges": set(),
            "date_range": {
                "start": None,
                "end": None
            },
            "data_types": {}
        }
        
        try:
            # Get all records for statistics
            response = await self.client.databases.query(
                database_id=self.database_id,
                page_size=100
            )
            
            for page in response["results"]:
                props = page["properties"]
                stats["total_records"] += 1
                
                # Exchange
                exchange = self._get_select(props.get("Exchange", {}))
                if exchange:
                    stats["exchanges"].add(exchange)
                
                # Data type
                data_type = self._get_select(props.get("Data Type", {}))
                if data_type:
                    stats["data_types"][data_type] = stats["data_types"].get(data_type, 0) + 1
                
                # Date range
                date = self._get_date(props.get("Collection Time", {}))
                if date:
                    if not stats["date_range"]["start"] or date < stats["date_range"]["start"]:
                        stats["date_range"]["start"] = date
                    if not stats["date_range"]["end"] or date > stats["date_range"]["end"]:
                        stats["date_range"]["end"] = date
            
            stats["exchanges"] = list(stats["exchanges"])
            
        except Exception as e:
            logger.error(f"Failed to calculate statistics: {e}")
        
        return stats


async def export_notion_data_to_csv():
    """Main function to export Notion data to CSV"""
    exporter = NotionToCSVExporter()
    
    logger.info("Starting Notion data export...")
    
    # Export all data
    exports = await exporter.export_all_data()
    
    logger.info(f"Export complete. Files created: {exports}")
    
    return exports


if __name__ == "__main__":
    # Run export
    asyncio.run(export_notion_data_to_csv())