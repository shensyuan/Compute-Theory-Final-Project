from datetime import datetime

from pydantic import Field

from .base import class_tool_decorator_generator
from .database import read_db, write_db

decorator, builder = class_tool_decorator_generator("SaveSchedulerTools")


class SaveSchedulerTools:
    @decorator
    def save_llm_plan(
        self,
        tasks: list[dict] = Field(
            ...,
            description="LLM 生成的完整行程清單。每個 dict 需包含: title(標題), date(格式 YYYY-MM-DD), time_slot(格式 HH:mm-HH:mm), category(分類)",
        ),
    ) -> str:
        """當你（LLM）已經規劃好行程後，呼叫此工具將行程儲存至資料庫。

        注意：此工具會以傳入的清單「取代」原本的排定行程，因此每次請傳入完整的排程結果，
        而不是只傳新增的部分。固定事件（fixed）不受影響，不需要重複列入。

        Args:
            tasks: 包含標題、日期、時間段與分類的任務清單。

        Returns:
            儲存結果的成功確認訊息。
        """
        scheduled = []
        for item in tasks:
            try:
                start_str, end_str = item["time_slot"].split("-")
                scheduled.append({
                    "title": item["title"],
                    "start": datetime.strptime(f"{item['date']} {start_str.strip()}", "%Y-%m-%d %H:%M"),
                    "end": datetime.strptime(f"{item['date']} {end_str.strip()}", "%Y-%m-%d %H:%M"),
                    "type": "TASK",
                    "category": item.get("category", "規劃任務"),
                })
            except (KeyError, ValueError) as e:
                return f"❌ 儲存失敗：資料格式錯誤 ({e})。請確保 date 為 YYYY-MM-DD、time_slot 為 HH:mm-HH:mm"

        db = read_db()
        db["scheduled"] = sorted(scheduled, key=lambda x: x["start"])
        write_db(db)
        return f"✅ 已成功將 {len(scheduled)} 項計畫儲存至資料庫。"


builder(SaveSchedulerTools())
