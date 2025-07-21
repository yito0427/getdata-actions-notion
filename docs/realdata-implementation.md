# 実データ保存機能実装ドキュメント

## 概要
RealDataNotionUploaderを実装し、実際の仮想通貨データ（価格、ボリューム、オーダーブック等）をNotionデータベースに確実に保存する機能を追加しました。

## 実装内容

### 1. RealDataNotionUploader (`src/notion/realdata_uploader.py`)

#### 主な特徴:
- **実データの完全保存**: 価格、ボリューム、bid/ask、高値/安値など全ての実データを保存
- **JSON形式での保存**: ページコンテンツにJSON形式で実データを保存
- **視覚的な表示**: タイトルに価格と変動率を含め、一目で状況が分かる
- **詳細なログ**: 保存成功/失敗を詳細にログ出力

#### 保存されるデータ:
```json
{
  "timestamp": "2025-07-21T10:00:00Z",
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "prices": {
    "last": 29999.99,
    "bid": 29998.00,
    "ask": 30001.00,
    "high": 30500.00,
    "low": 29500.00,
    "open": 29800.00,
    "close": 29999.99,
    "vwap": 29950.00
  },
  "volumes": {
    "base_volume": 1234.56,
    "quote_volume": 37000000.00
  }
}
```

### 2. main.py の更新

- `--direct-upload` オプション使用時に RealDataNotionUploader を使用
- 保存結果の詳細表示（ティッカー数、オーダーブック数、合計レコード数）

### 3. テストスクリプト (`scripts/test_realdata.py`)

実データが正しく保存されることを確認するためのテストスクリプト:

```bash
# テスト実行
poetry run python scripts/test_realdata.py
```

## 使用方法

### 1. ローカル実行（テスト）

```bash
# 優先度の高い取引所から実データを収集・保存
poetry run python -m src.main --priority-only --limit 5 --direct-upload

# 全取引所から実データを収集・保存（レート制限に注意）
poetry run python -m src.main --direct-upload
```

### 2. GitHub Actions での自動実行

`.github/workflows/crypto-data-collection.yml` で15分ごとに自動実行されます。

### 3. データの確認方法

1. **Notionで確認**:
   - データベースを開く
   - "Real Ticker Data" または "Real OrderBook Data" タイプのレコードを探す
   - ページを開いてJSON形式の実データを確認

2. **CSVエクスポート**:
   ```bash
   # NotionからCSVにエクスポート
   poetry run python -m src.utils.notion_to_csv
   ```

## 技術的な詳細

### レート制限対策
- 各レコード保存後に0.3秒の待機時間
- 取引所ごとに1秒の待機時間
- ティッカーは最大20件、オーダーブックは最大5件に制限

### エラーハンドリング
- 各レコードの保存失敗を個別にキャッチ
- 失敗してもプロセス全体は継続
- 詳細なエラーログ出力

### Notionページ構造
1. **プロパティ**: 標準的なデータベースフィールドを使用
2. **ページコンテンツ**: 
   - ヘッダー: "📊 実際の取引データ"
   - 概要: 主要な数値を日本語で表示
   - JSONコード: 完全な実データをJSON形式で保存

## トラブルシューティング

### データが保存されない場合

1. **環境変数の確認**:
   ```bash
   echo $NOTION_API_KEY
   echo $NOTION_DATABASE_ID
   ```

2. **Notion権限の確認**:
   - Integration がデータベースにアクセス権を持っているか
   - データベースが正しく共有されているか

3. **ログの確認**:
   - 実行時のログで "✅ 実データ保存成功" メッセージを確認
   - エラーメッセージ "❌ 実データ保存失敗" がないか確認

4. **手動テスト実行**:
   ```bash
   poetry run python scripts/test_realdata.py
   ```

## 今後の改善点

1. **バッチ処理**: 複数レコードを一度に保存してAPI呼び出しを削減
2. **圧縮**: 大量のデータを効率的に保存するための圧縮機能
3. **増分更新**: 既存データの更新機能
4. **データ検証**: 保存前のデータ整合性チェック