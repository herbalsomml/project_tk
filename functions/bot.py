async def send_message_to_admins(bot, message, ADMINS):
    for admin in ADMINS:
        try:
            await bot.send_message(admin, message, disable_web_page_preview=True)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")