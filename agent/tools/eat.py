from .base import class_tool_decorator_generator

decorator, builder = class_tool_decorator_generator("EatDinnerTools")


class EatDinnerTools:
    def __init__(self):
        self.food_database = {
            "台式": ["滷肉飯", "牛肉麵", "丹丹漢堡", "鹹酥雞"],
            "日式": ["拉麵", "壽司", "丼飯", "烏龍麵"],
            "西式": ["披薩", "漢堡", "義大利麵", "牛排"],
            "健康": ["溫沙拉", "水煮餐", "地中海料理"],
        }

    @decorator
    def get_dinner_recommendation(
        self,
        preference: str,
        budget: str,
    ) -> str:
        """將美食資料庫提供給 LLM，由 LLM 根據使用者偏好與預算進行邏輯判斷與推薦。

        Args:
            preference: 使用者的具體口味偏好或目前的心情
            budget: 使用者的預算或對餐廳等級的要求

        Returns:
            適合給使用者的食物
        """
        db_context = "\n".join(
            f"- {category}: {', '.join(items)}"
            for category, items in self.food_database.items()
        )

        # 不直接決定答案，把資料交給 LLM 做「推薦」這個推理步驟
        return (
            f"以下是可用的美食資料庫：\n{db_context}\n\n"
            f"使用者偏好是「{preference}」，預算為「{budget}」。\n"
            "請從資料庫中挑選『最合適的一個』選項，並解釋為什麼這個選項符合他的需求。"
        )


builder(EatDinnerTools())
