#!/usr/bin/env python3
"""
Poetry無しで直接実行するためのラッパースクリプト
"""
import subprocess
import sys
import os

# プロジェクトルートに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Python環境をチェック
print("🔍 Python環境を確認中...")
print(f"Python version: {sys.version}")

try:
    # 必要なモジュールをインポートテスト
    import ccxt
    import loguru
    import notion_client
    print("✅ 必要なパッケージが見つかりました")
except ImportError as e:
    print(f"❌ 必要なパッケージが不足しています: {e}")
    print("\n以下のコマンドでインストールしてください：")
    print("pip install ccxt loguru notion-client python-dotenv")
    sys.exit(1)

# 並列調査スクリプトを実行
print("\n🚀 102取引所の並列調査を開始します...")
try:
    subprocess.run([sys.executable, "scripts/survey_all_102_parallel.py"], check=True)
except subprocess.CalledProcessError as e:
    print(f"❌ エラーが発生しました: {e}")
    sys.exit(1)