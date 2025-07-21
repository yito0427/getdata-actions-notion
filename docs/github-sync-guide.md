# Notion → GitHub 同期ガイド

## 概要

このプロジェクトでは、NotionデータベースのデータをGitHubリポジトリに同期し、履歴管理を行う機能を提供しています。

## 🎯 機能

1. **NotionからGitHubエクスポート**: Notionデータベースの内容をMarkdown形式でエクスポート
2. **履歴管理**: 実行の度に日時付きの履歴ファイルを作成
3. **自動同期**: GitHub Actionsによる定期実行
4. **マニュアル実行**: ローカルでの手動実行も可能

## 📁 生成されるファイル構造

```
docs/exchange-data/
├── README.md                     # サマリーファイル
├── exchange-survey-results.md    # 最新の詳細結果
├── latest-survey-data.json       # プログラム利用用JSON
└── history/                      # 履歴ディレクトリ
    ├── survey_20240121_143022.md # 日時付き履歴ファイル
    ├── survey_20240121_093015.md
    └── ...
```

## 🚀 使用方法

### 1. 手動でNotion同期を実行

```bash
# Notion → GitHub 同期のみ実行
poetry run python scripts/github-sync/export_notion_to_github.py

# 完全な調査 + Notion更新 + GitHub同期を実行
poetry run python scripts/complete-survey-and-sync.py
```

### 2. GitHub Actionsでの自動実行

- **定期実行**: 毎週日曜日 9:00（JST）に自動実行
- **手動実行**: GitHub Actions画面から「Run workflow」で実行可能

### 3. ローカル開発での活用

```python
# Python スクリプトから利用
from src.github.notion_to_github import NotionToGitHubExporter

exporter = NotionToGitHubExporter()
result = await exporter.export_to_github()
print(f"成功: {result['successful_exchanges']} 取引所")
```

## 📊 データ形式

### メインファイル (exchange-survey-results.md)

- 最新の調査結果の詳細
- 成功した取引所の一覧と詳細情報
- APIサンプルコードと実データ
- 失敗した取引所の情報

### 履歴ファイル (history/survey_YYYYMMDD_HHMMSS.md)

- 特定時点での調査結果のスナップショット
- 全取引所の詳細情報
- 実行時のタイムスタンプ

### JSONファイル (latest-survey-data.json)

```json
{
  "timestamp": "2024-01-21 14:30:22",
  "total_exchanges": 102,
  "successful_exchanges": 95,
  "exchanges": [
    {
      "exchange": "binance",
      "total_tickers": 2543,
      "record_count": 4,
      "status": "Success",
      "content": "..."
    }
  ]
}
```

## 🔧 設定

### 必要な環境変数

```env
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_database_id
```

### GitHub Secrets（GitHub Actions用）

GitHub リポジトリの Settings → Secrets and variables → Actions で設定：

- `NOTION_API_KEY`: Notion APIキー
- `NOTION_DATABASE_ID`: NotionデータベースID

## 📈 活用例

### 1. データの変化追跡

```bash
# 今日と1週間前の結果を比較
diff docs/exchange-data/history/survey_20240114_*.md docs/exchange-data/history/survey_20240121_*.md
```

### 2. 取引所の追加・削除の確認

```bash
# 成功した取引所数の推移
grep "成功取引所数" docs/exchange-data/history/*.md
```

### 3. APIの変更検出

```bash
# 特定の取引所のAPIデータ変化を確認
grep -A 20 "### binance" docs/exchange-data/history/survey_20240121_*.md
```

### 4. プログラムでの統計分析

```python
import json
import glob
from datetime import datetime

# 全履歴の成功率推移を分析
history_files = glob.glob("docs/exchange-data/history/*.json")
for file in sorted(history_files):
    with open(file) as f:
        data = json.load(f)
    success_rate = data['successful_exchanges'] / data['total_exchanges']
    print(f"{data['timestamp']}: {success_rate:.1%}")
```

## 🛠️ トラブルシューティング

### よくあるエラー

1. **Notion API エラー**
   ```
   notion_client.errors.APIResponseError: Invalid database_id
   ```
   → NOTION_DATABASE_IDを確認してください

2. **認証エラー**
   ```
   notion_client.errors.APIResponseError: Unauthorized
   ```
   → NOTION_API_KEYが正しく設定されているか確認

3. **ファイル権限エラー**
   ```
   PermissionError: [Errno 13] Permission denied
   ```
   → スクリプトが実行可能か確認: `chmod +x scripts/github-sync/*.py`

### デバッグ方法

```bash
# 詳細ログで実行
LOG_LEVEL=DEBUG poetry run python scripts/github-sync/export_notion_to_github.py

# Notionデータベースの確認
poetry run python -c "from src.config import get_config; print(get_config().NOTION_DATABASE_ID)"
```

## 🔄 定期メンテナンス

1. **古い履歴ファイルのクリーンアップ**
   ```bash
   # 30日以上古い履歴ファイルを削除
   find docs/exchange-data/history/ -name "survey_*.md" -mtime +30 -delete
   ```

2. **大きなファイルのチェック**
   ```bash
   # 1MB以上のファイルを確認
   find docs/exchange-data/ -size +1M -ls
   ```

3. **GitHubリポジトリサイズの監視**
   - 履歴ファイルが蓄積されるため、定期的なサイズ確認を推奨

## 📚 関連ドキュメント

- [プロジェクト構造](project-structure.md)
- [取引所調査ガイド](guides/exchange-survey.md)
- [README](../README.md)