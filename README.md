# 🚀 getdata-actions-notion

**仮想通貨データ収集＆Notion自動保存システム**

GitHub Actionsで定期実行し、102の取引所から仮想通貨データを収集してNotionに自動保存するPythonツールです。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org)
[![CCXT](https://img.shields.io/badge/CCXT-102%20Exchanges-green.svg)](https://github.com/ccxt/ccxt)
[![Notion](https://img.shields.io/badge/Notion-API%20Integration-black.svg)](https://developers.notion.com)

## ✨ 特徴

- 🌐 **102の取引所対応** - CCXTライブラリを使用してBinance、Coinbase、Krakenなど主要取引所をサポート
- 🔓 **認証不要** - 公開APIのみ使用、APIキー不要でデータ収集
- ⚡ **高速並行処理** - 非同期処理で複数取引所から同時データ収集
- 📊 **Notion統合** - 収集データをNotionデータベースに自動保存・検索可能
- 📁 **CSV出力対応** - 日別・取引所別・データ種別にCSVファイル生成
- 🔄 **GitHub Actions対応** - 定期実行とクラウド自動化
- 🛡️ **エラーハンドリング** - レート制限対策とリトライ機能
- 📈 **リアルタイム分析** - Notionで価格動向や取引量を即座に分析

## 📊 収集可能なデータ

### 認証不要で取得できる公開データ

| データタイプ | 内容 | 取得間隔推奨 |
|------------|------|------------|
| **Ticker情報** | 現在価格、24時間高値/安値、取引量、変化率 | 1分 |
| **オーダーブック** | 買い/売り注文、スプレッド、深度情報 | 5分 |
| **取引履歴** | 最新の取引価格・数量・方向 | 5分 |
| **OHLCV** | ローソク足データ（1分〜1日） | 1時間 |
| **取引所ステータス** | 稼働状況、メンテナンス情報 | 1日 |

### 主要対応取引所

- **グローバル**: Binance, Coinbase, Kraken, Bitfinex, OKX, Bybit, KuCoin
- **日本**: bitFlyer, Coincheck, Zaif, bitbank
- **その他**: 98の追加取引所（CCXTサポート済み）

## 🛠️ セットアップ

### 1. リポジトリのクローンと環境構築

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/getdata-actions-notion.git
cd getdata-actions-notion

# Poetry のインストール（未インストールの場合）
curl -sSL https://install.python-poetry.org | python3 -

# 依存関係のインストール
poetry install
```

### 2. Notion統合の設定

#### 2.1 NotionでAPIキーを取得

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 「新しいインテグレーション」を作成
3. 生成されたAPIキーをコピー

#### 2.2 Notionデータベースまたはページを準備

**オプション1: 既存データベースを使用（推奨）**
- 既存のNotionデータベースのIDを取得
- データベースにインテグレーションのアクセス権を付与

**オプション2: 新しいページを作成**
- 新しいNotionページを作成
- ページIDを取得（新しいデータベースが自動作成されます）

#### 2.3 環境変数の設定

```bash
# .env.example を .env にコピー
cp .env.example .env

# .env ファイルを編集
NOTION_API_KEY=your_notion_api_key_here
NOTION_DATABASE_ID=your_database_or_page_id_here
```

## 🚀 使用方法

### 基本的な使い方

#### テストモード（Notion不要）

```bash
# 2つの取引所からテストデータ収集（CSVファイルのみ生成）
poetry run python -m src.main --test

# 特定の取引所を指定してテスト
poetry run python -m src.main --test --exchanges binance,coinbase

# Binanceのみで詳細テスト
poetry run python -m src.main --test --exchanges binance --limit 1
```

#### 本番モード（Notion統合）

```bash
# 【推奨】優先度の高い取引所からNotionに直接保存
poetry run python -m src.main --priority-only --direct-upload

# 特定の取引所数を制限（例：上位5取引所）
poetry run python -m src.main --priority-only --limit 5 --direct-upload

# 全取引所から収集（最大102取引所）
poetry run python -m src.main --direct-upload

# CSVファイル形式でNotionに保存（ファイル添付）
poetry run python -m src.main --priority-only
```

### 高度な使用方法

#### カスタム取引所指定

```bash
# 日本の主要取引所のみ
poetry run python -m src.main --exchanges bitflyer,coincheck,zaif --direct-upload

# グローバル主要取引所のみ
poetry run python -m src.main --exchanges binance,coinbase,kraken,bitfinex --direct-upload

# 大手5取引所で定期監視
poetry run python -m src.main --exchanges binance,coinbase,kraken,okx,bybit --direct-upload
```

#### データ収集の最適化

```bash
# 高速収集（少数の取引所、低遅延）
poetry run python -m src.main --priority-only --limit 3 --direct-upload

# 包括的収集（多数の取引所、高精度）
poetry run python -m src.main --limit 20 --direct-upload

# バランス型（推奨設定）
poetry run python -m src.main --priority-only --limit 10 --direct-upload
```

## 📁 プロジェクト構造

```
getdata-actions-notion/
├── src/
│   ├── collectors/              # データ収集エンジン
│   │   ├── base.py             # CCXT基底クラス（非同期処理）
│   │   └── manager.py          # 複数取引所の並行管理
│   ├── notion/                 # Notion API統合
│   │   ├── simple_uploader.py  # 既存DBへの直接アップロード
│   │   ├── rate_limiter.py     # API制限最適化・バッチ処理
│   │   ├── database_manager.py # 新規DB作成・管理
│   │   └── uploader.py         # CSVファイルアップロード
│   ├── utils/
│   │   └── csv_writer.py       # CSV出力（日別・取引所別）
│   ├── models.py               # Pydanticデータモデル
│   ├── config.py               # 環境変数・設定管理
│   └── main.py                 # CLIエントリーポイント
├── tests/                      # テストスイート
├── docs/                       # ドキュメント
├── data/                       # ローカルCSV出力先
├── output/                     # テスト結果出力
├── .github/
│   └── workflows/              # GitHub Actions定期実行ワークフロー
├── pyproject.toml              # Poetry依存関係管理
├── Makefile                    # 開発用コマンド
├── .env.example                # 環境変数テンプレート
└── CLAUDE.md                   # Claude開発ガイド
```

## 🔧 開発者向けコマンド

```bash
# ヘルプ表示
make help

# テスト実行（カバレッジ付き）
make test

# コードフォーマット（Black + isort）
make format

# リンター実行（flake8 + mypy）
make lint

# アプリケーション実行
make run

# 環境チェック
make check-env

# キャッシュクリア
make clean
```

## 📈 実装状況

### ✅ 完成済み機能

- **データ収集**: CCXT + 非同期処理で102取引所対応
- **エラーハンドリング**: リトライ機構・レート制限対策
- **Notion統合**: 直接DB保存・CSV添付の両方式
- **CSV出力**: 日別・取引所別・データ種別で整理
- **設定管理**: 環境変数・取引所別設定
- **ローカルテスト**: Notion不要のテストモード

### ✅ GitHub Actions自動化

- **定期実行**: 15分間隔で自動データ収集
- **Notion API最適化**: 0.5 RPS制限でAPI負荷を最小化
- **エラー監視**: 失敗時の自動Issue作成とアラート
- **テスト自動化**: PR時の自動テスト実行

### 🚧 予定機能

- **Webhooks**: リアルタイム価格アラート
- **ダッシュボード**: Notion内データ可視化
- **API拡張**: REST API提供

## 🔒 セキュリティ対策

### 重要な注意事項

- **`.env`ファイルは絶対にコミットしない**
- **Notion APIキーは環境変数で管理**
- **GitHub Secretsで本番環境キー管理**
- **ログに機密情報を出力しない**

### セキュリティ機能

```bash
# .gitignoreで環境変数ファイルを確実に除外
*.env
.env.*
notion_keys/
```

## 🎯 使用例・ユースケース

### 個人投資家
```bash
# 主要取引所の価格監視（15分ごと）
poetry run python -m src.main --exchanges binance,coinbase,kraken --direct-upload
```

### データ分析者
```bash
# 全取引所データ収集 + CSV出力
poetry run python -m src.main --limit 50
```

### トレーディングbot開発者
```bash
# 高頻度データ収集（テストモード）
poetry run python -m src.main --test --exchanges binance,bybit
```

## 🤝 コントリビューション

プルリクエストやイシューの報告を歓迎します！

### 開発の始め方

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチをプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### 開発ガイドライン

- Pythonコーディング規約（PEP 8）に準拠
- 型ヒント必須（mypy準拠）
- テストカバレッジ80%以上
- セキュリティ重視（APIキー漏洩防止）

## 📞 サポート・問い合わせ

- **Issues**: [GitHub Issues](https://github.com/yourusername/getdata-actions-notion/issues)
- **Discussions**: 機能提案やQ&A
- **Wiki**: 詳細ドキュメント

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🙏 謝辞

- [CCXT](https://github.com/ccxt/ccxt) - 仮想通貨取引所API統合
- [Notion API](https://developers.notion.com) - データベース統合
- [Poetry](https://python-poetry.org) - 依存関係管理
- [Pydantic](https://pydantic.dev) - データバリデーション

---

**⭐ このプロジェクトが役立ったら、ぜひスターをお願いします！**
