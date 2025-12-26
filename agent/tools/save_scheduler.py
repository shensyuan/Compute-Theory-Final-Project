import json
import os
from datetime import datetime
from typing import List
from pydantic import Field

# 假設 base.py 位在相同或上層目錄
from .base import class_tool_decorator_generator

# 初始化裝飾器與建構器
decorator, builder = class_tool_decorator_generator("TaskTools")

DB_FILE = "task_database.json"

class TaskTools():
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._write_db({"fixed": [], "floating": [], "scheduled": []})

    def _read_db(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in ["fixed", "scheduled"]:
                for item in data.get(key, []):
                    item["start"] = datetime.fromisoformat(item["start"])
                    item["end"] = datetime.fromisoformat(item["end"])
            return data

    def _write_db(self, data: dict):
        to_save = json.loads(json.dumps(data, default=str))
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    @decorator
    def save_llm_plan(
        self, 
        tasks: List[dict] = Field(
            ..., 
            description="LLM 生成的行程清單。每個 dict 需包含: title(標題), date(格式 YYYY-MM-DD), time_slot(格式 HH:mm-HH:mm), category(分類)"
        )
    ) -> str:
        """當你（LLM）已經規劃好行程後，呼叫此工具將行程永久儲存至資料庫中。

        Args:
            tasks: 包含標題、日期、時間段與分類的任務清單。

        Returns:
            儲存結果的成功確認訊息。
        """
        db = self._read_db()

        for item in tasks:
            try:
                # 解析時間段，例如 "14:00-18:00"
                start_str, end_str = item["time_slot"].split("-")
                full_start = f"{item['date']} {start_str.strip()}"
                full_end = f"{item['date']} {end_str.strip()}"

                db["scheduled"].append(
                    {
                        "title": item["title"],
                        "start": datetime.strptime(full_start, "%Y-%m-%d %H:%M"),
                        "end": datetime.strptime(full_end, "%Y-%m-%d %H:%M"),
                        "type": "TASK",
                        "category": item.get("category", "規劃任務"),
                    }
                )
            except Exception as e:
                return f"❌ 儲存失敗：資料格式錯誤 ({str(e)})。請確保時間格式為 HH:mm-HH:mm"

        # 確保排序正確
        db["scheduled"] = sorted(db["scheduled"], key=lambda x: x["start"])
        self._write_db(db)
        return f"✅ 已成功將 {len(tasks)} 項計畫同步至硬碟記憶庫中。"

    @decorator
    def get_full_schedule(self) -> str:
        """讀取並列出目前資料庫中所有已排定的行程。

        Returns:
            以日期分類的格式化行程表文字。
        """
        db = self._read_db()
        if not db["scheduled"]:
            return "📭 目前記憶庫中沒有任何預定的行程。"

        output = ["## 💾 記憶庫中的實際存檔"]
        curr_date = None
        for item in db["scheduled"]:
            item_date = item["start"].date()
            if item_date != curr_date:
                curr_date = item_date
                output.append(f"\n### 📅 {curr_date.strftime('%Y/%m/%d')}")
            
            output.append(
                f"- {item['start'].strftime('%H:%M')}-{item['end'].strftime('%H:%M')} | {item['title']}"
            )
        return "\n".join(output)

# 執行 builder 將實例化後的工具註冊
builder(TaskTools())