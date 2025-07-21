#!/usr/bin/env python3
"""
Notionデータベースの内容をGitHubリポジトリに同期するスクリプト
実行の度にファイルを更新し、履歴も保存する
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.github.notion_to_github import NotionToGitHubExporter


async def main():
    """メイン実行関数"""
    print("🚀 Notion → GitHub 同期を開始します...")
    print("=" * 50)
    
    try:
        # エクスポート実行
        exporter = NotionToGitHubExporter()
        result = await exporter.export_to_github()
        
        print("=" * 50)
        print("🎉 同期完了!")
        print(f"📊 {result['successful_exchanges']}/{result['total_exchanges']} 取引所のデータを記録")
        print()
        print("📁 生成されたファイル:")
        print(f"  - メイン結果: {result['main_file']}")
        print(f"  - 履歴ファイル: {result['history_file']}")
        print(f"  - JSONファイル: {result['json_file']}")
        print()
        print("💡 次のステップ:")
        print("  git add docs/exchange-data/")
        print("  git commit -m 'update: Notionデータをバックアップ'")
        print("  git push")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())