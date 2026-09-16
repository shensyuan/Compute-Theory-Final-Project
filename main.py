import logging

from dotenv import load_dotenv

# 必須在匯入 bot / agent 之前載入 .env，否則環境變數尚未就緒
load_dotenv()

from bot import start_bot  # noqa: E402
from agent.tools import tool_list  # noqa: E402


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger(__name__).info(
        "Registered tools: %s", ", ".join(tool.function.name for tool in tool_list)
    )
    start_bot()


if __name__ == "__main__":
    main()
