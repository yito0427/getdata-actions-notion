# 🚀 GitHub Actions セットアップガイド

## 概要

このプロジェクトは、15分間隔でGitHub Actionsが自動実行され、仮想通貨データをNotionに蓄積するように設計されています。

## 🔧 セットアップ手順

### 1. GitHub Secrets の設定

リポジトリの設定で以下のSecretsを追加してください：

#### 必須のSecrets

| Secret名 | 説明 | 取得方法 |
|----------|------|----------|
| `NOTION_API_KEY` | Notion統合APIキー | [Notion Integrations](https://www.notion.so/my-integrations)で作成 |
| `NOTION_DATABASE_ID` | NotionデータベースまたはページID | NotionページのURLから抽出 |

#### Secrets設定手順

1. GitHubリポジトリの `Settings` → `Secrets and variables` → `Actions`
2. `New repository secret` をクリック
3. 上記のSecret名と値を入力して保存

### 2. Notion統合の準備

#### 2.1 Notion APIキーの取得

1. [Notion Integrations](https://www.notion.so/my-integrations) にアクセス
2. 「New integration」をクリック
3. 統合名を入力（例：`Crypto Data Collector`）
4. 生成されたAPIキーをコピー → `NOTION_API_KEY` として設定

#### 2.2 Notionデータベースのセットアップ

**オプション1: 既存データベースを使用**
```
1. 既存のNotionデータベースページを開く
2. URLからデータベースIDを取得
3. データベースページで統合を追加：
   - ページ右上の「・・・」→「Add connections」
   - 作成した統合を選択
```

**オプション2: 新しいページを作成**
```
1. 新しいNotionページを作成
2. ページIDを取得（新しいデータベースが自動作成されます）
3. ページで統合を追加
```

### 3. ワークフロー実行スケジュール

#### メインデータ収集ワークフロー
- **ファイル**: `.github/workflows/crypto-data-collection.yml`
- **実行間隔**: 15分ごと（`*/15 * * * *`）
- **処理内容**: 
  - 優先取引所（最大10取引所）からデータ収集
  - Notion API制限に最適化された0.5 RPS でアップロード
  - エラー時の自動Issue作成

#### テストワークフロー
- **ファイル**: `.github/workflows/test-crypto-collection.yml`
- **実行タイミング**: プルリクエスト時、手動実行
- **処理内容**: 
  - 複数Pythonバージョンでのテスト
  - 異なる取引所設定でのテスト
  - 出力ファイルの検証

## 📊 Notion API使用量の最適化

### 制限値と設計

| 項目 | Notion制限 | 設計値 | 安全マージン |
|------|------------|--------|--------------|
| 同時リクエスト | 3 req/sec | 0.5 req/sec | 83% |
| 15分間ウィンドウ | 2,700 requests | 2,160 requests | 20% |
| 1日のリクエスト | ~259,200 | ~207,360 | 20% |

### 実行パターン

```bash
# 15分間隔で1日実行
96回/日 × 10取引所 × 1リクエスト = 960リクエスト/日
```

- **同時実行制限**: 最大3つの取引所を並行処理
- **レート制限**: 0.5秒間隔でAPIリクエスト
- **バッチ処理**: 10取引所ずつをバッチで処理

## 🚀 ワークフローの手動実行

### データ収集の手動実行

```yaml
# GitHub Actions画面で手動実行
workflow_dispatch:
  inputs:
    exchanges_limit: "20"    # 取引所数を指定
    test_mode: false         # テストモードOFF
```

### テスト実行

```yaml
# テスト用パラメータ
workflow_dispatch:
  inputs:
    test_exchanges: "binance,coinbase,kraken"
```

## 📈 監視とメンテナンス

### 成功時のログ

```
✅ Crypto data collection completed successfully
📅 Timestamp: 2024-01-15 12:15:00 UTC
🔄 Next run: 2024-01-15 12:30:00 UTC
Optimized upload complete: 8/10 exchanges
Total duration: 45.2s
Rate limiting stats: 65.3% utilization
```

### エラー時の対応

1. **自動Issue作成**: ワークフロー失敗時に詳細なIssueが自動作成
2. **ログ確認**: GitHub Actions画面でエラーログを確認
3. **API制限チェック**: Notion APIの制限状況を確認
4. **取引所APIチェック**: 各取引所APIの稼働状況を確認

### 週次レポート

- **実行タイミング**: 毎週日曜日 9:00 UTC
- **内容**: 
  - 週間データ収集サマリー
  - API使用率分析
  - パフォーマンス最適化提案

## 🔧 トラブルシューティング

### よくある問題

#### 1. Notion API認証エラー
```
❌ Error: Unauthorized (401)
```
**解決方法**: 
- Notion統合のAPIキーを確認
- データベースに統合のアクセス権があるか確認

#### 2. レート制限エラー
```
❌ Error: Rate limited (429)
```
**解決方法**: 
- ワークフローの実行間隔を延長（20分〜30分）
- 取引所数を減少（limit: 5-8）

#### 3. 取引所API接続エラー
```
❌ Exchange 'binance' failed: Connection timeout
```
**解決方法**: 
- 特定の取引所をスキップリストに追加
- リトライ回数を増加

### 設定の調整

#### 実行頻度の変更
```yaml
# .github/workflows/crypto-data-collection.yml
schedule:
  - cron: '*/20 * * * *'  # 20分間隔に変更
```

#### 取引所数の調整
```yaml
# ワークフロー内の環境変数
env:
  EXCHANGES_LIMIT: '5'  # 5取引所に制限
```

#### レート制限の調整
```yaml
env:
  RATE_LIMIT_PER_SECOND: '0.3'  # より保守的な設定
```

## 📊 パフォーマンス指標

### 目標値

- **成功率**: 95%以上
- **1回の実行時間**: 60秒以内
- **API使用率**: 80%以下
- **エラー率**: 5%以下

### モニタリング方法

1. **GitHub Actions実行履歴**: 成功/失敗の傾向を確認
2. **Notion データベース**: 実際に蓄積されたデータ量
3. **週次レポート**: 自動生成される分析レポート
4. **Issue tracking**: 自動作成されるエラーレポート

## 🚀 本番環境での最適化

### 推奨設定（本番運用）

```yaml
# 本番運用時の推奨パラメータ
EXCHANGES_LIMIT: 10
RATE_LIMIT_PER_SECOND: 0.5
MAX_CONCURRENT_EXCHANGES: 3
CRON_SCHEDULE: "*/15 * * * *"
```

### スケーリング戦略

1. **段階的拡張**: 最初は5取引所 → 10取引所 → 15取引所
2. **地域別分散**: 日本、アメリカ、ヨーロッパの取引所を分散
3. **時間帯別最適化**: 市場活発時間に合わせた頻度調整

## 📞 サポート

問題が発生した場合：

1. [GitHub Issues](../../issues) で報告
2. ワークフローログの詳細を添付
3. Notion APIの使用状況を確認
4. 取引所別のエラー状況を記載