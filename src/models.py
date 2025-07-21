"""
Data models for cryptocurrency data collection.
認証不要で取得可能な公開APIデータの定義
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TickerData(BaseModel):
    """
    Ticker情報（価格・ボリューム統計）
    CCXTのfetch_ticker()で取得可能なデータ
    """
    exchange: str = Field(..., description="取引所名")
    symbol: str = Field(..., description="通貨ペア (例: BTC/USDT)")
    timestamp: datetime = Field(..., description="データ取得時刻")
    
    # 価格情報
    last: Optional[float] = Field(None, description="最終取引価格")
    bid: Optional[float] = Field(None, description="買い注文の最高値")
    ask: Optional[float] = Field(None, description="売り注文の最安値")
    high: Optional[float] = Field(None, description="24時間高値")
    low: Optional[float] = Field(None, description="24時間安値")
    open: Optional[float] = Field(None, description="24時間前の価格")
    close: Optional[float] = Field(None, description="現在価格（lastと同じ）")
    
    # ボリューム情報
    base_volume: Optional[float] = Field(None, description="基準通貨の24時間取引量")
    quote_volume: Optional[float] = Field(None, description="決済通貨の24時間取引量")
    
    # 変化率
    percentage: Optional[float] = Field(None, description="24時間変化率（%）")
    change: Optional[float] = Field(None, description="24時間変化額")
    
    # 追加情報
    vwap: Optional[float] = Field(None, description="出来高加重平均価格")
    bid_volume: Optional[float] = Field(None, description="買い注文量")
    ask_volume: Optional[float] = Field(None, description="売り注文量")


class OrderBookData(BaseModel):
    """
    オーダーブック（板情報）
    CCXTのfetch_order_book()で取得可能なデータ
    """
    exchange: str = Field(..., description="取引所名")
    symbol: str = Field(..., description="通貨ペア")
    timestamp: datetime = Field(..., description="データ取得時刻")
    
    # 買い注文（価格、数量のリスト）
    bids: List[List[float]] = Field(..., description="買い注文 [[価格, 数量], ...]")
    # 売り注文（価格、数量のリスト）
    asks: List[List[float]] = Field(..., description="売り注文 [[価格, 数量], ...]")
    
    # 計算値
    spread: Optional[float] = Field(None, description="スプレッド（ask - bid）")
    spread_percentage: Optional[float] = Field(None, description="スプレッド率（%）")
    
    # 深度情報
    bid_depth: Optional[float] = Field(None, description="買い注文の合計量")
    ask_depth: Optional[float] = Field(None, description="売り注文の合計量")


class TradeData(BaseModel):
    """
    取引履歴
    CCXTのfetch_trades()で取得可能なデータ
    """
    exchange: str = Field(..., description="取引所名")
    symbol: str = Field(..., description="通貨ペア")
    timestamp: datetime = Field(..., description="取引時刻")
    
    trade_id: Optional[str] = Field(None, description="取引ID")
    price: float = Field(..., description="取引価格")
    amount: float = Field(..., description="取引量")
    cost: Optional[float] = Field(None, description="取引金額（price × amount）")
    side: Optional[str] = Field(None, description="売買方向（buy/sell）")
    taker_or_maker: Optional[str] = Field(None, description="taker/maker")


class OHLCVData(BaseModel):
    """
    OHLCV（ローソク足）データ
    CCXTのfetch_ohlcv()で取得可能なデータ
    """
    exchange: str = Field(..., description="取引所名")
    symbol: str = Field(..., description="通貨ペア")
    timeframe: str = Field(..., description="時間枠（1m, 5m, 1h, 1d等）")
    
    timestamp: datetime = Field(..., description="期間開始時刻")
    open: float = Field(..., description="始値")
    high: float = Field(..., description="高値")
    low: float = Field(..., description="安値")
    close: float = Field(..., description="終値")
    volume: float = Field(..., description="取引量")


class ExchangeStatus(BaseModel):
    """
    取引所ステータス情報
    CCXTのfetch_status()で取得可能なデータ
    """
    exchange: str = Field(..., description="取引所名")
    timestamp: datetime = Field(..., description="チェック時刻")
    
    status: str = Field(..., description="ステータス（ok/maintenance等）")
    updated: Optional[datetime] = Field(None, description="最終更新時刻")
    eta: Optional[datetime] = Field(None, description="復旧予定時刻")
    url: Optional[str] = Field(None, description="ステータスページURL")


class MarketInfo(BaseModel):
    """
    マーケット情報
    CCXTのload_markets()で取得可能なデータ
    """
    exchange: str = Field(..., description="取引所名")
    symbol: str = Field(..., description="通貨ペア")
    
    base: str = Field(..., description="基準通貨（BTC等）")
    quote: str = Field(..., description="決済通貨（USDT等）")
    active: bool = Field(..., description="取引可能かどうか")
    
    # 取引制限
    min_amount: Optional[float] = Field(None, description="最小取引量")
    max_amount: Optional[float] = Field(None, description="最大取引量")
    min_price: Optional[float] = Field(None, description="最小価格")
    max_price: Optional[float] = Field(None, description="最大価格")
    
    # 手数料情報（公開されている場合）
    taker_fee: Optional[float] = Field(None, description="Taker手数料")
    maker_fee: Optional[float] = Field(None, description="Maker手数料")
    
    # 精度情報
    amount_precision: Optional[int] = Field(None, description="数量の小数点精度")
    price_precision: Optional[int] = Field(None, description="価格の小数点精度")


class ExchangeInfo(BaseModel):
    """
    取引所基本情報
    """
    name: str = Field(..., description="取引所名")
    countries: List[str] = Field(default_factory=list, description="対応国")
    urls: Dict[str, Any] = Field(default_factory=dict, description="各種URL")
    has: Dict[str, bool] = Field(default_factory=dict, description="機能サポート状況")
    timeframes: Dict[str, str] = Field(default_factory=dict, description="対応時間枠")
    rate_limit: Optional[int] = Field(None, description="レート制限（リクエスト/秒）")


class CollectedData(BaseModel):
    """
    収集したすべてのデータを格納するコンテナ
    """
    exchange: str
    collection_timestamp: datetime
    
    # 各種データ
    tickers: List[TickerData] = Field(default_factory=list)
    orderbooks: List[OrderBookData] = Field(default_factory=list)
    trades: List[TradeData] = Field(default_factory=list)
    ohlcv: List[OHLCVData] = Field(default_factory=list)
    
    # メタデータ
    exchange_status: Optional[ExchangeStatus] = None
    markets: List[MarketInfo] = Field(default_factory=list)
    exchange_info: Optional[ExchangeInfo] = None
    
    # エラー情報
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)