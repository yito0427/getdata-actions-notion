#!/usr/bin/env python3
"""
Real Data Upload Test - 実データが確実に保存されることを確認
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.manager import ExchangeCollectorManager
from src.notion.realdata_uploader import RealDataNotionUploader
from src.config import Config
from loguru import logger


async def test_real_data_upload():
    """実データアップロードのテスト"""
    
    # 環境変数確認
    if not Config.NOTION_API_KEY or not Config.NOTION_DATABASE_ID:
        logger.error("❌ NOTION_API_KEY と NOTION_DATABASE_ID を設定してください")
        return
    
    logger.info("🔍 実データ保存テスト開始")
    logger.info(f"📊 Database ID: {Config.NOTION_DATABASE_ID}")
    
    # 1つの取引所からテストデータを収集
    exchanges = ["binance"]
    manager = ExchangeCollectorManager(exchanges)
    
    logger.info("📥 Binanceからデータ収集中...")
    results = await manager.collect_all(max_concurrent=1)
    
    # 収集したデータの確認
    for exchange_name, data in results.items():
        logger.info(f"\n📊 {exchange_name}のデータ:")
        logger.info(f"  - ティッカー数: {len(data.tickers)}")
        logger.info(f"  - オーダーブック数: {len(data.orderbooks)}")
        
        # 最初のティッカーデータを表示
        if data.tickers:
            ticker = data.tickers[0]
            logger.info(f"\n🎯 サンプルティッカー: {ticker.symbol}")
            logger.info(f"  - 価格: ${ticker.last:.2f}" if ticker.last else "  - 価格: N/A")
            logger.info(f"  - 買値: ${ticker.bid:.2f}" if ticker.bid else "  - 買値: N/A")
            logger.info(f"  - 売値: ${ticker.ask:.2f}" if ticker.ask else "  - 売値: N/A")
            logger.info(f"  - 24時間高値: ${ticker.high:.2f}" if ticker.high else "  - 24時間高値: N/A")
            logger.info(f"  - 24時間安値: ${ticker.low:.2f}" if ticker.low else "  - 24時間安値: N/A")
            logger.info(f"  - 取引量: {ticker.base_volume:.4f}" if ticker.base_volume else "  - 取引量: N/A")
            logger.info(f"  - 変動率: {ticker.percentage:.2f}%" if ticker.percentage else "  - 変動率: N/A")
    
    # RealDataNotionUploaderでアップロード
    logger.info("\n📤 Notionへ実データをアップロード中...")
    uploader = RealDataNotionUploader()
    
    upload_results = await uploader.upload_all_exchanges(results)
    
    # 結果表示
    logger.info("\n" + "="*60)
    logger.info("📊 アップロード結果:")
    logger.info("="*60)
    
    totals = upload_results["totals"]
    logger.info(f"✅ 成功した取引所: {totals['exchanges_successful']}/{totals['exchanges_processed']}")
    logger.info(f"📈 保存したティッカー: {totals['total_tickers']}件")
    logger.info(f"📊 保存したオーダーブック: {totals['total_orderbooks']}件")
    logger.info(f"💾 合計保存レコード: {totals['total_records']}件")
    
    # 各取引所の詳細
    for exchange_name, result in upload_results["exchanges"].items():
        logger.info(f"\n🏢 {exchange_name}:")
        logger.info(f"  - ステータス: {result['status']}")
        logger.info(f"  - ティッカー: {result.get('tickers_uploaded', 0)}件")
        logger.info(f"  - オーダーブック: {result.get('orderbooks_uploaded', 0)}件")
        logger.info(f"  - 処理時間: {result.get('duration', 0):.1f}秒")
    
    logger.info("\n" + "="*60)
    logger.info("✅ テスト完了!")
    logger.info("👉 Notionデータベースを確認してください")
    logger.info("   実際の価格データがJSON形式で保存されているはずです")
    logger.info("💡 CSVエクスポート: python -m src.utils.notion_to_csv")


if __name__ == "__main__":
    asyncio.run(test_real_data_upload())