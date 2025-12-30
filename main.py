from dotenv import load_dotenv

from bot import start_bot

if __name__ == "__main__":
    load_dotenv()
    from agent.tools import tool_list
    print(tool_list)
    
    start_bot()
