"""
NotionデータベースをGitHub用マークダウンファイルとしてエクスポートする機能
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from notion_client import Client
from ..config import get_config


class NotionToGitHubExporter:
    """NotionデータをGitHub記録用にエクスポートするクラス"""
    
    def __init__(self):
        """初期化"""
        config = get_config()
        self.notion_client = Client(auth=config.NOTION_API_KEY)
        self.database_id = config.NOTION_DATABASE_ID
        self.output_dir = Path("docs/exchange-data")
        self.history_dir = Path("docs/exchange-data/history")
        
        # ディレクトリ作成
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_to_github(self) -> Dict[str, Any]:
        """NotionデータをGitHub用ファイルとしてエクスポート"""
        print("🔄 NotionデータベースからGitHubエクスポートを開始...")
        
        # Notionデータベースを取得
        pages = await self._fetch_all_pages()
        
        # タイムスタンプ
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # メインファイルを生成
        main_content = self._generate_main_markdown(pages, date_str)
        main_file = self.output_dir / "exchange-survey-results.md"
        
        # 履歴ファイルを生成
        history_content = self._generate_history_markdown(pages, date_str)
        history_file = self.history_dir / f"survey_{timestamp_str}.md"
        
        # ファイル出力
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            f.write(history_content)
        
        # サマリーファイル更新
        await self._update_summary_file(pages, timestamp)
        
        # JSONファイルも出力（プログラム利用用）
        json_file = self.output_dir / "latest-survey-data.json"
        json_data = {
            "timestamp": date_str,
            "total_exchanges": len(pages),
            "successful_exchanges": len([p for p in pages if p.get('status') == 'Success']),
            "exchanges": pages
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        result = {
            "timestamp": date_str,
            "main_file": str(main_file),
            "history_file": str(history_file),
            "json_file": str(json_file),
            "total_exchanges": len(pages),
            "successful_exchanges": len([p for p in pages if p.get('status') == 'Success'])
        }
        
        print(f"✅ エクスポート完了: {len(pages)}取引所のデータを記録")
        return result
    
    async def _fetch_all_pages(self) -> List[Dict[str, Any]]:
        """Notionデータベースから全ページを取得"""
        pages = []
        has_more = True
        start_cursor = None
        
        while has_more:
            query_params = {
                "database_id": self.database_id,
                "page_size": 100
            }
            
            if start_cursor:
                query_params["start_cursor"] = start_cursor
            
            response = self.notion_client.databases.query(**query_params)
            
            for page in response["results"]:
                page_data = self._extract_page_data(page)
                pages.append(page_data)
            
            has_more = response["has_more"]
            start_cursor = response.get("next_cursor")
        
        return pages
    
    def _extract_page_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Notionページからデータを抽出"""
        properties = page.get("properties", {})
        
        # プロパティ値を抽出
        exchange_name = self._get_property_value(properties.get("Exchange"))
        total_tickers = self._get_property_value(properties.get("Total Tickers"))
        record_count = self._get_property_value(properties.get("Record Count"))
        status = self._get_property_value(properties.get("Status"))
        
        # ページ内容も取得
        page_content = self._fetch_page_content(page["id"])
        
        return {
            "page_id": page["id"],
            "exchange": exchange_name or "Unknown",
            "total_tickers": total_tickers or 0,
            "record_count": record_count or 0,
            "status": status or "Unknown",
            "content": page_content,
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time")
        }
    
    def _get_property_value(self, prop: Optional[Dict[str, Any]]) -> Any:
        """Notionプロパティ値を取得"""
        if not prop:
            return None
        
        prop_type = prop.get("type")
        
        if prop_type == "title":
            return prop["title"][0]["text"]["content"] if prop["title"] else None
        elif prop_type == "rich_text":
            return prop["rich_text"][0]["text"]["content"] if prop["rich_text"] else None
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "select":
            return prop["select"]["name"] if prop.get("select") else None
        
        return None
    
    def _fetch_page_content(self, page_id: str) -> str:
        """ページの内容を取得してマークダウンに変換"""
        try:
            blocks = self.notion_client.blocks.children.list(block_id=page_id)
            content_parts = []
            
            for block in blocks["results"]:
                content_part = self._convert_block_to_markdown(block)
                if content_part:
                    content_parts.append(content_part)
            
            return "\n\n".join(content_parts)
        except Exception as e:
            return f"コンテンツ取得エラー: {str(e)}"
    
    def _convert_block_to_markdown(self, block: Dict[str, Any]) -> str:
        """NotionブロックをMarkdownに変換"""
        block_type = block.get("type")
        
        if block_type == "paragraph":
            text = self._extract_rich_text(block["paragraph"]["rich_text"])
            return text
        elif block_type == "heading_1":
            text = self._extract_rich_text(block["heading_1"]["rich_text"])
            return f"# {text}"
        elif block_type == "heading_2":
            text = self._extract_rich_text(block["heading_2"]["rich_text"])
            return f"## {text}"
        elif block_type == "heading_3":
            text = self._extract_rich_text(block["heading_3"]["rich_text"])
            return f"### {text}"
        elif block_type == "code":
            code = self._extract_rich_text(block["code"]["rich_text"])
            language = block["code"]["language"]
            return f"```{language}\n{code}\n```"
        elif block_type == "bulleted_list_item":
            text = self._extract_rich_text(block["bulleted_list_item"]["rich_text"])
            return f"- {text}"
        
        return ""
    
    def _extract_rich_text(self, rich_text_array: List[Dict[str, Any]]) -> str:
        """リッチテキスト配列から文字列を抽出"""
        return "".join([text["text"]["content"] for text in rich_text_array])
    
    def _generate_main_markdown(self, pages: List[Dict[str, Any]], timestamp: str) -> str:
        """メイン結果ファイルのMarkdownを生成"""
        successful_pages = [p for p in pages if p.get('status') == 'Success']
        failed_pages = [p for p in pages if p.get('status') != 'Success']
        
        content = f"""# 🏦 仮想通貨取引所API調査結果

**最終更新**: {timestamp}  
**調査取引所数**: {len(pages)}  
**成功**: {len(successful_pages)} | **失敗**: {len(failed_pages)}

## 📊 調査サマリー

| 項目 | 値 |
|------|-----|
| 総調査取引所数 | {len(pages)} |
| 成功した取引所 | {len(successful_pages)} |
| 失敗した取引所 | {len(failed_pages)} |
| 成功率 | {len(successful_pages)/len(pages)*100:.1f}% |

## ✅ 成功した取引所一覧

"""

        # 成功した取引所の詳細
        for page in successful_pages:
            exchange = page['exchange']
            tickers = page['total_tickers']
            record_count = page['record_count']
            
            content += f"""### {exchange}
- **マーケット数**: {tickers}
- **利用可能データタイプ数**: {record_count}

{page['content'][:500]}...

---

"""

        # 失敗した取引所
        if failed_pages:
            content += f"""## ❌ 失敗した取引所

"""
            for page in failed_pages:
                exchange = page['exchange']
                content += f"- **{exchange}** (Status: {page['status']})\n"

        content += f"""
---

## 📁 関連ファイル

- [調査履歴](history/) - 過去の調査結果
- [JSONデータ](latest-survey-data.json) - プログラム利用用のJSONファイル
- [プロジェクトREADME](../../README.md) - プロジェクト概要

**生成日時**: {timestamp}
"""

        return content
    
    def _generate_history_markdown(self, pages: List[Dict[str, Any]], timestamp: str) -> str:
        """履歴ファイルのMarkdownを生成"""
        successful_pages = [p for p in pages if p.get('status') == 'Success']
        
        content = f"""# 取引所調査結果 - {timestamp}

## 調査概要
- **実行日時**: {timestamp}
- **総取引所数**: {len(pages)}
- **成功取引所数**: {len(successful_pages)}

## 詳細結果

"""

        for page in pages:
            exchange = page['exchange']
            status = page['status']
            tickers = page['total_tickers']
            record_count = page['record_count']
            
            content += f"""### {exchange}
- **ステータス**: {status}
- **マーケット数**: {tickers}
- **データタイプ数**: {record_count}

"""

            if page['content']:
                content += f"""{page['content']}

---

"""

        return content
    
    async def _update_summary_file(self, pages: List[Dict[str, Any]], timestamp: datetime):
        """サマリーファイルを更新"""
        summary_file = self.output_dir / "README.md"
        
        # 履歴ディレクトリから過去の結果を取得
        history_files = list(self.history_dir.glob("survey_*.md"))
        history_files.sort(reverse=True)
        
        successful_count = len([p for p in pages if p.get('status') == 'Success'])
        
        content = f"""# 取引所調査データ

このディレクトリには、仮想通貨取引所API調査の結果が保存されています。

## 最新結果

- **最終実行**: {timestamp.strftime("%Y-%m-%d %H:%M:%S")}
- **調査取引所数**: {len(pages)}
- **成功取引所数**: {successful_count}
- **成功率**: {successful_count/len(pages)*100:.1f}%

## ファイル構成

- [`exchange-survey-results.md`](exchange-survey-results.md) - 最新の調査結果（詳細）
- [`latest-survey-data.json`](latest-survey-data.json) - プログラム利用用JSONファイル
- [`history/`](history/) - 過去の調査結果履歴

## 調査履歴

"""

        # 履歴ファイルのリスト
        for i, history_file in enumerate(history_files[:10]):  # 最新10件
            file_name = history_file.name
            timestamp_part = file_name.replace("survey_", "").replace(".md", "")
            try:
                file_timestamp = datetime.strptime(timestamp_part, "%Y%m%d_%H%M%S")
                formatted_time = file_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                content += f"- [{formatted_time}](history/{file_name})\n"
            except ValueError:
                content += f"- [{file_name}](history/{file_name})\n"

        if len(history_files) > 10:
            content += f"\n... および他 {len(history_files) - 10} 件\n"

        content += """
## 活用方法

1. **最新データの確認**: `exchange-survey-results.md` を参照
2. **プログラムでの利用**: `latest-survey-data.json` を読み込み
3. **履歴の比較**: `history/` 内の過去ファイルと比較
4. **新しい調査実行**: プロジェクトルートでスクリプトを実行

"""

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(content)


async def main():
    """メイン実行関数"""
    exporter = NotionToGitHubExporter()
    result = await exporter.export_to_github()
    
    print(f"""
🎉 NotionからGitHubエクスポート完了!

📁 生成ファイル:
- メインファイル: {result['main_file']}
- 履歴ファイル: {result['history_file']}  
- JSONファイル: {result['json_file']}

📊 統計:
- 総取引所数: {result['total_exchanges']}
- 成功取引所数: {result['successful_exchanges']}
""")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())