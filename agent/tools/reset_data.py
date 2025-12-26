import json
import os
from datetime import datetime
from pydantic import Field

# 假設 base.py 位在相同或上層目錄
from .base import class_tool_decorator_generator

# 初始化裝飾器與建構器
decorator, builder = class_tool_decorator_generator("DatabaseManagementTools")

DB_FILE = "task_database.json"

class DatabaseManagementTools():
    def __init__(self):
        # 初始化資料庫文件
        if not os.path.exists(DB_FILE):
            self._write_db({"fixed": [], "floating": [], "scheduled": []})

    def _write_db(self, data: dict):
        """內部的資料庫寫入方法。"""
        # 使用 default=str 處理 datetime 物件
        to_save = json.loads(json.dumps(data, default=str))
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    @decorator
    def reset_all_data(self) -> str:
        """【危險操作】永久清空資料庫中所有儲存的固定行程、彈性任務以及已排定的計畫。
        
        當使用者明確表示「想重新開始」、「清空所有資料」或「刪除所有行程」時，請呼叫此功能。
        呼叫前請確認使用者已知悉此操作不可復原。

        Returns:
            清空成功後的確認訊息與後續操作指引。
        """
        empty_db = {"fixed": [], "floating": [], "scheduled": []}
        self._write_db(empty_db)
        
        # 仿照範本，回傳結構化回饋
        return (
            "🧹 記憶庫已徹底清空。\n\n"
            "目前的狀態是全新的。你可以開始：\n"
            "1. 透過 `ingest_data` 存入新的固定行程或彈性任務。\n"
            "2. 告訴我你的新目標，讓我重新為你規劃時間表。"
        )

# 執行 builder 將實例化後的工具註冊
builder(DatabaseManagementTools())