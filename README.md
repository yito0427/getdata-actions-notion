# 🎓 仮想通貨取引所API調査システム（学習用）

世界の102の仮想通貨取引所の公開APIを調査し、取得可能なデータを体系的に記録する学習用プロジェクトです。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org)
[![CCXT](https://img.shields.io/badge/CCXT-102%20Exchanges-green.svg)](https://github.com/ccxt/ccxt)
[![Notion](https://img.shields.io/badge/Notion-Database-black.svg)](https://developers.notion.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 プロジェクトの目的

このプロジェクトは**学習用**として設計されており、以下を目的としています：

1. **API理解**: 各取引所がどのようなデータを提供しているか理解する
2. **実装学習**: CCXTライブラリを使用したデータ取得方法を学ぶ
3. **データ整理**: 取得可能なデータを体系的に整理・記録する
4. **サンプルコード**: 各取引所のAPI利用例を提供する

> ⚠️ **注意**: 本番環境での高頻度データ収集には適していません。実運用には適切なデータベース（TimescaleDB等）の使用を推奨します。

## 🚀 クイックスタート

### 1. 環境準備

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/getdata-actions-notion.git
cd getdata-actions-notion

# Poetryのインストール（未インストールの場合）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係のインストール
poetry install
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集してNotion APIキーとデータベースIDを設定
```

### 3. 完全な調査とGitHub同期の実行

```bash
# 推奨: 調査→Notionアップロード→GitHub同期を一括実行
poetry run python scripts/complete-survey-and-sync.py

# または個別実行
poetry run python scripts/survey/survey_all_102_parallel.py
poetry run python scripts/notion-upload/upload_survey_detailed.py
poetry run python scripts/github-sync/export_notion_to_github.py
```

## 📊 収集されるデータ

### 各取引所について記録される情報

1. **基本情報**
   - 取引所名、公開API利用可能性
   - 総マーケット数（取扱通貨ペア数）
   - 主要通貨ペアのリスト

2. **取得可能なデータタイプ**
   - **Ticker**: 価格情報（last, bid, ask, high, low, volume等）
   - **OrderBook**: 板情報（買い注文、売り注文、スプレッド）
   - **Trades**: 約定履歴
   - **OHLCV**: ローソク足データ（対応時間軸含む）

3. **APIサンプルコード**
   ```python
   import ccxt
   exchange = ccxt.binance()
   ticker = exchange.fetch_ticker('BTC/USDT')
   print(f"最終価格: ${ticker['last']}")
   ```

4. **実際のデータサンプル**
   ```json
   {
     "symbol": "BTC/USDT",
     "last": 95123.45,
     "bid": 95120.00,
     "ask": 95125.00,
     "volume": 12345.67
   }
   ```

## 📁 プロジェクト構造

```
getdata-actions-notion/
├── scripts/
│   ├── survey/                    # 取引所調査スクリプト
│   │   └── survey_all_102_parallel.py  # メイン調査スクリプト
│   ├── notion-upload/             # Notionアップロード
│   │   └── upload_survey_detailed.py   # 詳細アップロード
│   └── utils/                     # テストスクリプト
├── src/                           # ソースコード
│   ├── collectors/                # データ収集モジュール
│   ├── notion/                    # Notion統合
│   └── utils/                     # ユーティリティ
├── docs/                          # ドキュメント
├── output/                        # 調査結果の出力
└── README.md                      # 本ファイル
```

詳細は [docs/project-structure.md](docs/project-structure.md) を参照してください。

## 🔧 主な機能

### 1. 並列取引所調査
- 102の取引所を最大20並列で調査
- 各取引所の公開APIをテスト
- 利用可能なデータタイプを自動検出

### 2. データ整理とドキュメント化
- 取得可能なデータを体系的に整理
- APIサンプルコードを自動生成
- 実際のレスポンスデータを記録

### 3. Notion統合
- 1取引所1レコードで詳細情報を保存
- 検索・フィルタリング可能な形式
- APIガイドとして活用可能

### 4. GitHub同期と履歴管理 🆕
- NotionデータをGitHubリポジトリに自動同期
- 実行の度に日時付き履歴ファイルを作成
- マークダウン形式での読みやすいレポート生成
- GitHub Actionsによる定期的な自動実行

## 📚 ドキュメント

- [取引所調査ガイド](docs/guides/exchange-survey.md) - 調査プロセスの詳細
- [プロジェクト構造](docs/project-structure.md) - ディレクトリとファイルの説明
- [スクリプトREADME](scripts/README.md) - 各スクリプトの使用方法
- [GitHub同期ガイド](docs/github-sync-guide.md) - Notion→GitHub同期機能の詳細 🆕

## 🎯 使用例

### 特定の取引所グループを調査

```python
# scripts/survey/custom_survey.py として作成
explorer = ExchangeExplorer()
explorer.exchanges = ["binance", "coinbase", "kraken"]  # 調査したい取引所
results = await explorer.explore_all_exchanges_parallel()
```

### 調査結果の分析

```python
# 調査結果JSONを読み込んで分析
import json
with open("output/exchange_survey_parallel.json") as f:
    results = json.load(f)

# Tickerデータが取得可能な取引所をリスト
ticker_exchanges = [
    name for name, data in results.items()
    if data.get("available_data", {}).get("ticker")
]
print(f"Ticker取得可能: {len(ticker_exchanges)}取引所")
```

## ⚠️ 注意事項

1. **学習用途限定**: 本番環境での使用は推奨しません
2. **API制限**: 各取引所のレート制限を遵守してください
3. **地域制限**: 一部の取引所は地域制限があります
4. **データ保存**: Notionは大量データの保存には不向きです

## 🤝 コントリビューション

改善提案やバグ報告は歓迎します：

1. Issueを作成して問題を報告
2. Forkしてフィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを送信

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照

## 🙏 謝辞

- [CCXT](https://github.com/ccxt/ccxt) - 仮想通貨取引所API統合ライブラリ
- [Notion API](https://developers.notion.com) - データベース統合
- [Poetry](https://python-poetry.org) - Pythonパッケージ管理

---

**📖 これは学習用プロジェクトです。実運用には適切なインフラストラクチャをご利用ください。**