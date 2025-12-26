from discord import Bot, Message, Intents

from os import getenv

from agent import test

SPECIAL_USER_ID = 302774180611358720

intents = Intents.default()
intents.message_content = True
bot = Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} !")


@bot.event
async def on_message(message: Message):
    if not bot.user.mentioned_in(message):
        return
    
    if "起床" in message.content:
        await message.reply("重睡")
    elif "你超電" in message.content:
        await message.reply("你比較電")
    elif "你好怪" in message.content:
        await message.reply("你才怪")
    elif "吃啥" in message.content:
        await message.reply("不知道")
    elif "微算機" in message.content:
        await message.reply("你要去讀規格書阿")
    else:
        reply_message = await message.reply(f"{bot.user.display_name} is thinking...")

        response_message = await test(message.content)
        print(f"Response: {response_message}")
        if response_message and len(response_message) < 2000:
            await reply_message.edit(response_message)

    if message.author.id == SPECIAL_USER_ID:
        await message.reply("但你幹嘛跟自己講話啊 你好怪喔")
def start_bot():
    bot.run(getenv("TOKEN"))
