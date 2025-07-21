#!/usr/bin/env python3
"""
調査結果をNotionにアップロードする専用スクリプト
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.notion.realdata_uploader import RealDataNotionUploader
from src.config import Config
from loguru import logger


async def upload_survey_results():
    """保存済みの調査結果をNotionにアップロード"""
    
    # JSONファイルを読み込み
    json_path = Path("output/exchange_survey_parallel.json")
    if not json_path.exists():
        logger.error("調査結果ファイルが見つかりません")
        return
    
    with open(json_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    
    logger.info(f"📊 {len(results)}取引所の調査結果を読み込みました")
    
    # Notion設定確認
    if not Config.NOTION_API_KEY or not Config.NOTION_DATABASE_ID:
        logger.error("Notion認証情報が設定されていません")
        return
    
    uploader = RealDataNotionUploader()
    client = uploader.client
    
    # 統計情報を計算
    successful = sum(1 for r in results.values() if r["status"] == "success")
    failed = len(results) - successful
    
    data_availability = {
        "ticker": sum(1 for r in results.values() if r.get("available_data", {}).get("ticker")),
        "orderbook": sum(1 for r in results.values() if r.get("available_data", {}).get("orderbook")),
        "trades": sum(1 for r in results.values() if r.get("available_data", {}).get("trades")),
        "ohlcv": sum(1 for r in results.values() if r.get("available_data", {}).get("ohlcv"))
    }
    
    logger.info(f"✅ 成功: {successful}取引所")
    logger.info(f"❌ 失敗: {failed}取引所")
    
    # 各取引所のレコードを作成
    uploaded = 0
    errors = 0
    
    # データ種類でソート（多い順）
    sorted_exchanges = sorted(
        results.items(),
        key=lambda x: sum(x[1].get("available_data", {}).values()),
        reverse=True
    )
    
    for i, (exchange_name, data) in enumerate(sorted_exchanges):
        try:
            logger.info(f"[{i+1}/{len(results)}] {exchange_name} をアップロード中...")
            
            data_types = [k for k, v in data.get("available_data", {}).items() if v]
            title = f"🏢 {exchange_name} | {data.get('total_markets', 0)} markets | {len(data_types)} types"
            
            # Notionページのプロパティ（シンプルに）
            properties = {
                "Name": {"title": [{"text": {"content": title}}]},
                "Data Type": {"select": {"name": "Exchange Survey"}},
                "Exchange": {"select": {"name": exchange_name}},
                "Collection Time": {"date": {"start": datetime.now().isoformat()}},
                "Total Tickers": {"number": data.get("total_markets", 0)},
                "Record Count": {"number": len(data_types)},
                "Status": {"select": {"name": "Success" if data["status"] == "success" else "Failed"}}
            }
            
            # ページコンテンツ
            content_text = f"📊 {exchange_name} 取引所調査結果\n\n"
            content_text += f"✅ 公開API: {'利用可能' if data.get('has_public_api') else '利用不可'}\n"
            content_text += f"📈 総マーケット数: {data.get('total_markets', 0)}\n"
            content_text += f"🔧 取得可能データ: {', '.join(data_types) if data_types else 'なし'}\n\n"
            
            if data.get("sample_symbols"):
                content_text += f"💱 取扱通貨ペア例:\n{', '.join(data['sample_symbols'][:10])}\n\n"
            
            # データ詳細
            if data.get("available_data"):
                content_text += "📋 データ取得可能性:\n"
                for dtype, available in data["available_data"].items():
                    content_text += f"{'✅' if available else '❌'} {dtype}\n"
                content_text += "\n"
            
            # API機能
            if data.get("api_features"):
                content_text += "🔧 API機能:\n"
                for feature, available in data["api_features"].items():
                    if feature != "timeframes" and isinstance(available, bool):
                        content_text += f"{'✅' if available else '❌'} {feature}\n"
                
                if data["api_features"].get("timeframes"):
                    content_text += f"\n⏱️ 対応時間軸: {', '.join(data['api_features']['timeframes'][:10])}"
            
            children = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": content_text}}]}
                }
            ]
            
            # エラー情報
            if data.get("errors"):
                children.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": f"⚠️ エラー: {data['errors'][0][:200]}"}}],
                        "icon": {"emoji": "⚠️"}
                    }
                })
            
            # Notionに保存
            await client.pages.create(
                parent={"database_id": Config.NOTION_DATABASE_ID},
                properties=properties,
                children=children
            )
            
            uploaded += 1
            await asyncio.sleep(0.3)  # レート制限対策
            
        except Exception as e:
            logger.error(f"❌ {exchange_name} のアップロード失敗: {e}")
            errors += 1
    
    logger.success(f"\n✅ アップロード完了!")
    logger.info(f"📊 成功: {uploaded}件")
    logger.info(f"❌ エラー: {errors}件")
    logger.info(f"💾 合計: {len(results)}取引所")


if __name__ == "__main__":
    asyncio.run(upload_survey_results())