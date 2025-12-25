from dotenv import load_dotenv

from bot import start_bot

if __name__ == "__main__":
    load_dotenv()
    from agent.tools import tool_list
    print(tool_list)
    
    start_bot()

    # from agent.agent import test
    # from asyncio import run
    # async def main():
    #     await test()
    # run(test())
