# 取引所調査ガイド

## 概要

このプロジェクトは、世界の102の仮想通貨取引所の公開APIを調査し、どのようなデータが取得可能かを体系的に記録するものです。

## 調査プロセス

### 1. データ収集フェーズ

```bash
# 全102取引所の並列調査を実行
poetry run python scripts/survey/survey_all_102_parallel.py
```

このスクリプトは以下を実行します：
- 102の取引所に並列アクセス（最大20同時接続）
- 各取引所の公開APIをテスト
- 利用可能なデータタイプを確認
- サンプルデータを取得

### 2. データ保存フェーズ

調査結果は `output/exchange_survey_parallel.json` に保存されます。

### 3. Notionアップロードフェーズ

```bash
# 詳細情報付きでNotionにアップロード
poetry run python scripts/notion-upload/upload_survey_detailed.py
```

## 収集されるデータ

### 基本情報
- 取引所名
- 公開API利用可能性
- 総マーケット数（取扱通貨ペア数）
- サンプル通貨ペア

### データタイプ別情報

#### 1. Ticker（価格情報）
```json
{
  "symbol": "BTC/USDT",
  "last": 95123.45,
  "bid": 95120.00,
  "ask": 95125.00,
  "high": 96000.00,
  "low": 94000.00,
  "volume": 12345.67
}
```

#### 2. OrderBook（板情報）
```json
{
  "bids": [[95120.00, 1.23], [95119.00, 2.34]],
  "asks": [[95125.00, 1.45], [95126.00, 2.56]],
  "spread": 5.00
}
```

#### 3. Trades（約定履歴）
- 約定価格
- 約定数量
- 約定時刻
- 売買方向

#### 4. OHLCV（ローソク足）
- 対応時間軸: 1m, 5m, 15m, 30m, 1h, 4h, 1d など
- 各時間軸のOHLCV値

### API機能
- fetchTicker: 個別通貨ペアの価格取得
- fetchTickers: 全通貨ペアの価格一括取得
- fetchOrderBook: 板情報取得
- fetchTrades: 約定履歴取得
- fetchOHLCV: ローソク足データ取得

## Notionデータベース構造

各取引所は1レコードとして保存され、以下の情報を含みます：

### プロパティ
- **Name**: 取引所名と概要
- **Data Type**: "Exchange API Guide"
- **Exchange**: 取引所名
- **Total Tickers**: マーケット数
- **Record Count**: 利用可能なデータタイプ数
- **Status**: Success/Failed

### ページコンテンツ
1. **取引所概要**
   - マーケット数
   - 主要通貨ペア
   - 利用可能なデータタイプ

2. **APIサンプルコード**
   ```python
   import ccxt
   exchange = ccxt.binance()
   ticker = exchange.fetch_ticker('BTC/USDT')
   ```

3. **実データサンプル**
   - 実際のAPI呼び出し結果
   - 価格、ボリューム、板情報など

4. **生のJSONレスポンス**
   - APIの実際のレスポンス例

## トラブルシューティング

### よくある問題

1. **API制限エラー**
   - 解決: 同時実行数を減らす
   - `max_concurrent=10` に変更

2. **認証エラー**
   - 一部の取引所は公開APIでもAPIキーが必要
   - これらは調査から除外される

3. **地域制限**
   - 一部の取引所は特定地域からのアクセスを制限
   - VPNの使用は推奨しない

### エラーの確認方法

```bash
# 調査結果のエラーを確認
cat output/exchange_survey_parallel.json | jq '.[] | select(.status == "error") | {exchange, errors}'
```

## 活用例

1. **取引所選定**
   - どの取引所がどのデータを提供しているか一覧で確認
   - 必要なデータタイプを提供する取引所を選定

2. **API統合開発**
   - サンプルコードをベースに実装
   - 各取引所の特性を理解

3. **データ分析**
   - 利用可能なデータの種類と粒度を把握
   - 分析に適した取引所を選定