# import json
# import os
# from datetime import datetime, timedelta
# from typing import List, Dict
# from pydantic import Field

# from .base import class_tool_decorator_generator

# decorator, builder = class_tool_decorator_generator("Scheduler")


# # 設定存檔路徑，確保資料不會因對話結束而消失
# DB_FILE = "task_database.json"


# class Scheduler:
#     def __init__(self):
#         # 初始化時讀取或建立資料庫
#         if not os.path.exists(DB_FILE):
#             self._write_db({"fixed": [], "floating": [], "scheduled": []})

#     def _read_db(self) -> dict:
#         with open(DB_FILE, "r", encoding="utf-8") as f:
#             data = json.load(f)
#             # 將字串格式的時間轉回 datetime 物件
#             for item in data.get("fixed", []):
#                 item["start"] = datetime.fromisoformat(item["start"])
#                 item["end"] = datetime.fromisoformat(item["end"])
#             for item in data.get("scheduled", []):
#                 item["start"] = datetime.fromisoformat(item["start"])
#                 item["end"] = datetime.fromisoformat(item["end"])
#             return data

#     def _write_db(self, data: dict):
#         # 寫入前將 datetime 轉為字串格式
#         to_save = json.loads(json.dumps(data, default=str))
#         with open(DB_FILE, "w", encoding="utf-8") as f:
#             json.dump(to_save, f, ensure_ascii=False, indent=4)

#     # ===============================
#     # 第一步：讀取並分類存檔
#     # ===============================
#     @decorator
#     def ingest_data(self, items: List[dict]) -> str:
#         """
#         將輸入分類為固定事件(有start/end)或任務(有duration)。
#         """
#         db = self._read_db()
#         # 清空舊數據重新寫入，或你可以選擇 append
#         db["fixed"].clear()
#         db["floating"].clear()

#         for item in items:
#             if "start" in item and "end" in item:
#                 db["fixed"].append(
#                     {
#                         "title": item["title"],
#                         "start": datetime.strptime(item["start"], "%Y-%m-%d %H:%M"),
#                         "end": datetime.strptime(item["end"], "%Y-%m-%d %H:%M"),
#                     }
#                 )
#             else:
#                 db["floating"].append(
#                     {
#                         "title": item["title"],
#                         "duration": item.get("duration_min", 60),
#                         "priority": item.get("priority", 3),
#                     }
#                 )

#         self._write_db(db)
#         return self.show_current_status()

#     # ===============================
#     # 第二步：顯示目前資料庫內容 (解決遺忘問題)
#     # ===============================
#     def show_current_status(self) -> str:
#         """
#         【強制呼叫】顯示目前儲存在硬碟中的所有事件與任務原貌。
#         """
#         db = self._read_db()
#         output = ["### 📥 目前儲存的原始清單"]

#         if db["fixed"]:
#             output.append("\n**📌 固定行程 (不可變動):**")
#             for e in db["fixed"]:
#                 output.append(
#                     f"- {e['start'].strftime('%m/%d %H:%M')} | {e['title']}")

#         if db["floating"]:
#             output.append("\n**📝 待排任務 (可變動):**")
#             for t in db["floating"]:
#                 output.append(
#                     f"- {t['title']} ({t['duration']} min | P{t['priority']})"
#                 )

#         return "\n".join(output)

#     # ===============================
#     # 第三步：自動排程邏輯
#     # ===============================
#     @decorator
#     def process_schedule(self, start_time_str: str) -> str:
#         """
#         依照優先級將任務填入固定事件的空檔中，並儲存結果。
#         """
#         db = self._read_db()
#         current_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")

#         fixed_sorted = sorted(db["fixed"], key=lambda x: x["start"])
#         tasks_sorted = sorted(
#             db["floating"], key=lambda x: x["priority"], reverse=True)

#         scheduled_tasks = []

#         for task in tasks_sorted:
#             duration = timedelta(minutes=task["duration"])

#             # 尋找不衝突的空檔
#             while True:
#                 task_start = current_time
#                 task_end = current_time + duration

#                 conflict = False
#                 # 檢查是否撞到固定行程
#                 for f in fixed_sorted:
#                     if task_start < f["end"] and task_end > f["start"]:
#                         current_time = f["end"] + timedelta(minutes=10)
#                         conflict = True
#                         break

#                 if not conflict:
#                     scheduled_tasks.append(
#                         {
#                             "title": task["title"],
#                             "start": task_start,
#                             "end": task_end,
#                             "type": "TASK",
#                         }
#                     )
#                     current_time = task_end + timedelta(minutes=10)
#                     break

#         # 合併並存入資料庫
#         final = []
#         for f in fixed_sorted:
#             final.append({**f, "type": "FIXED"})
#         final.extend(scheduled_tasks)

#         db["scheduled"] = sorted(final, key=lambda x: x["start"])
#         self._write_db(db)
#         return self.render_final_view()

#     def render_final_view(self) -> str:
#         """讀取儲存的排程並生成 To-do list"""
#         db = self._read_db()
#         if not db["scheduled"]:
#             return "目前沒有排程結果。"

#         output = ["## 🗓️ 儲存的完整行程表 (12/25 - 1/19)"]
#         curr_date = None
#         for item in db["scheduled"]:
#             if item["start"].date() != curr_date:
#                 curr_date = item["start"].date()
#                 output.append(f"\n### 📅 {curr_date.strftime('%m/%d (%a)')}")

#             tag = "🔴" if item["type"] == "FIXED" else "🔵"
#             output.append(
#                 f"- {tag} {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')} | {item['title']}"
#             )

#         return "\n".join(output)


# builder(Scheduler)
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict
# 確保引入 Field 以符合 Pydantic 規範
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
        """
        將輸入的行程分類為固定事件或待排任務。
        
        Args:
            items: 包含標題、開始結束時間或持續時間的字典列表。
        """
        db = self._read_db()
        db["fixed"].clear()
        db["floating"].clear()

        for item in items:
            if "start" in item and "end" in item:
                db["fixed"].append({
                    "title": item["title"],
                    "start": datetime.strptime(item["start"], "%Y-%m-%d %H:%M"),
                    "end": datetime.strptime(item["end"], "%Y-%m-%d %H:%M"),
                })
            else:
                db["floating"].append({
                    "title": item["title"],
                    "duration": item.get("duration_min", 60),
                    "priority": item.get("priority", 3),
                })

        self._write_db(db)
        return self.show_current_status()

    @decorator
    def show_current_status(self) -> str:
        """
        顯示目前儲存在資料庫中的所有原始事件與任務清單。
        """
        db = self._read_db()
        output = ["### 📥 目前儲存的原始清單"]
        if db["fixed"]:
            output.append("\n**📌 固定行程:**")
            for e in db["fixed"]:
                output.append(f"- {e['start'].strftime('%m/%d %H:%M')} | {e['title']}")
        if db["floating"]:
            output.append("\n**📝 待排任務:**")
            for t in db["floating"]:
                output.append(f"- {t['title']} ({t['duration']} min | P{t['priority']})")
        return "\n".join(output)

    @decorator
    def process_schedule(self, start_time_str: str) -> str:
        """
        依照優先級將任務填入固定事件的空檔中，並生成最終排程。
        
        Args:
            start_time_str: 排程開始的時間點 (格式: YYYY-MM-DD HH:MM)。
        """
        db = self._read_db()
        current_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
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
                        "title": task["title"],
                        "start": task_start,
                        "end": task_end,
                        "type": "TASK",
                    })
                    current_time = task_end + timedelta(minutes=10)
                    break

        final = [{**f, "type": "FIXED"} for f in fixed_sorted]
        final.extend(scheduled_tasks)
        db["scheduled"] = sorted(final, key=lambda x: x["start"])
        self._write_db(db)
        return self.render_final_view()

    def render_final_view(self) -> str:
        """格式化排程結果為易讀的清單。"""
        db = self._read_db()
        if not db["scheduled"]: return "目前沒有排程結果。"
        output = ["## 🗓️ 儲存的完整行程表"]
        curr_date = None
        for item in db["scheduled"]:
            if item["start"].date() != curr_date:
                curr_date = item["start"].date()
                output.append(f"\n### 📅 {curr_date.strftime('%m/%d (%a)')}")
            tag = "🔴" if item["type"] == "FIXED" else "🔵"
            output.append(f"- {tag} {item['start'].strftime('%H:%M')} - {item['end'].strftime('%H:%M')} | {item['title']}")
        return "\n".join(output)

# 2. 修改重點：傳入實例化後的物件 Scheduler()
builder(Scheduler())