#!/usr/bin/env python3
"""
Test script for CSV Export from Notion
NotionからCSVとして実データを抽出するテスト
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.notion_to_csv import NotionToCSVExporter
from src.config import Config
from loguru import logger


async def test_csv_export():
    """Test CSV export functionality"""
    
    # Verify environment variables
    if not Config.NOTION_API_KEY or not Config.NOTION_DATABASE_ID:
        logger.error("NOTION_API_KEY and NOTION_DATABASE_ID must be set")
        return
    
    logger.info("Starting CSV export test")
    logger.info(f"Database ID: {Config.NOTION_DATABASE_ID}")
    
    # Create exporter
    exporter = NotionToCSVExporter()
    
    # Export data from the last 24 hours
    start_date = datetime.now() - timedelta(days=1)
    
    logger.info(f"Exporting ticker data from {start_date} to now...")
    
    try:
        # Export ticker data
        csv_file = await exporter.export_ticker_data(
            start_date=start_date,
            exchanges=["binance", "coinbase"]  # Specific exchanges
        )
        
        if csv_file:
            logger.success(f"CSV export successful: {csv_file}")
            
            # Read and display first few lines
            with open(csv_file, 'r') as f:
                lines = f.readlines()[:10]
                logger.info("First 10 lines of exported CSV:")
                for line in lines:
                    print(line.rstrip())
        else:
            logger.warning("No data found to export")
            
        # Export all data
        logger.info("Exporting all cryptocurrency data...")
        all_exports = await exporter.export_all_data()
        
        logger.info(f"All exports completed: {all_exports}")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_csv_export())