import json
import os
from datetime import datetime
from typing import List, Dict
from pydantic import Field

# 假設 base.py 位於相同路徑
from .base import class_tool_decorator_generator

# 初始化裝飾器與建構器
decorator, builder = class_tool_decorator_generator("ScheduleQueryTools")

DB_FILE = "task_database.json"

class ScheduleQueryTools():
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._write_db({"fixed": [], "floating": [], "scheduled": []})

    def _read_db(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 確保時間格式正確轉換
            for key in ["fixed", "scheduled"]:
                for item in data.get(key, []):
                    if isinstance(item.get("start"), str):
                        item["start"] = datetime.fromisoformat(item["start"])
                    if isinstance(item.get("end"), str):
                        item["end"] = datetime.fromisoformat(item["end"])
            return data

    def _write_db(self, data: dict):
        # 存檔前轉回字串格式
        to_save = json.loads(json.dumps(data, default=str))
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    @decorator
    def get_full_schedule(self) -> str:
        """從資料庫中提取目前所有已排定的行程（包含固定事件與彈性任務）。
        
        當使用者詢問「我接下來要做什麼？」或「看看我的排程」時，請呼叫此工具。

        Returns:
            以日期分類、具備圖標區分的視覺化行程清單。
        """
        db = self._read_db()
        if not db["scheduled"]:
            return "📭 目前檔案中沒有排程資料。建議你可以先儲存一些新的計畫。"

        output = ["## 💾 完整整合行程表"]
        curr_date = None
        for item in db["scheduled"]:
            date = item["start"].date()
            if date != curr_date:
                curr_date = date
                output.append(f"\n### 📅 {date.strftime('%m/%d (%a)')}")

            # 區分固定事件(Red)與已排定任務(Blue)
            icon = "🔴" if item.get("type") == "FIXED" else "🔵"
            cat = item.get("category", "一般")
            output.append(
                f"- {icon} {item['start'].strftime('%H:%M')}-{item['end'].strftime('%H:%M')} | 【{cat}】{item['title']}"
            )

        return (
            "\n".join(output) + 
            "\n\n請根據以上排程，為使用者提供摘要或提醒接下來最重要的事項。"
        )

    @decorator
    def get_schedule_by_category(
        self, 
        target_category: str = Field(..., description="要查詢的特定分類名稱，例如：讀書、工作、運動")
    ) -> str:
        """只過濾並顯示特定分類的行程。
        
        當使用者想針對特定領域（如工作進度）進行回顧時，使用此工具。

        Args:
            target_category: 分類標籤名稱。

        Returns:
            該分類下的所有相關行程摘要。
        """
        db = self._read_db()
        # 模糊搜尋分類名稱
        filtered = [
            i
            for i in db.get("scheduled", [])
            if target_category.lower() in i.get("category", "").lower()
        ]

        if not filtered:
            return f"🔎 找不到與「{target_category}」相關的行程。請確認關鍵字是否正確。"

        output = [f"## 📂 分類查詢結果：{target_category}"]
        for item in filtered:
            output.append(
                f"- {item['start'].strftime('%m/%d %H:%M')} | {item['title']}"
            )

        return (
            "\n".join(output) + 
            f"\n\n以上是關於「{target_category}」的查詢結果，請以此回覆使用者。"
        )

# 執行註冊
builder(ScheduleQueryTools())