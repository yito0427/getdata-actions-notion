"""
Real Data Notion Uploader - 実際の仮想通貨データを確実に保存
このアップローダーは、価格、ボリューム、その他の実データをNotionに保存します
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from notion_client import AsyncClient
from loguru import logger

from ..models import CollectedData, TickerData, OrderBookData, TradeData
from ..config import Config


class RealDataNotionUploader:
    """実際の仮想通貨データをNotionデータベースに保存"""
    
    def __init__(self):
        """Initialize Notion client"""
        self.client = AsyncClient(auth=Config.NOTION_API_KEY)
        self.database_id = Config.NOTION_DATABASE_ID
        
    async def upload_ticker_with_real_data(self, ticker: TickerData) -> bool:
        """個別のティッカーデータを実データとともに保存"""
        try:
            # タイトルに実際の価格情報を含める
            price_str = f"${ticker.last:.2f}" if ticker.last else "N/A"
            change_str = f"{ticker.percentage:+.2f}%" if ticker.percentage else "0%"
            title = f"{ticker.exchange} {ticker.symbol} | {price_str} | {change_str}"
            
            # 実際のデータをJSONとして準備
            real_data = {
                "timestamp": ticker.timestamp.isoformat(),
                "exchange": ticker.exchange,
                "symbol": ticker.symbol,
                "prices": {
                    "last": ticker.last,
                    "bid": ticker.bid,
                    "ask": ticker.ask,
                    "high": ticker.high,
                    "low": ticker.low,
                    "open": ticker.open,
                    "close": ticker.close,
                    "vwap": ticker.vwap,
                    "previous_close": ticker.previous_close,
                    "change": ticker.change,
                    "percentage": ticker.percentage
                },
                "volumes": {
                    "base_volume": ticker.base_volume,
                    "quote_volume": ticker.quote_volume,
                    "bid_volume": ticker.bid_volume,
                    "ask_volume": ticker.ask_volume
                },
                "info": ticker.info if hasattr(ticker, 'info') else {}
            }
            
            # Notionページのプロパティ設定
            properties = {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Data Type": {
                    "select": {"name": "Real Ticker Data"}
                },
                "Exchange": {
                    "select": {"name": ticker.exchange}
                },
                "Collection Time": {
                    "date": {"start": ticker.timestamp.isoformat()}
                },
                "Record Count": {
                    "number": 1
                },
                "Status": {
                    "select": {"name": "Success"}
                },
                "Error Count": {
                    "number": 0
                }
            }
            
            # 数値フィールドに実際の値を保存
            if ticker.last:
                properties["Avg Volume"] = {"number": ticker.last}  # 価格を保存
            
            if ticker.percentage is not None:
                properties["Avg Spread %"] = {"number": abs(ticker.percentage) / 100}  # 変動率を保存
            
            if ticker.base_volume:
                properties["Total Tickers"] = {"number": ticker.base_volume}  # ボリュームを保存
            
            # ページコンテンツとして実データをJSON形式で保存
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📊 実際の取引データ"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": f"取引所: {ticker.exchange}\n"
                                         f"通貨ペア: {ticker.symbol}\n"
                                         f"価格: {price_str}\n"
                                         f"24時間変動: {change_str}\n"
                                         f"取引量: {ticker.base_volume:.4f} {ticker.symbol.split('/')[0] if '/' in ticker.symbol else ''}" if ticker.base_volume else "取引量: N/A"
                            }
                        }]
                    }
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{
                            "text": {"content": json.dumps(real_data, ensure_ascii=False, indent=2)}
                        }],
                        "language": "json",
                        "caption": [{
                            "text": {"content": "実際の取引データ (JSON形式)"}
                        }]
                    }
                }
            ]
            
            # Notionページを作成
            page = await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            logger.info(f"✅ 実データ保存成功: {ticker.exchange} {ticker.symbol} - Price: {price_str}, Volume: {ticker.base_volume}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 実データ保存失敗 {ticker.exchange} {ticker.symbol}: {e}")
            return False
    
    async def upload_orderbook_with_real_data(self, orderbook: OrderBookData) -> bool:
        """オーダーブックの実データを保存"""
        try:
            best_bid = orderbook.bids[0][0] if orderbook.bids else None
            best_ask = orderbook.asks[0][0] if orderbook.asks else None
            spread = orderbook.spread if orderbook.spread else (best_ask - best_bid if best_ask and best_bid else None)
            
            title = f"{orderbook.exchange} {orderbook.symbol} OrderBook | Spread: {spread:.4f}" if spread else f"{orderbook.exchange} {orderbook.symbol} OrderBook"
            
            # オーダーブックの実データ
            real_data = {
                "timestamp": orderbook.timestamp.isoformat(),
                "exchange": orderbook.exchange,
                "symbol": orderbook.symbol,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread": spread,
                "spread_percentage": orderbook.spread_percentage,
                "bid_depth": orderbook.bid_depth,
                "ask_depth": orderbook.ask_depth,
                "bids": orderbook.bids[:10],  # Top 10 bids
                "asks": orderbook.asks[:10]   # Top 10 asks
            }
            
            properties = {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Data Type": {
                    "select": {"name": "Real OrderBook Data"}
                },
                "Exchange": {
                    "select": {"name": orderbook.exchange}
                },
                "Collection Time": {
                    "date": {"start": orderbook.timestamp.isoformat()}
                },
                "Record Count": {
                    "number": 1
                },
                "Status": {
                    "select": {"name": "Success"}
                }
            }
            
            # 数値フィールドに実データを保存
            if spread:
                properties["Avg Spread %"] = {"number": orderbook.spread_percentage / 100 if orderbook.spread_percentage else 0}
            
            if orderbook.bid_depth:
                properties["Total OrderBooks"] = {"number": orderbook.bid_depth}
            
            # ページコンテンツ
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📈 オーダーブックデータ"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{
                            "text": {"content": json.dumps(real_data, ensure_ascii=False, indent=2)}
                        }],
                        "language": "json"
                    }
                }
            ]
            
            await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            logger.info(f"✅ オーダーブック保存: {orderbook.exchange} {orderbook.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ オーダーブック保存失敗: {e}")
            return False
    
    async def upload_exchange_data(self, data: CollectedData) -> Dict[str, Any]:
        """取引所の全データを実データとともに保存"""
        start_time = datetime.now(timezone.utc)
        
        result = {
            "exchange": data.exchange,
            "start_time": start_time.isoformat(),
            "tickers_uploaded": 0,
            "orderbooks_uploaded": 0,
            "total_uploaded": 0,
            "status": "processing"
        }
        
        try:
            # ティッカーデータをアップロード
            if data.tickers:
                logger.info(f"📤 {data.exchange}の{len(data.tickers)}件のティッカーデータをアップロード開始")
                
                for ticker in data.tickers[:20]:  # 最初の20件に制限（レート制限対策）
                    success = await self.upload_ticker_with_real_data(ticker)
                    if success:
                        result["tickers_uploaded"] += 1
                    await asyncio.sleep(0.3)  # レート制限対策
            
            # オーダーブックデータをアップロード（上位5件）
            if data.orderbooks:
                logger.info(f"📤 {data.exchange}の{len(data.orderbooks)}件のオーダーブックをアップロード")
                
                for orderbook in data.orderbooks[:5]:
                    success = await self.upload_orderbook_with_real_data(orderbook)
                    if success:
                        result["orderbooks_uploaded"] += 1
                    await asyncio.sleep(0.3)
            
            # 取引所サマリーを作成
            await self._create_exchange_summary(data, result)
            
            end_time = datetime.now(timezone.utc)
            result["end_time"] = end_time.isoformat()
            result["duration"] = (end_time - start_time).total_seconds()
            result["total_uploaded"] = result["tickers_uploaded"] + result["orderbooks_uploaded"]
            result["status"] = "success"
            
            logger.success(f"✅ {data.exchange}のデータアップロード完了: "
                          f"{result['tickers_uploaded']}ティッカー, "
                          f"{result['orderbooks_uploaded']}オーダーブック")
            
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"❌ {data.exchange}のアップロード失敗: {e}")
        
        return result
    
    async def _create_exchange_summary(self, data: CollectedData, upload_result: Dict[str, Any]):
        """取引所の実データサマリーを作成"""
        try:
            # 統計情報を計算
            avg_price = 0
            total_volume = 0
            if data.tickers:
                prices = [t.last for t in data.tickers if t.last]
                volumes = [t.base_volume for t in data.tickers if t.base_volume]
                avg_price = sum(prices) / len(prices) if prices else 0
                total_volume = sum(volumes) if volumes else 0
            
            title = f"📊 {data.exchange} 実データサマリー - {data.collection_timestamp.strftime('%Y-%m-%d %H:%M')}"
            
            properties = {
                "Name": {
                    "title": [{"text": {"content": title}}]
                },
                "Data Type": {
                    "select": {"name": "Exchange Summary"}
                },
                "Exchange": {
                    "select": {"name": data.exchange}
                },
                "Collection Time": {
                    "date": {"start": data.collection_timestamp.isoformat()}
                },
                "Total Tickers": {
                    "number": len(data.tickers)
                },
                "Total OrderBooks": {
                    "number": len(data.orderbooks)
                },
                "Record Count": {
                    "number": upload_result["total_uploaded"]
                },
                "Status": {
                    "select": {"name": "Success"}
                }
            }
            
            # サマリー統計
            summary_stats = {
                "exchange": data.exchange,
                "collection_time": data.collection_timestamp.isoformat(),
                "total_tickers": len(data.tickers),
                "total_orderbooks": len(data.orderbooks),
                "uploaded_tickers": upload_result["tickers_uploaded"],
                "uploaded_orderbooks": upload_result["orderbooks_uploaded"],
                "average_price": avg_price,
                "total_volume": total_volume,
                "top_symbols": [t.symbol for t in data.tickers[:10]] if data.tickers else []
            }
            
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "📊 取引所データサマリー"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "text": {
                                "content": f"✅ アップロード成功: {upload_result['total_uploaded']}件の実データ\n"
                                         f"📈 平均価格: ${avg_price:.2f}\n"
                                         f"📊 総取引量: {total_volume:.2f}"
                            }
                        }]
                    }
                },
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{
                            "text": {"content": json.dumps(summary_stats, ensure_ascii=False, indent=2)}
                        }],
                        "language": "json"
                    }
                }
            ]
            
            await self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            logger.info(f"✅ {data.exchange}のサマリー作成完了")
            
        except Exception as e:
            logger.error(f"サマリー作成失敗: {e}")
    
    async def upload_all_exchanges(self, all_results: Dict[str, CollectedData]) -> Dict[str, Any]:
        """全取引所のデータをアップロード"""
        start_time = datetime.now(timezone.utc)
        
        upload_summary = {
            "start_time": start_time.isoformat(),
            "exchanges": {},
            "totals": {
                "exchanges_processed": 0,
                "exchanges_successful": 0,
                "total_tickers": 0,
                "total_orderbooks": 0,
                "total_records": 0
            }
        }
        
        logger.info(f"🚀 {len(all_results)}取引所の実データアップロード開始")
        
        for exchange_name, data in all_results.items():
            result = await self.upload_exchange_data(data)
            upload_summary["exchanges"][exchange_name] = result
            
            # 統計更新
            upload_summary["totals"]["exchanges_processed"] += 1
            if result["status"] == "success":
                upload_summary["totals"]["exchanges_successful"] += 1
                upload_summary["totals"]["total_tickers"] += result["tickers_uploaded"]
                upload_summary["totals"]["total_orderbooks"] += result["orderbooks_uploaded"]
                upload_summary["totals"]["total_records"] += result["total_uploaded"]
            
            # レート制限対策
            await asyncio.sleep(1)
        
        end_time = datetime.now(timezone.utc)
        upload_summary["end_time"] = end_time.isoformat()
        upload_summary["total_duration"] = (end_time - start_time).total_seconds()
        
        # 最終サマリー
        totals = upload_summary["totals"]
        logger.success(f"✅ 全データアップロード完了: "
                      f"{totals['exchanges_successful']}/{totals['exchanges_processed']}取引所, "
                      f"{totals['total_records']}件の実データ保存済み")
        
        return upload_summary