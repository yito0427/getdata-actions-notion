"""
Main entry point for cryptocurrency data collection
"""

import asyncio
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
import json
from loguru import logger

from .collectors.manager import ExchangeCollectorManager
from .config import Config
from .notion.uploader import NotionUploader
from .notion.direct_uploader import NotionDirectUploader
from .notion.simple_uploader import SimpleNotionUploader
from .notion.rate_limiter import NotionOptimizedUploader


def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default logger
    
    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=Config.LOG_LEVEL
    )
    
    # File logging
    if Config.LOG_FILE:
        logger.add(
            Config.LOG_FILE,
            rotation="10 MB",
            retention="7 days",
            level=Config.LOG_LEVEL
        )


async def test_collection(exchanges: list = None, limit: int = 2):
    """Test data collection from specified exchanges"""
    
    # Use test exchanges if not specified
    if not exchanges:
        exchanges = ["binance", "coinbase"][:limit]
    
    logger.info(f"Testing data collection from: {exchanges}")
    
    # Create manager with specific exchanges
    manager = ExchangeCollectorManager(exchanges)
    
    # Collect data
    results = await manager.collect_all(max_concurrent=2)
    
    # Print summary
    summary = manager.get_summary()
    logger.info("Collection Summary:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    # Print errors if any
    errors = manager.get_errors_summary()
    if errors:
        logger.warning("Errors encountered:")
        for exchange, error_list in errors.items():
            logger.warning(f"  {exchange}: {len(error_list)} errors")
            for error in error_list[:2]:  # Show first 2 errors
                logger.warning(f"    - {error['type']}: {error['error']}")
    
    # Save sample data to file
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    for exchange_name, data in results.items():
        output_file = output_dir / f"{exchange_name}_sample_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to dict for JSON serialization
        data_dict = {
            "exchange": data.exchange,
            "collection_timestamp": data.collection_timestamp.isoformat(),
            "ticker_count": len(data.tickers),
            "orderbook_count": len(data.orderbooks),
            "trades_count": len(data.trades),
            "ohlcv_count": len(data.ohlcv),
            "errors_count": len(data.errors),
            "sample_ticker": data.tickers[0].model_dump() if data.tickers else None,
            "sample_orderbook": {
                "symbol": data.orderbooks[0].symbol,
                "spread": data.orderbooks[0].spread,
                "bid_depth": data.orderbooks[0].bid_depth,
                "ask_depth": data.orderbooks[0].ask_depth,
                "bids_count": len(data.orderbooks[0].bids),
                "asks_count": len(data.orderbooks[0].asks)
            } if data.orderbooks else None
        }
        
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2)
            
        logger.info(f"Sample data saved to: {output_file}")
    
    return results


async def collect_all_exchanges(limit: int = None, upload_to_notion: bool = True, direct_upload: bool = False):
    """Collect data from all available exchanges"""
    
    logger.info("Starting full data collection")
    
    # Create manager
    manager = ExchangeCollectorManager()
    
    if limit:
        # Limit number of exchanges
        manager.exchanges = manager.exchanges[:limit]
    
    logger.info(f"Will collect from {len(manager.exchanges)} exchanges")
    
    # Collect data
    results = await manager.collect_all()
    
    # Print summary
    summary = manager.get_summary()
    logger.info("Collection Summary:")
    for key, value in summary.items():
        logger.info(f"  {key}: {value}")
    
    # Upload to Notion if enabled
    if upload_to_notion and Config.NOTION_API_KEY:
        if direct_upload:
            logger.info("Uploading data directly to existing Notion database...")
            uploader = SimpleNotionUploader()
            upload_results = await uploader.upload_all_exchanges(results)
            logger.info(f"Simple upload complete: {upload_results['totals']['total_records']} records")
        else:
            logger.info("Uploading CSV files to Notion...")
            uploader = NotionUploader()
            
            # Setup database schema if needed
            await uploader.setup_notion_database()
            
            # Process and upload all data
            upload_results = await uploader.process_all_exchanges(results)
            
            logger.info(f"CSV upload complete. Daily summary: {upload_results.get('daily_summary', {}).get('url', 'N/A')}")
    
    return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Cryptocurrency Data Collector")
    parser.add_argument(
        "--exchanges",
        type=str,
        help="Comma-separated list of exchanges to collect from"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (collect from 2 exchanges only)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of exchanges to collect from"
    )
    parser.add_argument(
        "--priority-only",
        action="store_true",
        help="Collect from priority exchanges only"
    )
    parser.add_argument(
        "--direct-upload",
        action="store_true",
        help="Upload data directly to Notion databases (not CSV files)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Validate configuration
    try:
        if not args.test:  # Only validate Notion config if not in test mode
            Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("For testing without Notion, use: python -m src.main --test")
        sys.exit(1)
    
    # Run collection
    try:
        if args.test:
            # Test mode
            exchanges = args.exchanges.split(",") if args.exchanges else None
            asyncio.run(test_collection(exchanges))
            
        elif args.priority_only:
            # Priority exchanges only
            manager = ExchangeCollectorManager()
            results = asyncio.run(manager.collect_from_priority_exchanges(limit=args.limit or 10))
            
            # Upload to Notion
            if Config.NOTION_API_KEY:
                if args.direct_upload:
                    # Optimized upload with rate limiting for GitHub Actions
                    from notion_client import AsyncClient
                    notion_client = AsyncClient(auth=Config.NOTION_API_KEY)
                    uploader = NotionOptimizedUploader(notion_client, target_rps=0.5)
                    
                    # Convert results to format expected by optimized uploader
                    crypto_data_list = [{"exchange": name, "data": data} for name, data in results.items()]
                    upload_results = asyncio.run(uploader.upload_crypto_data(crypto_data_list))
                    
                    logger.info(f"Optimized upload complete: {upload_results['summary']['successful']}/{upload_results['summary']['total_exchanges']} exchanges")
                    logger.info(f"Total duration: {upload_results['summary']['duration_seconds']:.1f}s")
                    logger.info(f"Rate limiting stats: {upload_results['rate_limiting']['utilization_percent']:.1f}% utilization")
                else:
                    # CSV file upload
                    uploader = NotionUploader()
                    asyncio.run(uploader.setup_notion_database())
                    upload_results = asyncio.run(uploader.process_all_exchanges(results))
                    logger.info(f"CSV upload complete: {upload_results.get('daily_summary', {}).get('url', 'N/A')}")
            
        else:
            # Full collection
            exchanges = args.exchanges.split(",") if args.exchanges else None
            if exchanges:
                manager = ExchangeCollectorManager(exchanges)
                asyncio.run(manager.collect_all())
            else:
                asyncio.run(collect_all_exchanges(
                    limit=args.limit, 
                    upload_to_notion=True,
                    direct_upload=args.direct_upload
                ))
                
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()