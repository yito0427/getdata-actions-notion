# Scripts Directory Structure

このディレクトリには、仮想通貨取引所データの調査・収集・アップロードに関するスクリプトが含まれています。

## 📁 ディレクトリ構成

```
scripts/
├── survey/                     # 取引所調査スクリプト
│   ├── explore_all_exchanges.py      # 基本的な取引所調査
│   ├── survey_all_102_exchanges.py   # 全102取引所の順次調査
│   └── survey_all_102_parallel.py    # 全102取引所の並列調査（推奨）
│
├── notion-upload/              # Notionアップロードスクリプト
│   ├── upload_survey_to_notion.py    # 調査結果の基本アップロード
│   └── upload_survey_detailed.py     # APIサンプル付き詳細アップロード（推奨）
│
├── github-sync/                # GitHub同期スクリプト 🆕
│   └── export_notion_to_github.py    # NotionからGitHubへの同期
│
├── complete-survey-and-sync.py # 完全実行スクリプト（推奨）🆕
│
└── utils/                      # ユーティリティスクリプト
    ├── test_realdata.py             # 実データテスト
    ├── test_enhanced_uploader.py    # アップローダーテスト
    ├── test_csv_export.py           # CSVエクスポートテスト
    └── test_github_sync.py          # GitHub同期テスト 🆕
```

## 🚀 使用方法

### 🌟 推奨：完全実行（一括処理）

```bash
# 調査 → Notionアップロード → GitHub同期 を一括実行
poetry run python scripts/complete-survey-and-sync.py
```

### 個別実行

#### 1. 取引所調査の実行

```bash
# 全102取引所を並列で調査（推奨、約2-5分）
poetry run python scripts/survey/survey_all_102_parallel.py

# 調査結果は output/exchange_survey_parallel.json に保存されます
```

#### 2. Notionへのアップロード

```bash
# APIサンプルコード付きで詳細情報をアップロード（推奨）
poetry run python scripts/notion-upload/upload_survey_detailed.py

# 基本情報のみアップロード（軽量版）
poetry run python scripts/notion-upload/upload_survey_to_notion.py
```

#### 3. GitHub同期 🆕

```bash
# NotionデータをGitHubに同期
poetry run python scripts/github-sync/export_notion_to_github.py
```

#### 4. テスト実行

```bash
# GitHub同期機能のテスト
poetry run python scripts/utils/test_github_sync.py
```

## 📊 各スクリプトの詳細

### survey/survey_all_102_parallel.py
- **目的**: 102の取引所を並列で調査
- **処理時間**: 約2-5分
- **同時実行数**: 最大20取引所
- **出力**: `output/exchange_survey_parallel.json`

### notion-upload/upload_survey_detailed.py
- **目的**: 調査結果をNotionに詳細情報付きで保存
- **含まれる情報**:
  - APIサンプルコード（Python + CCXT）
  - 実際に取得したデータサンプル
  - 生のJSONレスポンス例
  - API機能の利用可能性
- **レート制限**: 0.5秒/レコード

### github-sync/export_notion_to_github.py 🆕
- **目的**: NotionデータをGitHubリポジトリに同期
- **出力ファイル**:
  - `docs/exchange-data/exchange-survey-results.md` (最新結果)
  - `docs/exchange-data/history/survey_YYYYMMDD_HHMMSS.md` (履歴)
  - `docs/exchange-data/latest-survey-data.json` (JSON形式)
- **履歴管理**: 実行の度に日時付きファイルを作成

### complete-survey-and-sync.py 🆕
- **目的**: 調査からGitHub同期まで一括実行
- **処理フロー**:
  1. 102取引所の並列調査
  2. Notionへの詳細アップロード  
  3. GitHub同期とファイル生成
  4. Git変更の確認とコミット（オプション）
- **対話式**: ユーザー確認付きでコミット・プッシュ

## 🔧 カスタマイズ

### 調査する取引所数を制限する場合

`survey_all_102_parallel.py` の以下の行を編集：
```python
# 全102取引所を並列調査（最大20同時実行）
results = await explorer.explore_all_exchanges_parallel(max_concurrent=20)
```

### 特定の取引所のみ調査する場合

新しいスクリプトを作成するか、既存のスクリプトを修正して取引所リストを指定：
```python
explorer.exchanges = ["binance", "coinbase", "kraken"]  # 調査したい取引所のみ
```

## ⚠️ 注意事項

1. **API制限**: 各取引所にはレート制限があります
2. **Notion API制限**: 3リクエスト/秒の制限があるため、アップロード時は適切な待機時間を設定
3. **エラーハンドリング**: 一部の取引所はAPIキーが必要、または地域制限がある場合があります