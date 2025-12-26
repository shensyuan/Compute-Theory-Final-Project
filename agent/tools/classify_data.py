import json
import os
from datetime import datetime
from typing import Annotated
from pydantic import Field

# 假設 base.py 在同一個包結構中
from .base import class_tool_decorator_generator

# 初始化裝飾器與建構器
decorator, builder = class_tool_decorator_generator("ScheduleTools")

DB_FILE = "task_database.json"


class ScheduleTools():
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._write_db({"fixed": [], "floating": [], "scheduled": []})

    def _read_db(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 轉換字串回 datetime 物件供程式處理
            for key in ["fixed", "scheduled"]:
                for item in data.get(key, []):
                    if isinstance(item.get("start"), str):
                        item["start"] = datetime.fromisoformat(item["start"])
                    if isinstance(item.get("end"), str):
                        item["end"] = datetime.fromisoformat(item["end"])
            return data

    def _write_db(self, data: dict):
        # 存入時將 datetime 轉回字串
        to_save = json.loads(json.dumps(data, default=str))
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    @decorator
    def ingest_data(
        self,
        items: list[dict] = Field(
            ...,
            description="待存入的項目清單。固定事件需 start/end，彈性任務需 duration_min。"
        ),
    ) -> str:
        """將使用者提供的原始任務或固定行程存入底層資料庫。

        存入後，LLM 應讀取目前資料庫狀態，並根據這些資訊進行時間排程規劃。

        Args:
            items: 包含標題、類別與時間資訊的字典清單。
                  - 固定事件範例: {"title": "會議", "start": "2025-01-01 09:00", "end": "2025-01-01 10:00", "category": "工作"}
                  - 彈性任務範例: {"title": "慢跑", "duration_min": 30, "priority": 1, "category": "健康"}

        Returns:
            儲存成功訊息與後續操作指引。
        """
        db = self._read_db()
        count = 0
        for item in items:
            cat = item.get("category", "未分類")
            try:
                if "start" in item and "end" in item:
                    db["fixed"].append({
                        "title": item["title"],
                        "start": datetime.strptime(item["start"], "%Y-%m-%d %H:%M"),
                        "end": datetime.strptime(item["end"], "%Y-%m-%d %H:%M"),
                        "category": cat,
                    })
                else:
                    db["floating"].append({
                        "title": item["title"],
                        "duration": item.get("duration_min", 60),
                        "priority": item.get("priority", 3),
                        "category": cat,
                    })
                count += 1
            except Exception as e:
                return f"❌ 解析項目 '{item.get('title')}' 時發生錯誤: {str(e)}"

        self._write_db(db)

        # 這裡模仿 DinnerTools 回傳結構化資訊給 LLM
        return (
            f"✅ 已成功將 {count} 個項目存入資料庫。\n\n"
            "現在請你執行以下步驟：\n"
            "1. 綜合目前的『固定行程』與『彈性任務』。\n"
            "2. 判斷是否有時間衝突，並為彈性任務分配最適合的時間段。\n"
            "3. 完成排程後，請呼叫 `save_llm_plan` 工具正式儲存你的排程結果。"
        )


# 註冊工具
builder(ScheduleTools())
