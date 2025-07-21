#!/usr/bin/env python3
"""
完全な調査とGitHub同期を実行するスクリプト

1. 102取引所の並列調査を実行
2. 結果をNotionにアップロード
3. NotionデータをGitHubに同期
4. 自動でGitコミット・プッシュ（オプション）
"""

import asyncio
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートを sys.path に追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def run_command(command: str, description: str):
    """コマンドを実行して結果を表示"""
    print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ {description} 完了")
        if result.stdout:
            print(f"   出力: {result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失敗: {e}")
        if e.stderr:
            print(f"   エラー: {e.stderr.strip()}")
        return False


async def main():
    """メイン実行関数"""
    print("🚀 完全な取引所調査とGitHub同期を開始します")
    print("=" * 60)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ステップ1: 取引所調査の実行
    print(f"📊 ステップ1: 102取引所の並列調査")
    success = await run_command(
        "poetry run python scripts/survey/survey_all_102_parallel.py",
        "102取引所の並列調査"
    )
    
    if not success:
        print("❌ 調査に失敗しました。処理を中断します。")
        sys.exit(1)
    
    # ステップ2: Notionにアップロード
    print(f"\n📤 ステップ2: Notionへの詳細アップロード")
    success = await run_command(
        "poetry run python scripts/notion-upload/upload_survey_detailed.py",
        "Notionへの詳細アップロード"
    )
    
    if not success:
        print("⚠️  Notionアップロードに失敗しましたが、GitHub同期は継続します")
    
    # ステップ3: NotionからGitHubへの同期
    print(f"\n🔄 ステップ3: NotionからGitHubへの同期")
    success = await run_command(
        "poetry run python scripts/github-sync/export_notion_to_github.py",
        "NotionからGitHubへの同期"
    )
    
    if not success:
        print("❌ GitHub同期に失敗しました")
        sys.exit(1)
    
    # ステップ4: Gitコミット（オプション）
    print(f"\n📝 ステップ4: Git変更の確認")
    
    # Git statusを確認
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if result.stdout.strip():
        print("📋 変更されたファイル:")
        print(result.stdout)
        
        # ユーザーに確認
        while True:
            response = input("\n🤔 これらの変更をコミットしますか？ (y/n/skip): ").lower()
            
            if response in ['y', 'yes']:
                # Git add
                await run_command(
                    "git add docs/exchange-data/ output/",
                    "変更ファイルをステージング"
                )
                
                # Git commit
                commit_message = f"update: 取引所調査結果を更新 ({timestamp})"
                await run_command(
                    f'git commit -m "{commit_message}"',
                    "変更をコミット"
                )
                
                # Git push確認
                push_response = input("🚀 変更をプッシュしますか？ (y/n): ").lower()
                if push_response in ['y', 'yes']:
                    await run_command(
                        "git push origin main",
                        "変更をプッシュ"
                    )
                break
                
            elif response in ['n', 'no', 'skip']:
                print("⏭️  コミットをスキップします")
                break
                
            else:
                print("❓ 'y' または 'n' を入力してください")
    else:
        print("ℹ️  変更されたファイルはありません")
    
    print("=" * 60)
    print("🎉 全ての処理が完了しました！")
    print(f"⏰ 実行時刻: {timestamp}")
    print()
    print("📁 生成されたファイル:")
    print("  - docs/exchange-data/exchange-survey-results.md (最新結果)")
    print("  - docs/exchange-data/history/survey_YYYYMMDD_HHMMSS.md (履歴)")
    print("  - docs/exchange-data/latest-survey-data.json (JSON)")
    print("  - output/exchange_survey_parallel.json (調査生データ)")


if __name__ == "__main__":
    asyncio.run(main())