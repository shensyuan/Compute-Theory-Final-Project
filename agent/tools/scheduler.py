import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
from pydantic import Field

from .base import class_tool_decorator_generator

# 1. 產生裝飾器與建構器
decorator, builder = class_tool_decorator_generator("Scheduler")

DB_FILE = "task_database.json"

class Scheduler:
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._write_db({"fixed": [], "floating": [], "scheduled": []})

    def _read_db(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("fixed", []):
                item["start"] = datetime.fromisoformat(item["start"])
                item["end"] = datetime.fromisoformat(item["end"])
            for item in data.get("scheduled", []):
                item["start"] = datetime.fromisoformat(item["start"])
                item["end"] = datetime.fromisoformat(item["end"])
            return data

    def _write_db(self, data: dict):
        to_save = json.loads(json.dumps(data, default=str))
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    @decorator
    def ingest_data(self, items: List[dict]) -> str:
        """將使用者提供的混亂行程進行初步分類，並存入排程資料庫。

        Args:
            items: 包含行程資訊的清單，每個項目應有 title，並視情況提供 start/end 或 duration_min。
        """
        db = self._read_db()
        db["fixed"].clear()
        db["floating"].clear()

        for item in items:
            title = item.get("title", "未命名行程")
            if "start" in item and "end" in item:
                try:
                    db["fixed"].append({
                        "title": title,
                        "start": datetime.strptime(item["start"], "%Y-%m-%d %H:%M"),
                        "end": datetime.strptime(item["end"], "%Y-%m-%d %H:%M"),
                    })
                except Exception: continue
            else:
                db["floating"].append({
                    "title": title,
                    "duration": item.get("duration_min", 60),
                    "priority": item.get("priority", 3),
                })

        self._write_db(db)
        
        # 模仿 eat.py 的回傳邏輯：將狀態餵回給 LLM，由 LLM 決定下一步
        fixed_list = [f"{i['start'].strftime('%m/%d %H:%M')} | {i['title']}" for i in db["fixed"]]
        floating_list = [f"{i['title']} (需時 {i['duration']} 分鐘)" for i in db["floating"]]
        
        return (
            f"### 行程資料庫已更新 ###\n"
            f"固定行程：{', '.join(fixed_list) if fixed_list else '無'}\n"
            f"待排任務：{', '.join(floating_list) if floating_list else '無'}\n\n"
            "請根據上述資料，確認是否需要呼叫 `process_schedule` 來自動生成最佳時間表。"
        )

    @decorator
    def process_schedule(self, start_time_str: str) -> str:
        """執行自動排程演算法，將任務填入固定行程的空隙中。

        Args:
            start_time_str: 排程開始的時間點，格式為 'YYYY-MM-DD HH:MM'。
        """
        db = self._read_db()
        try:
            current_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        except:
            return "錯誤：時間格式應為 YYYY-MM-DD HH:MM。"

        fixed_sorted = sorted(db["fixed"], key=lambda x: x["start"])
        tasks_sorted = sorted(db["floating"], key=lambda x: x["priority"], reverse=True)

        scheduled_tasks = []
        for task in tasks_sorted:
            duration = timedelta(minutes=task["duration"])
            while True:
                task_start = current_time
                task_end = current_time + duration
                conflict = False
                for f in fixed_sorted:
                    if task_start < f["end"] and task_end > f["start"]:
                        current_time = f["end"] + timedelta(minutes=10)
                        conflict = True
                        break
                if not conflict:
                    scheduled_tasks.append({
                        "title": task["title"], "start": task_start, "end": task_end, "type": "TASK"
                    })
                    current_time = task_end + timedelta(minutes=10)
                    break

        final = [{**f, "type": "FIXED"} for f in fixed_sorted]
        final.extend(scheduled_tasks)
        db["scheduled"] = sorted(final, key=lambda x: x["start"])
        self._write_db(db)

        # 回傳給 LLM 讓它做最後的呈現
        res = "\n".join([f"- {i['start'].strftime('%H:%M')} - {i['end'].strftime('%H:%M')} | {i['title']}" for i in db["scheduled"]])
        return f"自動排程計算完畢。以下是結果：\n{res}\n\n請向使用者解釋這個排程的邏輯與順序。"

# 關鍵：實例化對象傳入 builder
builder(Scheduler())