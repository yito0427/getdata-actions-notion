#!/usr/bin/env python3
"""
調査結果を詳細情報（APIサンプルコード・実データ）付きでNotionにアップロード
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


def generate_api_sample_code(exchange_name: str, data: dict) -> str:
    """各取引所のAPIサンプルコードを生成"""
    
    sample_code = f"""# {exchange_name} API利用例

import ccxt

# 取引所インスタンスを作成
exchange = ccxt.{exchange_name}()

# マーケット情報を読み込み
markets = exchange.load_markets()
print(f"利用可能なマーケット数: {{len(markets)}}")
"""
    
    # サンプルシンボル
    symbol = data.get("sample_symbols", ["BTC/USDT"])[0] if data.get("sample_symbols") else "BTC/USDT"
    
    # Ticker取得例
    if data.get("available_data", {}).get("ticker") and data.get("api_features", {}).get("fetchTicker"):
        sample_code += f"""
# Ticker（価格情報）を取得
ticker = exchange.fetch_ticker('{symbol}')
print(f"最終価格: ${{ticker['last']}}")
print(f"24時間高値: ${{ticker['high']}}")
print(f"24時間安値: ${{ticker['low']}}")
print(f"24時間取引量: {{ticker['baseVolume']}}")
"""
    
    # OrderBook取得例
    if data.get("available_data", {}).get("orderbook") and data.get("api_features", {}).get("fetchOrderBook"):
        sample_code += f"""
# OrderBook（板情報）を取得
orderbook = exchange.fetch_order_book('{symbol}', limit=10)
print(f"最良買値: ${{orderbook['bids'][0][0] if orderbook['bids'] else 'N/A'}}")
print(f"最良売値: ${{orderbook['asks'][0][0] if orderbook['asks'] else 'N/A'}}")
print(f"買い注文数: {{len(orderbook['bids'])}}")
print(f"売り注文数: {{len(orderbook['asks'])}}")
"""
    
    # Trades取得例
    if data.get("available_data", {}).get("trades") and data.get("api_features", {}).get("fetchTrades"):
        sample_code += f"""
# Trades（約定履歴）を取得
trades = exchange.fetch_trades('{symbol}', limit=10)
for trade in trades[:3]:
    print(f"約定: ${{trade['price']}} x {{trade['amount']}} ({{trade['side']}})")
"""
    
    # OHLCV取得例
    if data.get("available_data", {}).get("ohlcv") and data.get("api_features", {}).get("fetchOHLCV"):
        timeframe = data.get("api_features", {}).get("timeframes", ["1h"])[0] if data.get("api_features", {}).get("timeframes") else "1h"
        sample_code += f"""
# OHLCV（ローソク足）を取得
ohlcv = exchange.fetch_ohlcv('{symbol}', '{timeframe}', limit=10)
for candle in ohlcv[-3:]:  # 最新3本
    timestamp = exchange.iso8601(candle[0])
    print(f"{{timestamp}} O:${{candle[1]}} H:${{candle[2]}} L:${{candle[3]}} C:${{candle[4]}} V:{{candle[5]}}")
"""
    
    return sample_code


def format_actual_data(data: dict) -> str:
    """実際に取得したデータをフォーマット"""
    
    output = "📊 実際に取得したデータ（サンプル）\n\n"
    
    # Ticker データ
    if data.get("ticker_sample"):
        ticker = data["ticker_sample"]
        output += "💹 **Ticker データ**\n"
        output += f"• シンボル: {ticker.get('symbol', 'N/A')}\n"
        output += f"• 最終価格: ${ticker.get('last', 'N/A')}\n"
        output += f"• 買値/売値: ${ticker.get('bid', 'N/A')} / ${ticker.get('ask', 'N/A')}\n"
        output += f"• 24時間取引量: {ticker.get('volume', 'N/A')}\n\n"
    
    # OrderBook データ
    if data.get("orderbook_sample"):
        ob = data["orderbook_sample"]
        output += "📈 **OrderBook データ**\n"
        output += f"• 買い注文数: {ob.get('bids', 0)}件\n"
        output += f"• 売り注文数: {ob.get('asks', 0)}件\n"
        output += f"• スプレッド: ${ob.get('spread', 'N/A')}\n\n"
    
    # Trades データ
    if data.get("trades_count"):
        output += "📝 **Trades データ**\n"
        output += f"• 取得可能な約定履歴: {data['trades_count']}件\n\n"
    
    # OHLCV データ
    if data.get("ohlcv_timeframes"):
        output += "🕯️ **OHLCV データ**\n"
        output += f"• 対応時間軸: {', '.join(data['ohlcv_timeframes'][:10])}\n"
        if len(data['ohlcv_timeframes']) > 10:
            output += f"• 他 {len(data['ohlcv_timeframes']) - 10} 種類\n"
    
    return output


async def upload_detailed_survey():
    """詳細情報付きで調査結果をNotionにアップロード"""
    
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
    
    # 成功した取引所のみ処理
    successful_exchanges = {k: v for k, v in results.items() if v["status"] == "success"}
    
    logger.info(f"✅ {len(successful_exchanges)}の成功した取引所を処理します")
    
    uploaded = 0
    errors = 0
    
    # データ種類でソート（多い順）
    sorted_exchanges = sorted(
        successful_exchanges.items(),
        key=lambda x: sum(x[1].get("available_data", {}).values()),
        reverse=True
    )
    
    for i, (exchange_name, data) in enumerate(sorted_exchanges):
        try:
            logger.info(f"[{i+1}/{len(successful_exchanges)}] {exchange_name} の詳細情報をアップロード中...")
            
            data_types = [k for k, v in data.get("available_data", {}).items() if v]
            title = f"🏢 {exchange_name} | {data.get('total_markets', 0)} markets | {len(data_types)} types | API Guide"
            
            # Notionページのプロパティ
            properties = {
                "Name": {"title": [{"text": {"content": title}}]},
                "Data Type": {"select": {"name": "Exchange API Guide"}},
                "Exchange": {"select": {"name": exchange_name}},
                "Collection Time": {"date": {"start": datetime.now().isoformat()}},
                "Total Tickers": {"number": data.get("total_markets", 0)},
                "Record Count": {"number": len(data_types)},
                "Status": {"select": {"name": "Success"}}
            }
            
            # ページコンテンツ構築
            children = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"text": {"content": f"📚 {exchange_name} API完全ガイド"}}]}
                },
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{
                            "text": {
                                "content": f"✅ 公開API利用可能\n"
                                          f"📊 {data.get('total_markets', 0)} マーケット\n"
                                          f"🔧 {len(data_types)} 種類のデータ取得可能"
                            }
                        }],
                        "icon": {"emoji": "💡"}
                    }
                }
            ]
            
            # 基本情報セクション
            basic_info = f"**取引所概要:**\n"
            basic_info += f"• 取扱通貨ペア数: {data.get('total_markets', 0)}\n"
            basic_info += f"• 主要通貨ペア: {', '.join(data.get('sample_symbols', [])[:5])}\n"
            basic_info += f"• データ取得可能: {', '.join(data_types)}\n"
            
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": basic_info}}]}
            })
            
            # APIサンプルコード
            children.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "🔧 APIサンプルコード"}}]}
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"text": {"content": generate_api_sample_code(exchange_name, data)}}],
                        "language": "python",
                        "caption": [{"text": {"content": f"{exchange_name} API利用例（Python + CCXT）"}}]
                    }
                }
            ])
            
            # 実際のデータサンプル
            children.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "📊 実際に取得したデータ"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": format_actual_data(data)}}]}
                }
            ])
            
            # 生のJSONデータ（一部）
            if data.get("ticker_sample") or data.get("orderbook_sample"):
                sample_json = {
                    "exchange": exchange_name,
                    "timestamp": datetime.now().isoformat(),
                    "ticker": data.get("ticker_sample", {}),
                    "orderbook_summary": {
                        "bids": data.get("orderbook_sample", {}).get("bids", 0),
                        "asks": data.get("orderbook_sample", {}).get("asks", 0),
                        "spread": data.get("orderbook_sample", {}).get("spread")
                    } if data.get("orderbook_sample") else None,
                    "available_timeframes": data.get("ohlcv_timeframes", [])[:10]
                }
                
                children.extend([
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {"rich_text": [{"text": {"content": "🔍 生データサンプル（JSON）"}}]}
                    },
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"text": {"content": json.dumps(sample_json, ensure_ascii=False, indent=2)[:1500]}}],
                            "language": "json",
                            "caption": [{"text": {"content": "実際のAPIレスポンス例"}}]
                        }
                    }
                ])
            
            # API機能詳細
            if data.get("api_features"):
                api_details = "**利用可能なAPI機能:**\n"
                for feature, available in data["api_features"].items():
                    if feature != "timeframes" and isinstance(available, bool):
                        api_details += f"{'✅' if available else '❌'} {feature}\n"
                
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": api_details}}]}
                })
            
            # Notionに保存
            await client.pages.create(
                parent={"database_id": Config.NOTION_DATABASE_ID},
                properties=properties,
                children=children
            )
            
            uploaded += 1
            await asyncio.sleep(0.5)  # レート制限対策
            
        except Exception as e:
            logger.error(f"❌ {exchange_name} のアップロード失敗: {e}")
            errors += 1
            if errors > 5:
                logger.warning("エラーが多いため、レート制限を緩和します")
                await asyncio.sleep(2)
    
    logger.success(f"\n✅ 詳細情報付きアップロード完了!")
    logger.info(f"📊 成功: {uploaded}件")
    logger.info(f"❌ エラー: {errors}件")
    logger.info(f"💾 合計: {len(successful_exchanges)}取引所")


if __name__ == "__main__":
    asyncio.run(upload_detailed_survey())