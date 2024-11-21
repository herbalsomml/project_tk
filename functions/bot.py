import asyncio
from os import getenv


ADMINS = getenv("ADMINS", "").split(',')


async def send_message_to_admins(bot, message):
    for admin in ADMINS:
        try:
            await bot.send_message(admin, message, disable_web_page_preview=True)
        except Exception as e:
            pass