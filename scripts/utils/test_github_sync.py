#!/usr/bin/env python3
"""
GitHub同期機能のテストスクリプト
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.github.notion_to_github import NotionToGitHubExporter


async def test_github_sync():
    """GitHub同期機能をテストする"""
    print("🧪 GitHub同期機能のテスト開始")
    print("=" * 50)
    
    try:
        # エクスポーター初期化
        exporter = NotionToGitHubExporter()
        print(f"✅ エクスポーター初期化成功")
        
        # 出力ディレクトリの確認
        if exporter.output_dir.exists():
            print(f"✅ 出力ディレクトリ存在: {exporter.output_dir}")
        else:
            print(f"📁 出力ディレクトリ作成: {exporter.output_dir}")
        
        if exporter.history_dir.exists():
            print(f"✅ 履歴ディレクトリ存在: {exporter.history_dir}")
        else:
            print(f"📁 履歴ディレクトリ作成: {exporter.history_dir}")
        
        print("\n🔄 Notionからデータ取得をテスト中...")
        
        # NotionデータをGitHubに同期
        result = await exporter.export_to_github()
        
        print("\n🎉 同期完了!")
        print(f"📊 結果:")
        print(f"  - 総取引所数: {result['total_exchanges']}")
        print(f"  - 成功取引所数: {result['successful_exchanges']}")
        print(f"  - タイムスタンプ: {result['timestamp']}")
        
        print(f"\n📁 生成ファイル:")
        print(f"  - メイン: {result['main_file']}")
        print(f"  - 履歴: {result['history_file']}")  
        print(f"  - JSON: {result['json_file']}")
        
        # ファイル存在確認
        files_to_check = [
            result['main_file'],
            result['history_file'], 
            result['json_file']
        ]
        
        print(f"\n🔍 ファイル存在確認:")
        for file_path in files_to_check:
            if Path(file_path).exists():
                size = Path(file_path).stat().st_size
                print(f"  ✅ {file_path} ({size:,} bytes)")
            else:
                print(f"  ❌ {file_path}")
        
        # JSONファイル内容確認
        json_path = Path(result['json_file'])
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            print(f"\n📄 JSONファイル内容:")
            print(f"  - タイムスタンプ: {json_data['timestamp']}")
            print(f"  - 総取引所数: {json_data['total_exchanges']}")
            print(f"  - 成功取引所数: {json_data['successful_exchanges']}")
            
            if json_data['exchanges']:
                sample_exchange = json_data['exchanges'][0]
                print(f"  - サンプル取引所: {sample_exchange['exchange']}")
        
        print("\n✅ 全てのテスト完了!")
        return True
        
    except Exception as e:
        print(f"\n❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """ファイル構造をテストする"""
    print("\n🗂️  ファイル構造テスト")
    print("-" * 30)
    
    expected_dirs = [
        "docs/exchange-data",
        "docs/exchange-data/history"
    ]
    
    expected_files = [
        "src/github/notion_to_github.py",
        "scripts/github-sync/export_notion_to_github.py",
        "scripts/complete-survey-and-sync.py",
        ".github/workflows/sync-notion-to-github.yml"
    ]
    
    # ディレクトリ確認
    for dir_path in expected_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  ✅ {dir_path}/")
        else:
            print(f"  ❌ {dir_path}/")
    
    # ファイル確認
    for file_path in expected_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")


async def main():
    """メイン関数"""
    print("🚀 GitHub同期機能テスト開始")
    
    # ファイル構造テスト
    test_file_structure()
    
    # 実際の同期テスト
    success = await test_github_sync()
    
    if success:
        print(f"\n🎊 全テスト成功!")
        sys.exit(0)
    else:
        print(f"\n💥 テスト失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())