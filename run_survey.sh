#!/bin/bash
# 102取引所調査実行スクリプト

echo "🚀 全102取引所の調査を開始します"
echo "⏱️  この処理には10-20分程度かかります"
echo ""

# Poetryが利用可能か確認
if command -v poetry &> /dev/null; then
    echo "✅ Poetry環境で実行します"
    poetry run python scripts/survey_all_102_exchanges.py
else
    echo "⚠️  Poetryが見つかりません。直接Pythonで実行を試みます"
    
    # Python3が利用可能か確認
    if command -v python3 &> /dev/null; then
        echo "✅ Python3で実行します"
        python3 scripts/survey_all_102_exchanges.py
    else
        echo "❌ Python3が見つかりません"
        echo "以下のコマンドを手動で実行してください："
        echo ""
        echo "poetry run python scripts/survey_all_102_exchanges.py"
        echo ""
        echo "または："
        echo ""
        echo "python3 scripts/survey_all_102_exchanges.py"
        exit 1
    fi
fi