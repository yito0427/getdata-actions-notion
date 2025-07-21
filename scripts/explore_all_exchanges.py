#!/usr/bin/env python3
"""
102取引所のデータ探索スクリプト
各取引所から取得可能なデータ種別を調査し、Notionに記録
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.base import BaseExchangeCollector
from src.notion.realdata_uploader import RealDataNotionUploader
from src.config import Config
from loguru import logger
import ccxt.async_support as ccxt


class ExchangeExplorer:
    """全取引所のデータ取得可能性を調査"""
    
    def __init__(self):
        self.exchanges = ccxt.exchanges  # 全102取引所
        self.results = {}
        
    async def explore_exchange(self, exchange_name: str) -> dict:
        """1つの取引所を調査"""
        result = {
            "exchange": exchange_name,
            "status": "pending",
            "has_public_api": False,
            "available_data": {
                "ticker": False,
                "orderbook": False,
                "trades": False,
                "ohlcv": False,
                "markets": False
            },
            "sample_symbols": [],
            "total_markets": 0,
            "api_features": {},
            "errors": []
        }
        
        exchange = None
        try:
            # 取引所インスタンスを作成
            exchange_class = getattr(ccxt, exchange_name)
            exchange = exchange_class({
                'enableRateLimit': True,
                'rateLimit': 1000,  # 1秒待機
                'timeout': 30000    # 30秒タイムアウト
            })
            
            # マーケット情報を取得
            try:
                markets = await exchange.load_markets()
                result["has_public_api"] = True
                result["total_markets"] = len(markets)
                result["sample_symbols"] = list(markets.keys())[:5]  # 最初の5シンボル
                
                # API機能を確認
                result["api_features"] = {
                    "fetchTicker": exchange.has.get('fetchTicker', False),
                    "fetchTickers": exchange.has.get('fetchTickers', False),
                    "fetchOrderBook": exchange.has.get('fetchOrderBook', False),
                    "fetchTrades": exchange.has.get('fetchTrades', False),
                    "fetchOHLCV": exchange.has.get('fetchOHLCV', False),
                    "timeframes": list(exchange.timeframes.keys()) if hasattr(exchange, 'timeframes') else []
                }
                
                # 各データタイプをテスト
                if result["sample_symbols"] and result["api_features"]["fetchTicker"]:
                    symbol = result["sample_symbols"][0]
                    
                    # Ticker
                    try:
                        ticker = await exchange.fetch_ticker(symbol)
                        if ticker:
                            result["available_data"]["ticker"] = True
                            result["ticker_sample"] = {
                                "symbol": ticker.get('symbol'),
                                "last": ticker.get('last'),
                                "bid": ticker.get('bid'),
                                "ask": ticker.get('ask'),
                                "volume": ticker.get('baseVolume')
                            }
                    except Exception as e:
                        result["errors"].append(f"Ticker error: {str(e)}")
                    
                    # OrderBook
                    if result["api_features"]["fetchOrderBook"]:
                        try:
                            orderbook = await exchange.fetch_order_book(symbol, limit=10)
                            if orderbook:
                                result["available_data"]["orderbook"] = True
                                result["orderbook_sample"] = {
                                    "bids": len(orderbook.get('bids', [])),
                                    "asks": len(orderbook.get('asks', [])),
                                    "spread": orderbook['asks'][0][0] - orderbook['bids'][0][0] if orderbook.get('bids') and orderbook.get('asks') else None
                                }
                        except Exception as e:
                            result["errors"].append(f"OrderBook error: {str(e)}")
                    
                    # Trades
                    if result["api_features"]["fetchTrades"]:
                        try:
                            trades = await exchange.fetch_trades(symbol, limit=10)
                            if trades:
                                result["available_data"]["trades"] = True
                                result["trades_count"] = len(trades)
                        except Exception as e:
                            result["errors"].append(f"Trades error: {str(e)}")
                    
                    # OHLCV
                    if result["api_features"]["fetchOHLCV"] and result["api_features"]["timeframes"]:
                        try:
                            timeframe = result["api_features"]["timeframes"][0]
                            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=10)
                            if ohlcv:
                                result["available_data"]["ohlcv"] = True
                                result["ohlcv_timeframes"] = result["api_features"]["timeframes"]
                        except Exception as e:
                            result["errors"].append(f"OHLCV error: {str(e)}")
                
                result["available_data"]["markets"] = True
                result["status"] = "success"
                
            except Exception as e:
                result["errors"].append(f"Market loading error: {str(e)}")
                result["status"] = "failed"
            
        except Exception as e:
            result["errors"].append(f"Exchange initialization error: {str(e)}")
            result["status"] = "error"
        
        finally:
            if exchange:
                await exchange.close()
        
        return result
    
    async def explore_all_exchanges(self, limit: int = None):
        """全取引所を調査"""
        exchanges_to_test = self.exchanges[:limit] if limit else self.exchanges
        
        logger.info(f"🔍 {len(exchanges_to_test)}の取引所を調査開始")
        
        # バッチ処理（同時実行数を制限）
        batch_size = 5
        for i in range(0, len(exchanges_to_test), batch_size):
            batch = exchanges_to_test[i:i+batch_size]
            tasks = [self.explore_exchange(exchange) for exchange in batch]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for exchange, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    self.results[exchange] = {
                        "exchange": exchange,
                        "status": "error",
                        "errors": [str(result)]
                    }
                else:
                    self.results[exchange] = result
                    
                # ログ出力
                if result and not isinstance(result, Exception):
                    status_icon = "✅" if result["status"] == "success" else "❌"
                    data_types = [k for k, v in result["available_data"].items() if v]
                    logger.info(f"{status_icon} {exchange}: {len(data_types)}種類のデータ取得可能")
            
            # レート制限対策
            await asyncio.sleep(2)
        
        return self.results
    
    def generate_summary(self):
        """調査結果のサマリーを生成"""
        summary = {
            "total_exchanges": len(self.results),
            "successful": len([r for r in self.results.values() if r["status"] == "success"]),
            "failed": len([r for r in self.results.values() if r["status"] != "success"]),
            "data_availability": {
                "ticker": len([r for r in self.results.values() if r.get("available_data", {}).get("ticker")]),
                "orderbook": len([r for r in self.results.values() if r.get("available_data", {}).get("orderbook")]),
                "trades": len([r for r in self.results.values() if r.get("available_data", {}).get("trades")]),
                "ohlcv": len([r for r in self.results.values() if r.get("available_data", {}).get("ohlcv")])
            },
            "top_exchanges": []
        }
        
        # データ種類が多い順にソート
        sorted_exchanges = sorted(
            self.results.items(),
            key=lambda x: sum(x[1].get("available_data", {}).values()),
            reverse=True
        )
        
        summary["top_exchanges"] = [
            {
                "name": ex[0],
                "markets": ex[1].get("total_markets", 0),
                "data_types": sum(ex[1].get("available_data", {}).values())
            }
            for ex in sorted_exchanges[:20]
        ]
        
        return summary


async def save_to_notion(explorer: ExchangeExplorer):
    """調査結果をNotionに保存"""
    if not Config.NOTION_API_KEY or not Config.NOTION_DATABASE_ID:
        logger.error("Notion認証情報が設定されていません")
        return
    
    uploader = RealDataNotionUploader()
    client = uploader.client
    
    # サマリーページを作成
    summary = explorer.generate_summary()
    
    title = f"📊 102取引所データ調査結果 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Data Type": {"select": {"name": "Exchange Survey"}},
        "Collection Time": {"date": {"start": datetime.now().isoformat()}},
        "Total Tickers": {"number": summary["data_availability"]["ticker"]},
        "Total OrderBooks": {"number": summary["data_availability"]["orderbook"]},
        "Record Count": {"number": summary["successful"]},
        "Status": {"select": {"name": "Completed"}}
    }
    
    # 詳細な調査結果をJSON形式で保存
    children = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"text": {"content": "🌍 102取引所データ調査レポート"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {
                        "content": f"調査完了: {summary['total_exchanges']}取引所\n"
                                  f"成功: {summary['successful']}取引所\n"
                                  f"失敗: {summary['failed']}取引所"
                    }
                }]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📈 データ取得可能性"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "text": {
                        "content": f"Ticker: {summary['data_availability']['ticker']}取引所\n"
                                  f"OrderBook: {summary['data_availability']['orderbook']}取引所\n"
                                  f"Trades: {summary['data_availability']['trades']}取引所\n"
                                  f"OHLCV: {summary['data_availability']['ohlcv']}取引所"
                    }
                }]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "🏆 トップ20取引所"}}]}
        },
        {
            "object": "block",
            "type": "table",
            "table": {
                "table_width": 3,
                "has_column_header": True,
                "has_row_header": False,
                "children": [
                    {
                        "object": "block",
                        "type": "table_row",
                        "table_row": {
                            "cells": [
                                [{"text": {"content": "取引所"}}],
                                [{"text": {"content": "マーケット数"}}],
                                [{"text": {"content": "データ種類"}}]
                            ]
                        }
                    }
                ] + [
                    {
                        "object": "block",
                        "type": "table_row",
                        "table_row": {
                            "cells": [
                                [{"text": {"content": ex["name"]}}],
                                [{"text": {"content": str(ex["markets"])}}],
                                [{"text": {"content": f"{ex['data_types']}種類"}}]
                            ]
                        }
                    }
                    for ex in summary["top_exchanges"][:10]
                ]
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📋 全調査結果（JSON）"}}]}
        },
        {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "text": {"content": json.dumps(explorer.results, ensure_ascii=False, indent=2)[:2000]}
                }],
                "language": "json",
                "caption": [{"text": {"content": "全102取引所の調査結果（最初の2000文字）"}}]
            }
        }
    ]
    
    try:
        page = await client.pages.create(
            parent={"database_id": Config.NOTION_DATABASE_ID},
            properties=properties,
            children=children
        )
        logger.success(f"✅ 調査結果をNotionに保存しました")
        
        # 各取引所の詳細ページも作成（全取引所）
        sorted_exchanges = sorted(
            explorer.results.items(),
            key=lambda x: sum(x[1].get("available_data", {}).values()),
            reverse=True
        )
        
        logger.info(f"\n📝 各取引所の詳細をNotionに保存中...")
        for i, (exchange_name, data) in enumerate(sorted_exchanges):
            await save_exchange_detail(uploader, exchange_name, data)
            logger.info(f"  [{i+1}/{len(sorted_exchanges)}] {exchange_name}")
            await asyncio.sleep(0.5)  # レート制限
        
    except Exception as e:
        logger.error(f"Notion保存エラー: {e}")


async def save_exchange_detail(uploader: RealDataNotionUploader, exchange_name: str, data: dict):
    """個別取引所の詳細をNotionに保存（1取引所1レコード）"""
    client = uploader.client
    
    # タイトルに主要情報を含める
    data_types = [k for k, v in data.get("available_data", {}).items() if v]
    title = f"🏢 {exchange_name} | {data.get('total_markets', 0)} markets | {len(data_types)} data types"
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "Data Type": {"select": {"name": "Exchange Analysis"}},
        "Exchange": {"select": {"name": exchange_name}},
        "Collection Time": {"date": {"start": datetime.now().isoformat()}},
        "Total Tickers": {"number": data.get("total_markets", 0)},  # マーケット数を保存
        "Record Count": {"number": len(data_types)},  # 取得可能なデータ種類数
        "Status": {"select": {"name": "Success" if data["status"] == "success" else "Failed"}}
    }
    
    # 詳細情報を構造化して表示
    children = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {"rich_text": [{"text": {"content": f"🏢 {exchange_name} 取引所分析レポート"}}]}
        },
        {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{
                    "text": {
                        "content": f"✅ 公開API: {'利用可能' if data.get('has_public_api') else '利用不可'}\n"
                                  f"📊 総マーケット数: {data.get('total_markets', 0)}\n"
                                  f"🔧 取得可能データ種類: {len(data_types)}種類"
                    }
                }],
                "icon": {"emoji": "📊"}
            }
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📋 取得可能なデータ種別"}}]}
        }
    ]
    
    # データ種別の詳細
    if data.get("available_data"):
        data_details = []
        
        # Ticker情報
        if data["available_data"].get("ticker"):
            ticker_info = "✅ **Ticker (価格情報)**\n"
            if data.get("ticker_sample"):
                sample = data["ticker_sample"]
                ticker_info += f"  - シンボル: {sample.get('symbol')}\n"
                ticker_info += f"  - 最終価格: ${sample.get('last')}\n"
                ticker_info += f"  - 買値/売値: ${sample.get('bid')} / ${sample.get('ask')}\n"
                ticker_info += f"  - 取引量: {sample.get('volume')}\n"
            data_details.append(ticker_info)
        else:
            data_details.append("❌ **Ticker**: 取得不可\n")
        
        # OrderBook情報
        if data["available_data"].get("orderbook"):
            ob_info = "✅ **OrderBook (板情報)**\n"
            if data.get("orderbook_sample"):
                sample = data["orderbook_sample"]
                ob_info += f"  - 買い注文数: {sample.get('bids')}件\n"
                ob_info += f"  - 売り注文数: {sample.get('asks')}件\n"
                ob_info += f"  - スプレッド: {sample.get('spread')}\n"
            data_details.append(ob_info)
        else:
            data_details.append("❌ **OrderBook**: 取得不可\n")
        
        # Trades情報
        if data["available_data"].get("trades"):
            trades_info = f"✅ **Trades (約定履歴)**: {data.get('trades_count', 0)}件取得可能\n"
            data_details.append(trades_info)
        else:
            data_details.append("❌ **Trades**: 取得不可\n")
        
        # OHLCV情報
        if data["available_data"].get("ohlcv"):
            ohlcv_info = "✅ **OHLCV (ローソク足)**\n"
            if data.get("ohlcv_timeframes"):
                ohlcv_info += f"  - 対応時間軸: {', '.join(data['ohlcv_timeframes'][:10])}\n"
            data_details.append(ohlcv_info)
        else:
            data_details.append("❌ **OHLCV**: 取得不可\n")
        
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"text": {"content": "\n".join(data_details)}}]
            }
        })
    
    # API機能の詳細
    if data.get("api_features"):
        children.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🔧 API機能詳細"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "text": {
                            "content": f"fetchTicker: {'✅' if data['api_features'].get('fetchTicker') else '❌'}\n"
                                      f"fetchTickers: {'✅' if data['api_features'].get('fetchTickers') else '❌'}\n"
                                      f"fetchOrderBook: {'✅' if data['api_features'].get('fetchOrderBook') else '❌'}\n"
                                      f"fetchTrades: {'✅' if data['api_features'].get('fetchTrades') else '❌'}\n"
                                      f"fetchOHLCV: {'✅' if data['api_features'].get('fetchOHLCV') else '❌'}"
                        }
                    }]
                }
            }
        ])
    
    # サンプルシンボル
    if data.get("sample_symbols"):
        children.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "💱 取扱通貨ペア（サンプル）"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "text": {"content": ", ".join(data["sample_symbols"][:20])}
                    }]
                }
            }
        ])
    
    # エラー情報
    if data.get("errors"):
        children.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "⚠️ エラー情報"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "text": {"content": "\n".join(data["errors"][:5])}  # 最初の5エラーのみ
                    }]
                }
            }
        ])
    
    # 完全なJSON データ
    children.extend([
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📄 完全な調査データ（JSON）"}}]}
        },
        {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "text": {"content": json.dumps(data, ensure_ascii=False, indent=2)[:2000]}
                }],
                "language": "json",
                "caption": [{"text": {"content": f"{exchange_name}の完全な調査結果"}}]
            }
        }
    ])
    
    try:
        await client.pages.create(
            parent={"database_id": Config.NOTION_DATABASE_ID},
            properties=properties,
            children=children
        )
        logger.info(f"✅ {exchange_name}の詳細分析を保存（1レコード）")
    except Exception as e:
        logger.error(f"{exchange_name}の保存エラー: {e}")


async def main():
    """メイン実行関数"""
    logger.info("🚀 102取引所のデータ調査を開始します")
    
    # 調査実行
    explorer = ExchangeExplorer()
    
    # テスト用に最初の20取引所のみ（全102取引所は時間がかかる）
    # 全取引所を調査する場合は limit=None に変更
    results = await explorer.explore_all_exchanges(limit=20)
    
    # 結果をファイルに保存
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "exchange_survey.json", "w", encoding="utf-8") as f:
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
    await save_to_notion(explorer)
    
    logger.success("✅ 調査完了！")


if __name__ == "__main__":
    asyncio.run(main())