import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import Field

# 假設 base.py 位於相同目錄結構
from .base import class_tool_decorator_generator

# 初始化裝飾器與建構器
decorator, builder = class_tool_decorator_generator("TaskUpdateTools")

DB_FILE = "task_database.json"

class TaskUpdateTools():
    def __init__(self):
        if not os.path.exists(DB_FILE):
            self._write_db({"fixed": [], "floating": [], "scheduled": []})

    def _read_db(self) -> dict:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in ["fixed", "scheduled"]:
                for item in data.get(key, []):
                    if isinstance(item.get("start"), str):
                        item["start"] = datetime.fromisoformat(item["start"])
                    if isinstance(item.get("end"), str):
                        item["end"] = datetime.fromisoformat(item["end"])
            return data

    def _write_db(self, data: dict):
        to_save = json.loads(json.dumps(data, default=str))
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(to_save, f, ensure_ascii=False, indent=4)

    @decorator
    def update_item_properties(
        self,
        title: str = Field(..., description="要修改的任務或事件名稱關鍵字"),
        new_duration_min: int = Field(None, description="新的執行分鐘數 (彈性任務適用)"),
        new_priority: int = Field(None, description="新的優先級 1-5 (彈性任務適用)"),
        new_category: str = Field(None, description="新的分類名稱"),
        new_start: str = Field(None, description="新的開始時間 YYYY-MM-DD HH:MM (固定事件適用)"),
        new_end: str = Field(None, description="新的結束時間 YYYY-MM-DD HH:MM (固定事件適用)"),
    ) -> str:
        """修改資料庫中既存項目（固定事件或彈性任務）的屬性。
        
        修改後，你應重新評估目前的排程方案是否仍然最佳，並視情況建議使用者進行調整。

        Args:
            title: 用於搜尋項目的標題關鍵字。
            new_duration_min: 更新任務所需時間。
            new_priority: 更新優先權。
            new_category: 更新類別。
            new_start: 更新固定行程的開始點。
            new_end: 更新固定行程的結束點。

        Returns:
            修改結果描述與 Agent 的行動指引。
        """
        db = self._read_db()
        found = False
        
        # 遍歷固定與彈性清單進行更新
        for collection_key in ["fixed", "floating"]:
            for item in db[collection_key]:
                if title.lower() in item["title"].lower():
                    if new_category: item["category"] = new_category
                    
                    if collection_key == "fixed":
                        if new_start: item["start"] = datetime.strptime(new_start, "%Y-%m-%d %H:%M")
                        if new_end: item["end"] = datetime.strptime(new_end, "%Y-%m-%d %H:%M")
                    else:
                        if new_duration_min: item["duration"] = new_duration_min
                        if new_priority: item["priority"] = new_priority
                    
                    found = True

        if not found:
            return f"❌ 找不到包含「{title}」的項目，請確認名稱是否正確。"

        self._write_db(db)

        # 仿照 DinnerTools 的結構化回傳，引導 LLM 下一步
        return (
            f"✅ 已成功更新「{title}」的相關屬性。\n\n"
            "由於項目屬性已更動，請你執行以下邏輯判斷：\n"
            "1. 檢查此更動是否與現有的其他行程產生『時間重疊』或『邏輯衝突』。\n"
            "2. 如果有必要，請根據新的優先級或時長，為使用者提出一個優化後的排程建議。\n"
            "3. 確認無誤後，可呼叫 `save_llm_plan` 更新最終排程表。"
        )

# 執行註冊
builder(TaskUpdateTools())