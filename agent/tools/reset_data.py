from .base import class_tool_decorator_generator
from .database import EMPTY_DB, write_db

decorator, builder = class_tool_decorator_generator("DatabaseManagementTools")


class DatabaseManagementTools:
    @decorator
    def reset_all_data(self) -> str:
        """【危險操作】永久清空資料庫中所有固定行程、彈性任務以及已排定的計畫。

        當使用者明確表示「想重新開始」、「清空所有資料」或「刪除所有行程」時，請呼叫此功能。
        呼叫前請確認使用者已知悉此操作不可復原。

        Returns:
            清空成功後的確認訊息與後續操作指引。
        """
        write_db(EMPTY_DB)

        return (
            "🧹 資料庫已徹底清空。\n\n"
            "目前的狀態是全新的。你可以開始：\n"
            "1. 透過 `ingest_data` 存入新的固定行程或彈性任務。\n"
            "2. 告訴我你的新目標，讓我重新為你規劃時間表。"
        )


builder(DatabaseManagementTools())
