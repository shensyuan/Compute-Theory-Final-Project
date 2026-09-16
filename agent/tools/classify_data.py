from datetime import datetime

from pydantic import Field

from .base import class_tool_decorator_generator
from .database import read_db, write_db

decorator, builder = class_tool_decorator_generator("TaskClassifyTools")

TIME_FORMAT = "%Y-%m-%d %H:%M"


class TaskClassifyTools:
    @decorator
    def ingest_data(
        self,
        items: list[dict] = Field(
            ...,
            description="""包含標題、類別與時間資訊的字典清單。
- 固定事件範例: {"title": "會議", "start": "2025-01-01 09:00", "end": "2025-01-01 10:00", "category": "工作"}
- 彈性任務範例: {"title": "慢跑", "duration_min": 30, "priority": 1, "category": "健康"}""",
        ),
    ) -> str:
        """將使用者提供的固定行程或彈性任務存入資料庫。

        有 start / end 的項目視為固定事件，其餘視為需要被排程的彈性任務。
        存入後，你應讀取目前資料庫狀態，為彈性任務規劃時間並呼叫 save_llm_plan 儲存。

        Returns:
            儲存成功訊息與後續操作指引。
        """
        db = read_db()
        count = 0
        for item in items:
            category = item.get("category", "未分類")
            try:
                if "start" in item and "end" in item:
                    db["fixed"].append({
                        "title": item["title"],
                        "start": datetime.strptime(item["start"], TIME_FORMAT),
                        "end": datetime.strptime(item["end"], TIME_FORMAT),
                        "category": category,
                    })
                else:
                    db["floating"].append({
                        "title": item["title"],
                        "duration": item.get("duration_min", 60),
                        "priority": item.get("priority", 3),
                        "category": category,
                    })
                count += 1
            except (KeyError, ValueError) as e:
                return f"❌ 解析項目 '{item.get('title')}' 時發生錯誤: {e}"

        write_db(db)

        return (
            f"✅ 已成功將 {count} 個項目存入資料庫。\n\n"
            "現在請你執行以下步驟：\n"
            "1. 綜合目前的『固定行程』與『彈性任務』。\n"
            "2. 判斷是否有時間衝突，並為彈性任務分配最適合的時間段。\n"
            "3. 完成排程後，請呼叫 `save_llm_plan` 工具正式儲存你的排程結果。"
        )


builder(TaskClassifyTools())
