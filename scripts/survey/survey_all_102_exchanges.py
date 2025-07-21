#!/usr/bin/env python3
"""
全102取引所の完全調査スクリプト
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from explore_all_exchanges import ExchangeExplorer, save_to_notion
from loguru import logger


async def main():
    """全102取引所を調査してNotionに保存"""
    logger.info("🚀 全102取引所の完全調査を開始します")
    logger.info("⏱️  この処理には10-20分程度かかる可能性があります")
    
    # 調査実行
    explorer = ExchangeExplorer()
    
    # 全102取引所を調査（limit=None）
    results = await explorer.explore_all_exchanges(limit=None)
    
    # サマリー表示
    summary = explorer.generate_summary()
    logger.info("\n" + "="*60)
    logger.info("📊 調査結果サマリー")
    logger.info("="*60)
    logger.info(f"調査取引所数: {summary['total_exchanges']}")
    logger.info(f"成功: {summary['successful']}")
    logger.info(f"失敗: {summary['failed']}")
    logger.info("")
    logger.info("データ取得可能性:")
    for data_type, count in summary['data_availability'].items():
        logger.info(f"  {data_type}: {count}取引所")
    
    # Notionに保存
    logger.info("\n📤 Notionへの保存を開始します...")
    await save_to_notion(explorer)
    
    logger.success("\n✅ 全102取引所の調査とNotion保存が完了しました！")
    logger.info("👉 Notionデータベースを確認してください")


if __name__ == "__main__":
    asyncio.run(main())