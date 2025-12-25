from ollama import AsyncClient, ChatResponse, Message

from os import getenv

from .tools import tool_list, func_map

messages = [
    Message(role="system", content="""
            你的最終回應必須要在 2000 個字元以內。
            如果使用者的要求與任務排程相關，請使用 Scheduler 開頭的 tools
            如果使用者未提及**預計需要的總時數**或**預計完成日期**，請使用告訴使用者提供以上資訊
            """)
]

OLLAMA_API_TOKEN = getenv("OLLAMA_TOKEN")
OLLAMA_API_ENDPOINT = getenv("OLLAMA_API_ENDPOINT")
OLLAMA_MODEL = getenv("OLLAMA_MODEL", "")

if OLLAMA_API_TOKEN is None:
    raise RuntimeError("Ollama API token not found.")

if OLLAMA_API_ENDPOINT is None:
    raise RuntimeError("Ollama API endpoint not found.")


async def test(context: str) -> str:
    client = AsyncClient(
        host=OLLAMA_API_ENDPOINT,
        headers={
            "Authorization": f"Bearer {OLLAMA_API_TOKEN}"
        }
    )

    messages.append(Message(role="user", content=context))

    print("Waiting for LLM response...")

    response: ChatResponse = await client.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        tools=tool_list,
        think=True
    )
    messages.append(response.message)

    if response.message.tool_calls:
        for call in response.message.tool_calls:
            print(f"Call: {call.function.name}")
            target_func = func_map.get(call.function.name)

            if target_func:
                result = target_func(**call.function.arguments)
            else:
                result = "Unknown tool"

            messages.append(Message(
                role="tool",
                tool_name=call.function.name,
                content=str(result)
            ))

        response = await client.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=tool_list
        )
        print("Function called.")

    return response.message.content or ""
