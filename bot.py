"""Discord 介面層：接收 @mention 的訊息，處理快速指令，其餘交給 LLM agent。"""

import logging
import re
from os import getenv
from typing import Awaitable, Callable

from discord import Bot, Intents, Message

from agent import ask_agent, clear_history

log = logging.getLogger(__name__)

DISCORD_MESSAGE_LIMIT = 2000
THINKING_TEXT = "🤔 正在思考中，請稍候…"
ERROR_TEXT = "⚠️ 處理時發生錯誤，請稍後再試。"
EMPTY_REPLY_TEXT = "（模型沒有回傳任何內容，請換個方式描述再試一次）"

HELP_TEXT = """📋 **我可以幫你做這些事**（請 @我 後輸入）
• 記錄行程／任務：「下週三 14:00-16:00 有計算理論期末考」「幫我排 3 小時讀微算機，週五前完成」
• 規劃時間：「幫我把這些任務排進這週」
• 查詢行程：「看看我的行程」「列出讀書相關的行程」
• 修改項目：「把慢跑改成 45 分鐘」
• 清空資料：「清空所有行程」
• 晚餐推薦：「今天想吃清爽一點的，預算 150」

⚡ **快速指令**：`help`／`幫助`、`ping`／`狀態`、`reset`／`清除對話`"""

_MENTION_PATTERN = re.compile(r"<@!?\d+>")

intents = Intents.default()
intents.message_content = True
bot = Bot(intents=intents)


async def _help(message: Message) -> None:
    await message.reply(HELP_TEXT)


async def _ping(message: Message) -> None:
    await message.reply(
        f"線上｜延遲 {bot.latency * 1000:.0f} ms｜模型：{getenv('OLLAMA_MODEL', '未設定')}"
    )


async def _reset(message: Message) -> None:
    clear_history(message.channel.id)
    await message.reply("🧹 已清除此頻道的對話記憶（資料庫中的行程不受影響）。")


# 完全比對（不分大小寫）去掉 @mention 之後的文字
QUICK_COMMANDS: dict[tuple[str, ...], Callable[[Message], Awaitable[None]]] = {
    ("help", "幫助", "功能"): _help,
    ("ping", "狀態"): _ping,
    ("reset", "清除對話"): _reset,
}


def _strip_mentions(content: str) -> str:
    return _MENTION_PATTERN.sub("", content).strip()


def _find_quick_command(text: str) -> Callable[[Message], Awaitable[None]] | None:
    lowered = text.lower()
    for keywords, handler in QUICK_COMMANDS.items():
        if lowered in keywords:
            return handler
    return None


def _split_message(text: str) -> list[str]:
    """把超過 Discord 上限的文字切成多段。"""
    return [text[i:i + DISCORD_MESSAGE_LIMIT] for i in range(0, len(text), DISCORD_MESSAGE_LIMIT)]


@bot.event
async def on_ready():
    log.info("Logged in as %s", bot.user)


@bot.event
async def on_message(message: Message):
    if message.author.bot or not bot.user.mentioned_in(message):
        return

    text = _strip_mentions(message.content)
    if not text:
        await _help(message)
        return

    quick_command = _find_quick_command(text)
    if quick_command is not None:
        await quick_command(message)
        return

    reply_message = await message.reply(THINKING_TEXT)
    try:
        response = await ask_agent(message.channel.id, text)
    except Exception:  # noqa: BLE001 - 任何錯誤都要讓使用者看到，而不是讓「思考中」卡住
        log.exception("ask_agent failed")
        await reply_message.edit(ERROR_TEXT)
        return

    log.info("Response: %s", response)
    chunks = _split_message(response) or [EMPTY_REPLY_TEXT]
    await reply_message.edit(chunks[0])
    for chunk in chunks[1:]:
        await message.channel.send(chunk)


def start_bot() -> None:
    token = getenv("TOKEN")
    if not token:
        raise RuntimeError("缺少環境變數 TOKEN（Discord bot token），請參考 .env.example")
    bot.run(token)
