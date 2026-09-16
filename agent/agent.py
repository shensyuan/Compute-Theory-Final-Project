"""LLM agent 核心：維護每個頻道的對話歷史，並執行 tool-calling 迴圈。"""

import logging
from datetime import datetime
from os import getenv

from ollama import AsyncClient, ChatResponse, Message

from .tools import func_map, tool_list

log = logging.getLogger(__name__)

# 每個頻道保留的對話訊息數（不含 system prompt），避免 context 無限成長
MAX_HISTORY = 20
# 單次請求最多允許的 tool-calling 回合數，避免模型無限呼叫工具
MAX_TOOL_ROUNDS = 10

_WEEKDAYS = ("星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日")

# channel_id -> 該頻道的 user / assistant 對話紀錄
_histories: dict[int, list[Message]] = {}


class AgentConfigError(RuntimeError):
    """缺少必要的環境變數。"""


def _settings() -> tuple[str, str, str]:
    """在呼叫時才讀取環境變數，確保 ``load_dotenv()`` 已經執行過。"""
    token = getenv("OLLAMA_TOKEN")
    endpoint = getenv("OLLAMA_API_ENDPOINT")
    model = getenv("OLLAMA_MODEL")
    missing = [
        name
        for name, value in (
            ("OLLAMA_TOKEN", token),
            ("OLLAMA_API_ENDPOINT", endpoint),
            ("OLLAMA_MODEL", model),
        )
        if not value
    ]
    if missing:
        raise AgentConfigError(f"缺少環境變數：{', '.join(missing)}（請參考 .env.example）")
    return token, endpoint, model


def _system_prompt() -> Message:
    now = datetime.now()
    tool_names = "\n".join(f"- {tool.function.name}" for tool in tool_list)
    return Message(
        role="system",
        content=f"""你是 Discord 上的個人排程助理，負責幫使用者記錄行程、規劃時間，也能推薦晚餐。
現在時間：{now.strftime('%Y-%m-%d %H:%M')}（{_WEEKDAYS[now.weekday()]}）。

可用的工具：
{tool_names}

規則：
1. 與行程、任務、排程相關的要求，一律先透過工具讀寫資料庫，不要憑空捏造行程內容。
2. 使用者要排彈性任務時，若未提供「預計需要的總時數」或「預計完成日期」，請先向使用者詢問，不要自行假設。
3. 「明天」「這週五」等相對日期，請以上述現在時間為基準換算成實際日期。
4. 規劃完成後務必呼叫 save_llm_plan 儲存，且每次傳入完整排程。
5. 清空資料前必須確認使用者明確表示要清空。
6. 最終回應請使用繁體中文，簡潔清楚，且必須在 1900 個字元以內。""",
    )


async def _chat(client: AsyncClient, model: str, messages: list[Message]) -> ChatResponse:
    return await client.chat(model=model, messages=messages, tools=tool_list, think=True)


def _run_tool(name: str, arguments: dict) -> str:
    """執行工具；任何錯誤都以字串回傳給 LLM，讓它有機會修正參數重試。"""
    func = func_map.get(name)
    if func is None:
        return f"Unknown tool: {name}"
    try:
        return str(func(**arguments))
    except Exception as e:  # noqa: BLE001 - 工具錯誤要回饋給模型而不是讓 bot 掛掉
        log.warning("Tool %s failed: %s: %s", name, type(e).__name__, e)
        return f"Tool error ({type(e).__name__}): {e}"


def clear_history(channel_id: int) -> None:
    _histories.pop(channel_id, None)


async def ask_agent(channel_id: int, content: str) -> str:
    """把使用者訊息送給 LLM，處理 tool calls，回傳最終文字回覆。

    對話歷史依 ``channel_id`` 分開保存。若 LLM API 呼叫失敗會直接拋出例外，
    由呼叫端決定如何回覆使用者；失敗的那則使用者訊息不會留在歷史中。
    """
    token, endpoint, model = _settings()
    client = AsyncClient(host=endpoint, headers={"Authorization": f"Bearer {token}"})

    history = _histories.setdefault(channel_id, [])
    history.append(Message(role="user", content=content))
    messages = [_system_prompt(), *history]

    try:
        log.info("[%s] Waiting for LLM response...", channel_id)
        response = await _chat(client, model, messages)

        for _ in range(MAX_TOOL_ROUNDS):
            if not response.message.tool_calls:
                break
            messages.append(response.message)
            for call in response.message.tool_calls:
                log.info("[%s] Tool call: %s(%s)", channel_id, call.function.name, call.function.arguments)
                result = _run_tool(call.function.name, call.function.arguments)
                messages.append(Message(role="tool", tool_name=call.function.name, content=result))
            response = await _chat(client, model, messages)
    except Exception:
        history.pop()
        raise

    reply = response.message.content or ""
    history.append(Message(role="assistant", content=reply))
    del history[:-MAX_HISTORY]
    return reply
