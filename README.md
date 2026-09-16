# Compute Theory Final Project — LLM 排程助理 Discord Bot

一個以 **Discord** 為介面、以 **Ollama LLM API** 的個人排程 Agent。
使用者在 Discord 中 @bot 用自然語言描述行程或任務，LLM 透過 **tool calling** 讀寫本地 JSON 資料庫，
完成「記錄 → 規劃 → 儲存 → 查詢 → 修改」的完整流程，也能順便推薦晚餐。

## 功能

| 使用者說 | Agent 做的事 |
|---|---|
| 「下週三 14:00-16:00 有計算理論期末考」 | 呼叫 `ingest_data` 存成固定事件 |
| 「幫我排 3 小時讀微算機，週五前完成」 | 存成彈性任務 → LLM 依現有行程規劃時段 → `save_llm_plan` 儲存 |
| 「看看我的行程」／「列出讀書相關的行程」 | `get_full_schedule` / `get_schedule_by_category` |
| 「把慢跑改成 45 分鐘」 | `update_item_properties`，並重新評估排程 |
| 「清空所有行程」 | `reset_all_data`（會先確認） |
| 「今天想吃清爽一點的，預算 150」 | `get_dinner_recommendation` |
| `help`／`ping`／`reset` | 快速指令，不經過 LLM |

若使用者要排彈性任務但沒給「預計總時數」或「預計完成日期」，Agent 會先反問而不是自行假設。

## 專案架構

```
Test/
├── main.py                  # 進入點：載入 .env、設定 logging、啟動 bot
├── bot.py                   # Discord 介面層：@mention 過濾、快速指令、呼叫 agent、回覆分段
├── agent/
│   ├── agent.py             # LLM 核心：per-channel 對話歷史、system prompt、tool-calling 迴圈
│   └── tools/
│       ├── __init__.py      # 自動載入本目錄所有工具模組
│       ├── base.py          # 把 Python 函式轉成 Ollama Tool 並註冊（decorator / builder）
│       ├── database.py      # 共用 JSON 資料層（datetime ↔ ISO 字串）
│       ├── classify_data.py # ingest_data
│       ├── save_scheduler.py# save_llm_plan
│       ├── get_schedule.py  # get_full_schedule / get_schedule_by_category
│       ├── update.py        # update_item_properties
│       ├── reset_data.py    # reset_all_data
│       └── eat.py           # get_dinner_recommendation
├── task_database.json       # 排程資料庫
├── requirements.txt
└── .env.example
```

### 工具註冊機制

每個工具模組用 `class_tool_decorator_generator("ClassName")` 取得一組 `(decorator, builder)`：
`@decorator` 標記要暴露給 LLM 的方法，`builder(instance)` 在實例化後把 bound method 註冊進
`tool_list`（給 Ollama 的 schema）與 `func_map`（實際可呼叫的函式），名稱為 `ClassName.method`。
方法的 docstring 與 `pydantic.Field(description=...)` 會自動變成工具說明與參數描述。
`agent/tools/__init__.py` 會自動 import 目錄下所有模組，新增工具只需新增一個檔案。

### 對話與 Tool-calling 迴圈（`agent/agent.py`）

1. 依 Discord `channel_id` 保存對話歷史（最多 20 則），每次請求動態產生含**現在日期時間**的 system prompt。
2. 呼叫 `client.chat(..., tools=tool_list, think=True)`。
3. 若回應含 `tool_calls`，逐一執行並以 `role="tool"` 回傳結果，再次呼叫 LLM；最多 10 回合。
4. 工具執行失敗時把錯誤字串交給 LLM 自行修正，不會讓 bot 中斷。
5. 回傳最終文字；若 API 失敗則拋出例外，由 `bot.py` 改成錯誤提示並回滾該則訊息。

## 安裝與執行

需求：Python 3.13

```bash
git clone https://github.com/shensyuan/Compute-Theory-Final-Project.git
cd Compute-Theory-Final-Project
python -m venv .venv
.venv\Scripts\activate          # Windows；macOS/Linux 用 source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # 填入 TOKEN / OLLAMA_TOKEN / OLLAMA_API_ENDPOINT / OLLAMA_MODEL
python main.py
```

Discord Developer Portal 需開啟 **Message Content Intent**，並以 `bot` scope 邀請機器人進伺服器。

## Demo 腳本

```
@Bot help
@Bot 下週三 14:00-16:00 有計算理論期末考
@Bot 幫我排 3 小時讀微算機，週五前完成          ← Agent 會規劃時段並儲存
@Bot 看看我的行程                             ← 固定事件 + 排定任務
@Bot 把讀微算機改成 4 小時                      ← 修改後重新評估
@Bot 今天想吃清爽一點的，預算 150
@Bot 清空所有行程
```

## 使用的技術

- [py-cord](https://github.com/Pycord-Development/pycord) — Discord API
- [ollama-python](https://github.com/ollama/ollama-python) — LLM API 與 tool schema 轉換
- [pydantic](https://docs.pydantic.dev/) — 參數描述與型別
- [python-dotenv](https://github.com/theskumar/python-dotenv) — 環境變數
