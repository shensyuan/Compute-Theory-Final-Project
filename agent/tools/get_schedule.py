from pydantic import Field

from .base import class_tool_decorator_generator
from .database import read_db

decorator, builder = class_tool_decorator_generator("ScheduleQueryTools")


def _all_events(db: dict) -> list[dict]:
    """合併固定行程（type=FIXED）與 LLM 排定的行程（type=TASK），依開始時間排序。"""
    fixed = [{**item, "type": "FIXED"} for item in db.get("fixed", [])]
    scheduled = [{**item, "type": item.get("type", "TASK")} for item in db.get("scheduled", [])]
    return sorted(fixed + scheduled, key=lambda x: x["start"])


class ScheduleQueryTools:
    @decorator
    def get_full_schedule(self) -> str:
        """列出目前所有行程，包含使用者的固定事件與 LLM 已排定的任務。

        當使用者詢問「我接下來要做什麼？」或「看看我的排程」時，請呼叫此工具。

        Returns:
            以日期分類、具備圖標區分（🔴 固定事件 / 🔵 排定任務）的行程清單。
        """
        db = read_db()
        events = _all_events(db)
        if not events:
            floating = db.get("floating", [])
            if floating:
                titles = "、".join(t["title"] for t in floating)
                return f"📭 目前沒有已排定的行程，但有 {len(floating)} 個彈性任務尚未排程：{titles}。"
            return "📭 目前資料庫中沒有任何行程。建議你可以先儲存一些新的計畫。"

        output = ["## 💾 完整整合行程表"]
        current_date = None
        for item in events:
            date = item["start"].date()
            if date != current_date:
                current_date = date
                output.append(f"\n### 📅 {date.strftime('%m/%d (%a)')}")

            icon = "🔴" if item["type"] == "FIXED" else "🔵"
            category = item.get("category", "一般")
            output.append(
                f"- {icon} {item['start'].strftime('%H:%M')}-{item['end'].strftime('%H:%M')} | 【{category}】{item['title']}"
            )

        return (
            "\n".join(output)
            + "\n\n請根據以上排程，為使用者提供摘要或提醒接下來最重要的事項。"
        )

    @decorator
    def get_schedule_by_category(
        self,
        target_category: str = Field(..., description="要查詢的特定分類名稱，例如：讀書、工作、運動"),
    ) -> str:
        """只過濾並顯示特定分類的行程（固定事件與排定任務皆包含）。

        當使用者想針對特定領域（如工作進度）進行回顧時，使用此工具。

        Args:
            target_category: 分類標籤名稱。

        Returns:
            該分類下的所有相關行程摘要。
        """
        db = read_db()
        keyword = target_category.lower()
        filtered = [
            item for item in _all_events(db)
            if keyword in item.get("category", "").lower()
        ]

        if not filtered:
            return f"🔎 找不到與「{target_category}」相關的行程。請確認關鍵字是否正確。"

        output = [f"## 📂 分類查詢結果：{target_category}"]
        for item in filtered:
            icon = "🔴" if item["type"] == "FIXED" else "🔵"
            output.append(f"- {icon} {item['start'].strftime('%m/%d %H:%M')} | {item['title']}")

        return (
            "\n".join(output)
            + f"\n\n以上是關於「{target_category}」的查詢結果，請以此回覆使用者。"
        )


builder(ScheduleQueryTools())
