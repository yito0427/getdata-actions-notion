# Notionデータベース設計

## 概要

仮想通貨データを効率的に保存・検索できるよう、以下の3つのデータベースを作成します：

1. **Crypto Tickers** - 価格・ボリューム情報
2. **Crypto OrderBooks** - オーダーブック（板情報）
3. **Exchange Status** - 取引所ステータス

## 1. Crypto Tickers データベース

最も頻繁に更新される価格情報を保存します。

### プロパティ構成

| プロパティ名 | タイプ | 説明 |
|------------|--------|------|
| Title | タイトル | {取引所}_{通貨ペア}_{タイムスタンプ} |
| Exchange | セレクト | 取引所名（binance, coinbase等） |
| Symbol | セレクト | 通貨ペア（BTC/USDT等） |
| Timestamp | 日付 | データ取得時刻 |
| Last Price | 数値 | 最終取引価格 |
| Bid | 数値 | 買い注文の最高値 |
| Ask | 数値 | 売り注文の最安値 |
| High 24h | 数値 | 24時間高値 |
| Low 24h | 数値 | 24時間安値 |
| Volume Base | 数値 | 基準通貨の24時間取引量 |
| Volume Quote | 数値 | 決済通貨の24時間取引量 |
| Change % | 数値 | 24時間変化率（%） |
| VWAP | 数値 | 出来高加重平均価格 |
| Spread | 数値 | スプレッド（Ask - Bid） |
| Spread % | 数値 | スプレッド率 |

### ビュー設定

1. **Latest Prices** - 各通貨ペアの最新価格
   - フィルター: 各Symbol × Exchangeの最新レコード
   - ソート: Symbol → Exchange

2. **High Volume** - 高ボリューム取引
   - フィルター: Volume Base > 1000
   - ソート: Volume Base (降順)

3. **Price Changes** - 大きな価格変動
   - フィルター: |Change %| > 5
   - ソート: Change % (降順)

## 2. Crypto OrderBooks データベース

オーダーブックの深度情報を保存します（更新頻度は低め）。

### プロパティ構成

| プロパティ名 | タイプ | 説明 |
|------------|--------|------|
| Title | タイトル | {取引所}_{通貨ペア}_OrderBook_{タイムスタンプ} |
| Exchange | セレクト | 取引所名 |
| Symbol | セレクト | 通貨ペア |
| Timestamp | 日付 | データ取得時刻 |
| Best Bid | 数値 | 最高買い価格 |
| Best Ask | 数値 | 最安売り価格 |
| Spread | 数値 | スプレッド |
| Spread % | 数値 | スプレッド率 |
| Bid Depth | 数値 | 買い注文の合計量 |
| Ask Depth | 数値 | 売り注文の合計量 |
| Bid Orders | 数値 | 買い注文数 |
| Ask Orders | 数値 | 売り注文数 |
| Mid Price | 数値 | 中間価格 |
| Imbalance | 数値 | 注文の偏り（Bid/Ask比率） |

## 3. Exchange Status データベース

取引所の稼働状況を記録します。

### プロパティ構成

| プロパティ名 | タイプ | 説明 |
|------------|--------|------|
| Title | タイトル | {取引所}_Status_{日付} |
| Exchange | セレクト | 取引所名 |
| Check Time | 日付 | チェック時刻 |
| Status | セレクト | ok, maintenance, degraded, down |
| Total Markets | 数値 | 利用可能なマーケット数 |
| Active Symbols | 数値 | アクティブな通貨ペア数 |
| Collected Tickers | 数値 | 収集したTicker数 |
| Errors | 数値 | エラー数 |
| Error Details | テキスト | エラー詳細（JSON） |
| Collection Duration | 数値 | データ収集にかかった時間（秒） |

## Notionデータベースの作成手順

1. **新規ページ作成**
   - ワークスペースで「/database」と入力
   - 「データベース - フルページ」を選択

2. **各データベースを作成**
   - 上記のプロパティを追加
   - プロパティタイプを正確に設定

3. **ビューの作成**
   - 各データベースに推奨ビューを追加
   - フィルターとソートを設定

4. **APIアクセス許可**
   - 各データベースの「...」→「コネクト」
   - 作成したインテグレーションを追加

5. **データベースIDの取得**
   - 各データベースのURLからIDをコピー
   - .envファイルに追加：
   ```
   NOTION_TICKER_DB_ID=xxxxx
   NOTION_ORDERBOOK_DB_ID=xxxxx
   NOTION_STATUS_DB_ID=xxxxx
   ```

## データ保存戦略

1. **Ticker Data**
   - 1分ごとに最新データを保存
   - 古いデータは定期的にアーカイブ

2. **OrderBook Data**
   - 5分ごとに主要通貨ペアのみ保存
   - スプレッドが大きく変動した時のみ保存

3. **Exchange Status**
   - 各収集サイクルごとに1レコード
   - エラーが発生した場合は詳細を記録

## パフォーマンス最適化

1. **バッチ挿入**
   - 複数のレコードをまとめて挿入
   - API制限（3リクエスト/秒）を考慮

2. **データ圧縮**
   - OrderBookの詳細データは要約のみ保存
   - 完全なデータは必要に応じて別途保存

3. **定期クリーンアップ**
   - 30日以上前のTickerデータを削除
   - エラーのないStatusレコードは7日後に削除