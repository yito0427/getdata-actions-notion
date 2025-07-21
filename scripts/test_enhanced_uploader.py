#!/usr/bin/env python3
"""
Test script for Enhanced Notion Uploader
実際の仮想通貨データをNotionに保存するテスト
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.manager import ExchangeCollectorManager
from src.notion.enhanced_uploader import EnhancedNotionUploader
from src.config import Config
from loguru import logger


async def test_enhanced_uploader():
    """Test the enhanced uploader with real data"""
    
    # Verify environment variables
    if not Config.NOTION_API_KEY or not Config.NOTION_DATABASE_ID:
        logger.error("NOTION_API_KEY and NOTION_DATABASE_ID must be set")
        return
    
    logger.info("Starting enhanced uploader test")
    logger.info(f"Database ID: {Config.NOTION_DATABASE_ID}")
    
    # Collect data from 2 exchanges as a test
    exchanges = ["binance", "coinbase"]
    manager = ExchangeCollectorManager(exchanges)
    
    logger.info("Collecting data from exchanges...")
    results = await manager.collect_all(max_concurrent=2)
    
    # Upload using enhanced uploader
    uploader = EnhancedNotionUploader()
    
    for exchange_name, data in results.items():
        if data.tickers:
            logger.info(f"Uploading {len(data.tickers)} tickers from {exchange_name}")
            result = await uploader.upload_exchange_data(data)
            
            logger.info(f"Upload result: {result}")
            
            if result["status"] == "success":
                logger.success(f"Successfully uploaded {result['records_uploaded']} records with full data")
                logger.info("Actual cryptocurrency data (prices, volumes, etc.) has been stored in Notion")
                logger.info("This data can be exported to CSV using: python -m src.utils.notion_to_csv")
            else:
                logger.error(f"Upload failed: {result.get('error', 'Unknown error')}")
    
    logger.info("Test completed. Check your Notion database for the uploaded data.")


if __name__ == "__main__":
    asyncio.run(test_enhanced_uploader())