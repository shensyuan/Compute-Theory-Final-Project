from datetime import datetime

from pydantic import Field

from .base import class_tool_decorator_generator
from .database import read_db, write_db

decorator, builder = class_tool_decorator_generator("TaskUpdateTools")

TIME_FORMAT = "%Y-%m-%d %H:%M"


class TaskUpdateTools:
    @decorator
    def update_item_properties(
        self,
        title: str = Field(..., description="要修改的任務或事件名稱關鍵字"),
        new_duration_min: int | None = Field(None, description="新的執行分鐘數 (彈性任務適用)"),
        new_priority: int | None = Field(None, description="新的優先級 1-5 (彈性任務適用)"),
        new_category: str | None = Field(None, description="新的分類名稱"),
        new_start: str | None = Field(None, description="新的開始時間 YYYY-MM-DD HH:MM (固定事件適用)"),
        new_end: str | None = Field(None, description="新的結束時間 YYYY-MM-DD HH:MM (固定事件適用)"),
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
        db = read_db()
        keyword = title.lower()
        found = False

        try:
            for item in db["fixed"]:
                if keyword in item["title"].lower():
                    found = True
                    if new_category:
                        item["category"] = new_category
                    if new_start:
                        item["start"] = datetime.strptime(new_start, TIME_FORMAT)
                    if new_end:
                        item["end"] = datetime.strptime(new_end, TIME_FORMAT)

            for item in db["floating"]:
                if keyword in item["title"].lower():
                    found = True
                    if new_category:
                        item["category"] = new_category
                    if new_duration_min:
                        item["duration"] = new_duration_min
                    if new_priority:
                        item["priority"] = new_priority
        except ValueError as e:
            return f"❌ 時間格式錯誤 ({e})，請使用 YYYY-MM-DD HH:MM。"

        if not found:
            return f"❌ 找不到包含「{title}」的項目，請確認名稱是否正確。"

        write_db(db)

        return (
            f"✅ 已成功更新「{title}」的相關屬性。\n\n"
            "由於項目屬性已更動，請你執行以下邏輯判斷：\n"
            "1. 檢查此更動是否與現有的其他行程產生『時間重疊』或『邏輯衝突』。\n"
            "2. 如果有必要，請根據新的優先級或時長，為使用者提出一個優化後的排程建議。\n"
            "3. 確認無誤後，可呼叫 `save_llm_plan` 更新最終排程表（請傳入完整排程）。"
        )


builder(TaskUpdateTools())
