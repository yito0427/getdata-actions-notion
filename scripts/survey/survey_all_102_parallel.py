#!/usr/bin/env python3
"""
全102取引所の並列調査スクリプト（高速版）
各取引所のAPIは独立しているため、並列実行で高速化
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from explore_all_exchanges import ExchangeExplorer, save_to_notion
from loguru import logger
import ccxt.async_support as ccxt


class ParallelExchangeExplorer(ExchangeExplorer):
    """並列実行版の取引所調査クラス"""
    
    async def explore_all_exchanges_parallel(self, max_concurrent: int = 20):
        """全取引所を並列で調査（最大同時実行数を制限）"""
        logger.info(f"🚀 {len(self.exchanges)}取引所の並列調査を開始（最大同時実行: {max_concurrent}）")
        
        start_time = time.time()
        
        # セマフォで同時実行数を制限
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def explore_with_semaphore(exchange_name):
            async with semaphore:
                logger.info(f"🔍 {exchange_name} 調査開始")
                result = await self.explore_exchange(exchange_name)
                
                # 結果をログ
                status_icon = "✅" if result["status"] == "success" else "❌"
                data_types = [k for k, v in result.get("available_data", {}).items() if v]
                logger.info(f"{status_icon} {exchange_name}: {len(data_types)}種類のデータ取得可能")
                
                return exchange_name, result
        
        # 全取引所を並列実行
        tasks = [explore_with_semaphore(exchange) for exchange in self.exchanges]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 結果を格納
        for item in results:
            if isinstance(item, Exception):
                logger.error(f"予期しないエラー: {item}")
            else:
                exchange_name, result = item
                self.results[exchange_name] = result
        
        elapsed_time = time.time() - start_time
        logger.success(f"✅ 調査完了！処理時間: {elapsed_time:.1f}秒")
        
        return self.results


async def save_to_notion_batch(explorer: ExchangeExplorer):
    """Notionへのバッチ保存（高速版）"""
    if not Config.NOTION_API_KEY or not Config.NOTION_DATABASE_ID:
        logger.error("Notion認証情報が設定されていません")
        return
    
    from src.notion.realdata_uploader import RealDataNotionUploader
    from src.config import Config
    
    uploader = RealDataNotionUploader()
    
    # サマリーページを作成
    summary = explorer.generate_summary()
    
    logger.info(f"📊 Notionへの保存を開始: {len(explorer.results)}取引所")
    
    # サマリーレポートを最初に作成
    await save_summary_report(uploader, explorer, summary)
    
    # 各取引所の詳細を並列で保存（Notion API制限を考慮）
    sorted_exchanges = sorted(
        explorer.results.items(),
        key=lambda x: sum(x[1].get("available_data", {}).values()),
        reverse=True
    )
    
    # Notion APIのレート制限を考慮してバッチ処理
    batch_size = 10  # 10件ずつ処理
    for i in range(0, len(sorted_exchanges), batch_size):
        batch = sorted_exchanges[i:i+batch_size]
        
        logger.info(f"📤 Notionへバッチ保存中... [{i+1}-{min(i+batch_size, len(sorted_exchanges))}/{len(sorted_exchanges)}]")
        
        # バッチ内は順次処理（Notion API制限のため）
        for exchange_name, data in batch:
            await save_exchange_detail_fast(uploader, exchange_name, data)
            await asyncio.sleep(0.3)  # Notion API制限対策
        
        # バッチ間で少し待機
        if i + batch_size < len(sorted_exchanges):
            await asyncio.sleep(1)
    
    logger.success(f"✅ 全{len(sorted_exchanges)}取引所のデータをNotionに保存完了！")


async def save_summary_report(uploader, explorer, summary):
    """サマリーレポートを保存"""
    client = uploader.client
    
    title = f"📊 102取引所並列調査結果 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Data Type": {"select": {"name": "Exchange Survey"}},
        "Collection Time": {"date": {"start": datetime.now().isoformat()}},
        "Total Tickers": {"number": summary["data_availability"]["ticker"]},
        "Total OrderBooks": {"number": summary["data_availability"]["orderbook"]},
        "Record Count": {"number": summary["successful"]},
        "Status": {"select": {"name": "Completed"}}
    }
    
    children = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"text": {"content": "🌍 102取引所データ調査レポート（並列実行版）"}}]}
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{
                    "text": {
                        "content": f"✅ 調査完了: {summary['total_exchanges']}取引所\n"
                                  f"✅ 成功: {summary['successful']}取引所\n"
                                  f"❌ 失敗: {summary['failed']}取引所"
                    }
                }],
                "icon": {"emoji": "🚀"}
            }
        }
    ]
    
    await client.pages.create(
        parent={"database_id": Config.NOTION_DATABASE_ID},
        properties=properties,
        children=children
    )


async def save_exchange_detail_fast(uploader, exchange_name: str, data: dict):
    """取引所詳細を保存（データ詳細含む）"""
    from src.config import Config
    client = uploader.client
    
    data_types = [k for k, v in data.get("available_data", {}).items() if v]
    title = f"🏢 {exchange_name} | {data.get('total_markets', 0)} markets | {len(data_types)} types"
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Data Type": {"select": {"name": "Exchange Analysis"}},
        "Exchange": {"select": {"name": exchange_name}},
        "Collection Time": {"date": {"start": datetime.now().isoformat()}},
        "Total Tickers": {"number": data.get("total_markets", 0)},
        "Record Count": {"number": len(data_types)},
        "Status": {"select": {"name": "Success" if data["status"] == "success" else "Failed"}}
    }
    
    # 詳細なデータ情報を構築
    children = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": f"📊 {exchange_name} データ詳細"}}]}
        }
    ]
    
    # 基本情報
    basic_info = f"✅ 公開API: {'利用可能' if data.get('has_public_api') else '利用不可'}\n"
    basic_info += f"📊 総マーケット数: {data.get('total_markets', 0)}\n"
    basic_info += f"🔧 取得可能データ種類: {len(data_types)}種類"
    
    children.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": [{"text": {"content": basic_info}}]}
    })
    
    # データ種別の詳細
    if data.get("available_data"):
        data_details = "📋 **取得可能データ:**\n"
        
        # Ticker
        if data["available_data"].get("ticker"):
            data_details += "✅ Ticker (価格情報)\n"
            if data.get("ticker_sample"):
                s = data["ticker_sample"]
                data_details += f"  • 最終価格: ${s.get('last')}\n"
                data_details += f"  • Bid/Ask: ${s.get('bid')} / ${s.get('ask')}\n"
                data_details += f"  • 取引量: {s.get('volume')}\n"
        else:
            data_details += "❌ Ticker\n"
        
        # OrderBook
        if data["available_data"].get("orderbook"):
            data_details += "✅ OrderBook (板情報)\n"
            if data.get("orderbook_sample"):
                ob = data["orderbook_sample"]
                data_details += f"  • 買い/売り注文: {ob.get('bids')}/{ob.get('asks')}件\n"
                data_details += f"  • スプレッド: {ob.get('spread')}\n"
        else:
            data_details += "❌ OrderBook\n"
        
        # Trades
        if data["available_data"].get("trades"):
            data_details += f"✅ Trades: {data.get('trades_count', 0)}件\n"
        else:
            data_details += "❌ Trades\n"
        
        # OHLCV
        if data["available_data"].get("ohlcv"):
            data_details += "✅ OHLCV (ローソク足)\n"
            if data.get("ohlcv_timeframes"):
                data_details += f"  • 時間軸: {', '.join(data['ohlcv_timeframes'][:5])}\n"
        else:
            data_details += "❌ OHLCV\n"
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": data_details}}]}
        })
    
    # サンプルシンボル
    if data.get("sample_symbols"):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {"content": f"💱 取扱通貨ペア例: {', '.join(data['sample_symbols'][:10])}"}
                }]
            }
        })
    
    # API機能
    if data.get("api_features"):
        api_info = "🔧 **API機能:**\n"
        for feature, available in data["api_features"].items():
            if feature != "timeframes":
                api_info += f"{'✅' if available else '❌'} {feature}\n"
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": api_info}}]}
        })
    
    # JSONデータ（最初の1000文字）
    children.append({
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{
                "text": {"content": json.dumps(data, ensure_ascii=False, indent=2)[:1000]}
            }],
            "language": "json",
            "caption": [{"text": {"content": "調査データ（抜粋）"}}]
        }
    })
    
    await client.pages.create(
        parent={"database_id": Config.NOTION_DATABASE_ID},
        properties=properties,
        children=children
    )


async def main():
    """メイン実行関数"""
    logger.info("🚀 全102取引所の並列調査を開始します")
    logger.info("⚡ 並列実行により処理時間を大幅に短縮します")
    
    # 調査実行
    explorer = ParallelExchangeExplorer()
    
    # 全102取引所を並列調査（最大20同時実行）
    results = await explorer.explore_all_exchanges_parallel(max_concurrent=20)
    
    # 結果をファイルに保存
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "exchange_survey_parallel.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
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
    
    # 必要なインポート
    from src.config import Config
    
    await save_to_notion_batch(explorer)
    
    logger.success("\n✅ 全102取引所の並列調査とNotion保存が完了しました！")
    logger.info("👉 Notionデータベースを確認してください")


if __name__ == "__main__":
    asyncio.run(main())