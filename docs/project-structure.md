# プロジェクト構造

## 概要

このプロジェクトは学習用の仮想通貨取引所API調査システムです。102の取引所から取得可能なデータを調査し、Notionデータベースに記録します。

## ディレクトリ構造

```
getdata-actions-notion/
├── src/                           # ソースコード
│   ├── collectors/                # データ収集モジュール
│   │   ├── base.py               # 基底コレクタークラス
│   │   └── manager.py            # 収集マネージャー
│   ├── notion/                    # Notion統合モジュール
│   │   ├── realdata_uploader.py  # 実データアップローダー
│   │   ├── enhanced_uploader.py  # 拡張アップローダー
│   │   ├── simple_uploader.py    # シンプルアップローダー
│   │   ├── direct_uploader.py    # 直接アップローダー
│   │   ├── database_manager.py   # データベース管理
│   │   ├── rate_limiter.py       # レート制限
│   │   └── uploader.py           # 基本アップローダー
│   ├── utils/                     # ユーティリティ
│   │   ├── csv_writer.py         # CSV出力
│   │   └── notion_to_csv.py      # NotionからCSVエクスポート
│   ├── models.py                  # データモデル定義
│   ├── config.py                  # 設定管理
│   └── main.py                    # メインエントリーポイント
│
├── scripts/                       # 実行スクリプト
│   ├── survey/                    # 取引所調査
│   │   ├── explore_all_exchanges.py
│   │   ├── survey_all_102_exchanges.py
│   │   └── survey_all_102_parallel.py ★推奨
│   ├── notion-upload/             # Notionアップロード
│   │   ├── upload_survey_to_notion.py
│   │   └── upload_survey_detailed.py  ★推奨
│   └── utils/                     # ユーティリティ
│       └── test_*.py              # 各種テストスクリプト
│
├── docs/                          # ドキュメント
│   ├── guides/                    # ガイド文書
│   │   └── exchange-survey.md    # 取引所調査ガイド
│   ├── project-structure.md      # プロジェクト構造（本ファイル）
│   ├── exchange-survey-guide.md  # 調査ガイド
│   └── realdata-implementation.md # 実装詳細
│
├── .github/                       # GitHub設定
│   └── workflows/                 # GitHub Actions
│       ├── crypto-data-collection.yml # データ収集（定期実行無効）
│       └── exchange-survey.yml    # 取引所調査（手動実行）
│
├── output/                        # 出力ディレクトリ
│   └── exchange_survey_parallel.json # 調査結果
│
├── data/                          # データディレクトリ
├── logs/                          # ログディレクトリ
│
├── pyproject.toml                 # Poetry設定
├── poetry.lock                    # 依存関係ロック
├── requirements.txt               # pip用依存関係
├── Makefile                       # 開発用コマンド
├── .env.example                   # 環境変数テンプレート
├── .gitignore                     # Git除外設定
├── README.md                      # プロジェクトREADME
└── CLAUDE.md                      # Claude開発ガイド
```

## 主要コンポーネント

### 1. データ収集 (src/collectors/)
- **BaseCollector**: CCXT を使用した取引所データ収集の基底クラス
- **ExchangeCollectorManager**: 複数取引所の並列データ収集を管理

### 2. Notion統合 (src/notion/)
- **RealDataNotionUploader**: 実際の価格データをJSON形式で保存
- **各種アップローダー**: 用途別のデータアップロード実装

### 3. スクリプト (scripts/)
- **survey/**: 取引所調査スクリプト群
- **notion-upload/**: Notionへのデータアップロードスクリプト
- **utils/**: テストとユーティリティスクリプト

### 4. ドキュメント (docs/)
- プロジェクトの使用方法
- 実装の詳細
- ガイドとチュートリアル

## データフロー

```
1. 取引所調査実行
   scripts/survey/survey_all_102_parallel.py
   ↓
2. 結果をJSONに保存
   output/exchange_survey_parallel.json
   ↓
3. Notionにアップロード
   scripts/notion-upload/upload_survey_detailed.py
   ↓
4. Notionデータベース
   各取引所の詳細情報（APIサンプル、実データ含む）
```

## 環境設定

### 必要な環境変数
```env
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
LOG_LEVEL=INFO
```

### 依存関係管理
- **Poetry**: 推奨される依存関係管理ツール
- **pip**: requirements.txt も提供

## 開発ガイドライン

1. **コーディング規約**
   - Python PEP 8 準拠
   - 型ヒント使用
   - 日本語コメント可

2. **テスト**
   - scripts/utils/ 内のテストスクリプトを使用
   - 新機能追加時はテストスクリプトも作成

3. **ドキュメント**
   - 新機能追加時は docs/ に文書を追加
   - README.md の更新を忘れずに