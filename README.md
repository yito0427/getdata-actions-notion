# 🚀 getdata-actions-notion

**仮想通貨データ収集＆Notion自動保存システム**

このプロジェクトは、GitHub Actionsを使用して15分間隔で自動実行され、世界中の102の仮想通貨取引所から公開データを収集し、Notionデータベースに蓄積する完全自動化システムです。認証不要の公開APIのみを使用し、リアルタイムで価格・取引量・オーダーブック情報を取得・分析できます。

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Poetry](https://img.shields.io/badge/Poetry-Dependency%20Management-blue.svg)](https://python-poetry.org)
[![CCXT](https://img.shields.io/badge/CCXT-102%20Exchanges-green.svg)](https://github.com/ccxt/ccxt)
[![Notion](https://img.shields.io/badge/Notion-API%20Integration-black.svg)](https://developers.notion.com)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Auto%20Collection-green.svg)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 プロジェクト概要

### ✅ 運用状況

**🚀 GitHub Actions自動運用中**: 15分間隔でデータ収集実行
**📊 Notion統合**: `DB_crypt`データベースに自動蓄積
**🔗 接続状況**: Notion API認証済み（ユーザー: `getdata_to_DB`）
**⚡ 最適化**: 0.5 RPS制限でAPI負荷最小化

### 🏗️ システム設計

このシステムは以下のアーキテクチャで構成されています：

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│  GitHub Actions │    │   Python     │    │    Notion       │
│  (15分間隔実行)  │───▶│  Data Collector│───▶│   DB_crypt      │
│   ✅ 運用中      │    │   (CCXT)     │    │   ✅ 接続済み   │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                     │
         │              ┌────────▼────────┐           │
         │              │ 102 Exchanges   │           │
         │              │ Public APIs     │           │
         │              │ (No Auth)       │           │
         │              └─────────────────┘           │
         │                                            │
         └──────────── ✅ エラー監視・自動Issue作成 ──────┘
```

### 💡 主要特徴

**🌍 グローバル対応**: 世界102の取引所から同時収集
**🔓 認証不要**: 公開APIのみ使用でセキュア
**⚡ 高性能**: 非同期処理で高速データ収集
**🤖 完全自動化**: GitHub Actionsで24時間運用
**📊 即座に分析**: Notionで収集データを可視化・検索
**🛡️ エラー対応**: 自動監視・復旧・レポート機能

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
| **Ticker情報** | 現在価格(last/bid/ask)、24時間高値/安値、取引量(base/quote)、変化率、VWAP | 1分 |
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

### 🤖 自動運用（推奨）

**✅ GitHub Actions運用中 - 完全自動化システム**:

1. **✅ GitHub Secretsの設定完了**:
   ```
   NOTION_API_KEY=ntn_645736... ✅ 設定済み
   NOTION_DATABASE_ID=************ ✅ 設定済み
   ```

2. **✅ 自動実行運用中**:
   - 15分間隔で自動データ収集実行中
   - 毎日96回の定期収集スケジュール
   - Notion `DB_crypt`データベースに蓄積中

3. **✅ 監視とレポート機能**:
   - 環境変数検証ワークフロー: 正常動作確認済み
   - エラー時の自動Issue作成機能: 有効
   - Notion API使用率: 37%（安全圏内）

### 📊 現在の稼働状況

- **接続ユーザー**: `getdata_to_DB`
- **対象データベース**: `DB_crypt`
- **API制限遵守**: 0.5 RPS（制限の83%マージン確保）
- **次回実行**: 15分後に自動実行

### 💻 ローカル実行

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
# 【推奨】優先度の高い取引所からNotionに直接保存（API最適化済み）
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

### ✅ GitHub Actions自動化（運用中）

- **✅ 定期実行**: 15分間隔で自動データ収集実行中
- **✅ Notion API統合**: `DB_crypt`データベースに自動保存
- **✅ 環境変数**: 認証情報設定完了・接続確認済み
- **✅ エラー監視**: 自動Issue作成・復旧機能有効
- **✅ API最適化**: 0.5 RPS制限でAPI負荷最小化

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

### 💰 個人投資家
**価格監視とトレンド分析**:
```bash
# 主要取引所の価格監視（15分ごと自動実行）
GitHub Actions: 自動運用
手動実行: poetry run python -m src.main --exchanges binance,coinbase,kraken --direct-upload
```
- リアルタイム価格変動をNotion上で分析
- 複数取引所の価格差（アービトラージ機会）を発見
- 24時間の価格履歴を自動蓄積

### 📊 データ分析者・研究者
**市場分析と研究**:
```bash
# 全取引所データ収集 + CSV出力
poetry run python -m src.main --limit 50
```
- 102取引所の市場動向を包括的に分析
- 地域別・取引所別の価格相関を研究
- CSVエクスポートで外部分析ツールと連携

### 🤖 トレーディングbot開発者
**戦略開発とバックテスト**:
```bash
# 高頻度データ収集（テストモード）
poetry run python -m src.main --test --exchanges binance,bybit
```
- 取引アルゴリズムの開発・検証
- リアルタイムオーダーブック分析
- 市場マイクロストラクチャー研究

### 🏢 金融機関・フィンテック企業
**市場監視と規制対応**:
```bash
# Enterprise級データ収集
poetry run python -m src.main --direct-upload  # 全102取引所
```
- 規制当局への報告データ自動生成
- 市場操作・異常取引の検出
- 顧客への市場情報提供サービス

### 📰 メディア・ニュース配信
**市場レポート自動生成**:
- Notionデータから自動記事生成
- 価格アラート・市場速報の配信
- 週次・月次市場レポートの作成

### 🎓 教育・学習目的
**仮想通貨市場の学習**:
```bash
# 学習用データ収集
poetry run python -m src.main --test --limit 3
```
- 市場の仕組みと価格形成を理解
- プログラミング・データ分析スキルの向上
- ブロックチェーン技術の実践的学習

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

## 📚 詳細ドキュメント

### 📖 技術ドキュメント
- [GitHub Actions セットアップガイド](docs/github-actions-setup.md) - 自動運用の詳細設定
- [本番環境デプロイ状況](docs/deployment-status.md) - 現在の稼働状況・監視情報
- [CLAUDE.md](CLAUDE.md) - 開発者向けプロジェクト構造説明
- [API制限最適化](src/notion/rate_limiter.py) - Notion API使用量最適化

### 🎯 主要機能の詳細

#### 1. 自動データ収集システム
```python
# 15分間隔で以下を自動実行
- 優先10取引所からデータ収集
- 0.5 RPS でNotion APIアップロード
- エラー監視と自動復旧
- 週次パフォーマンスレポート生成
```

#### 2. Notion統合機能
- **直接データベース保存**: CSV添付ではなくレコード形式で高速保存
- **リアルタイム検索**: Notionの強力な検索・フィルター機能
- **自動集計**: 取引所別・時間別の自動サマリー生成
- **可視化対応**: グラフ・チャート表示に最適化されたデータ形式

#### 3. API制限最適化
```yaml
Notion API制限: 3 req/sec, 2,700 req/15min
設計値: 0.5 req/sec, 960 req/day
安全マージン: 83% (同時実行), 20% (日間制限)
```

### 📥 実データのCSVエクスポート機能

収集した実際の仮想通貨データ（価格、ボリューム等）はNotionからCSVファイルとして抽出できます：

```bash
# Notionデータベースから実データをCSVエクスポート
poetry run python -m src.utils.notion_to_csv

# テストスクリプトでエクスポート実行
poetry run python scripts/test_csv_export.py
```

**エクスポートされるCSVデータ内容**:
- `timestamp`: データ収集時刻
- `exchange`: 取引所名
- `symbol`: 通貨ペア（BTC/USDT等）
- `price`: 最終取引価格
- `bid/ask`: 買い/売り注文の最良価格
- `high/low`: 24時間の高値/安値
- `open/close`: 始値/終値
- `vwap`: 出来高加重平均価格
- `base_volume/quote_volume`: 基準通貨/決済通貨の取引量
- `change_percent/change_absolute`: 変動率/変動額
- `spread/spread_percent`: スプレッド値/スプレッド率

### 🔧 高度な設定

#### GitHub Actions カスタマイズ
```yaml
# .github/workflows/crypto-data-collection.yml
env:
  EXCHANGES_LIMIT: 15          # 取引所数増加
  RATE_LIMIT_PER_SECOND: 0.3   # より保守的なレート制限
  MAX_CONCURRENT: 2            # 同時実行数削減
```

#### 取引所別設定
```python
# src/config.py - 優先取引所リスト
PRIORITY_EXCHANGES = [
    "binance", "coinbase", "kraken", "bitfinex", "okx", 
    "bybit", "kucoin", "bitflyer", "coincheck", "zaif"
]
```

## 📊 パフォーマンス指標

### 🎯 運用実績（想定値）

| 指標 | 値 | 備考 |
|------|----|----|
| **収集頻度** | 15分間隔 | 1日96回実行 |
| **取引所数** | 10-102 | 設定可能 |
| **1日のデータ数** | ~960-9,200 | 取引所数により変動 |
| **API使用率** | 37% | Notion制限の安全圏内 |
| **環境変数設定** | ✅ 完了 | 認証・接続確認済み |
| **成功率** | 95%+ | エラー監視・自動復旧 |
| **応答時間** | 45-60秒 | 10取引所収集時 |

### 📈 拡張性

**垂直スケーリング**:
- 取引所数: 10 → 50 → 102
- 収集頻度: 15分 → 5分 → 1分

**水平スケーリング**:
- 複数リージョンでの分散実行
- 地域別取引所の時間帯最適化
- カスタムNotionワークスペース連携

## 📞 サポート・問い合わせ

### 🔍 問題解決
- **Issues**: [GitHub Issues](https://github.com/yourusername/getdata-actions-notion/issues) - バグ報告・機能要望
- **Discussions**: GitHub Discussions - 使用方法の質問・アイデア共有
- **Wiki**: 詳細ドキュメント・FAQ・チュートリアル

### 🚀 機能追加・改善提案
- **プルリクエスト**: 新機能・改善の提案
- **Issues Labels**: `enhancement`, `feature`, `optimization`
- **ロードマップ**: 今後の開発計画をIssuesで公開

## 🚀 プロジェクト状況

### ✅ 本番運用中

**現在の状況**: GitHub Actionsで15分間隔の自動運用実行中  
**Notion統合**: `DB_crypt`データベースでデータ蓄積中  
**監視状況**: 環境変数検証・API接続確認完了  
**最終更新**: 2025年7月21日

### 📊 リアルタイム稼働データ

- **自動実行**: 毎日96回（15分間隔）
- **API使用率**: Notion制限の37%で安全運用
- **対応取引所**: 世界102の仮想通貨取引所
- **データ形式**: リアルタイム価格・取引量・オーダーブック（実データ保存）

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🙏 謝辞

- [CCXT](https://github.com/ccxt/ccxt) - 仮想通貨取引所API統合
- [Notion API](https://developers.notion.com) - データベース統合
- [Poetry](https://python-poetry.org) - 依存関係管理
- [Pydantic](https://pydantic.dev) - データバリデーション
- [GitHub Actions](https://github.com/features/actions) - 自動実行基盤

---

**✨ 本番運用中のプロジェクトです！ データ収集システムがリアルタイムで稼働しています**
