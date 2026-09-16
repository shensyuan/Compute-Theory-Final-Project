"""所有排程工具共用的 JSON 資料層。

資料庫結構::

    {
        "fixed":     [{"title", "start", "end", "category"}],           # 使用者的固定行程
        "floating":  [{"title", "duration", "priority", "category"}],   # 尚未排入時間的彈性任務
        "scheduled": [{"title", "start", "end", "type", "category"}]    # LLM 排好的最終行程
    }

檔案內 ``start`` / ``end`` 以 ISO 8601 字串儲存，讀入時轉成 ``datetime``。
"""

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path

# 專案根目錄（Test/）下的 task_database.json，不依賴執行時的工作目錄
DB_PATH = Path(__file__).resolve().parents[2] / "task_database.json"

EMPTY_DB: dict[str, list] = {"fixed": [], "floating": [], "scheduled": []}

_DATETIME_KEYS = ("start", "end")
_DATETIME_COLLECTIONS = ("fixed", "scheduled")


def read_db() -> dict:
    """讀取資料庫；檔案不存在時自動建立空資料庫。"""
    if not DB_PATH.exists():
        write_db(EMPTY_DB)
        return deepcopy(EMPTY_DB)

    with DB_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    for collection in _DATETIME_COLLECTIONS:
        for item in data.get(collection, []):
            for key in _DATETIME_KEYS:
                if isinstance(item.get(key), str):
                    item[key] = datetime.fromisoformat(item[key])
    return data


def write_db(data: dict) -> None:
    """將資料庫寫回磁碟，``datetime`` 會被序列化為 ISO 8601 字串。"""
    serializable = json.loads(json.dumps(data, default=_serialize))
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=4)


def _serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
