import asyncio
import logging
import sys
from os import getenv
from aiogram import F
import requests
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, Message, InlineQuery, InlineQueryResultPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder
from uuid import uuid4
from functions.bot import send_message_to_admins
from aiogram.types import FSInputFile
from chaturbate import ChaturbateAccountHandler

from chaturbate_poller.config_manager import ConfigManager
from functions.db import create_database_and_table, add_user, get_users, get_users_amount
from functions.rate import get_bank_rate, calculate_rates, get_rate_for_amount, get_tokens_rate_text, get_rates_text


# Configurations
config_manager = ConfigManager()
TOKEN = getenv("BOT_TOKEN")
CONTACT_TG_USERNAME = getenv("CONTACT_TG_USERNAME")
REVIEWS_LINK = getenv("REVIEWS_LINK")
IMAGE_LINK = getenv("IMAGE_LINK")
ADMINS = getenv("ADMINS", "").split(',')

DB_NAME = getenv("DB_NAME")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

account2_proxies = {
    "http://": "http://A0fmwzSxRVr4HuT:uoLH28xd0SgXxVF@66.128.194.31:43316",
    "https://": "https://A0fmwzSxRVr4HuT:uoLH28xd0SgXxVF@66.128.194.31:43316",
}

CB_USERNAME_1 = getenv("CB_USERNAME_1")
CB_EVENTS_TOKEN_1 = getenv("CB_EVENTS_TOKEN_1")
CB_STATS_TOKEN_1 = getenv("CB_STATS_TOKEN_1")

CB_USERNAME_2 = getenv("CB_USERNAME_2")
CB_EVENTS_TOKEN_2 = getenv("CB_EVENTS_TOKEN_2")
CB_STATS_TOKEN_2 = getenv("CB_STATS_TOKEN_2")

account1 = ChaturbateAccountHandler(CB_USERNAME_1, CB_EVENTS_TOKEN_1, CB_STATS_TOKEN_1, bot)
account2 = ChaturbateAccountHandler(CB_USERNAME_2, CB_EVENTS_TOKEN_2, CB_STATS_TOKEN_2, bot, proxies=account2_proxies)

accounts = [
    account1,
    account2
]

keyboard = InlineKeyboardBuilder().add(
    InlineKeyboardButton(text="⭐ ОТЗЫВЫ", url=f"{REVIEWS_LINK}")
).row(
    InlineKeyboardButton(text="🔥 Совершить обмен", url=f"https://t.me/{CONTACT_TG_USERNAME}")
)


@dp.message(CommandStart())
async def handle_start_command(message: Message) -> None:
    nickname = message.from_user.username
    await add_user(DB_NAME, ADMINS, bot, message.from_user.id, message.from_user.full_name, nickname)
    await message.answer(f"Привет, <b>{message.from_user.full_name}</b>!\nОтправь мне сумму токенов или просто напиши <code>КУРС</code> :з")


@dp.message()
async def handle_message(message: Message) -> None:
    nickname = message.from_user.username
    await add_user(DB_NAME, ADMINS, bot, message.from_user.id, message.from_user.full_name, nickname)

    if not message.text:
        return await message.answer("<b>Пожалуйста, отправьте количество токенов или команду <code>КУРС</code>.</b>")

    if message.text.lower() == "курс":
        await send_message_to_admins(bot, f"🔔 <b>Пользователь {'@' + message.from_user.username if message.from_user.username else message.from_user.first_name} запросил курс!</b>")
        text = get_rates_text()
        await message.answer_photo(IMAGE_LINK, caption=text, reply_markup=keyboard.as_markup())
        return
    elif message.text == "!дамп":
        if str(message.from_user.id) in ADMINS:
            db_file = FSInputFile('database.db')

            for admin in ADMINS:
                try:
                    await bot.send_document(admin, db_file, caption=f"<code>Дамп базы данных запрошенный админом</code><b> {message.from_user.full_name}</b>")
                except:
                    pass
            return
    elif message.text == "!юзеры":
        if str(message.from_user.id) in ADMINS:
            user_list = get_users(DB_NAME)
            users_count = get_users_amount(DB_NAME)
            return await message.answer(f"<b>Количество юзеров:</b> {users_count}\n\n{user_list}", disable_web_page_preview=True)
    elif message.text == "!баланс":
        if str(message.from_user.id) in ADMINS:
            text = "<b>💰 Балансы аккаунтов:</b>\n\n"
            for account in accounts:
                balance = await account.fetch_token_balance()
                text += f"<b>{account.username}</b> - <code>{balance}</code>\n"
            
            return await message.answer(text, disable_web_page_preview=True)

    try:
        tokens = int(message.text.strip())
        text = get_tokens_rate_text(tokens)
        await message.answer_photo(IMAGE_LINK, caption=text, reply_markup=keyboard.as_markup())
    except ValueError:
        await message.answer("<b>Сумма токенов должна быть числом!</b>")


@dp.inline_query(F.query)
async def inline_query_handler(inline_query: InlineQuery):
    query = inline_query.query.strip()

    if query.isdigit():
        tokens = int(query)
        text = get_tokens_rate_text(tokens)
    else:
        text = get_rates_text()

    results = [
        InlineQueryResultPhoto(
            id=str(uuid4()),
            photo_url='https://i.ibb.co/NyWfPg3/2024-10-06-21-49-32.png',
            thumbnail_url='https://i.ibb.co/NyWfPg3/2024-10-06-21-49-32.png',
            caption=text,
            parse_mode="HTML",
            type="photo",
            photo_width=1860,
            photo_height=1868,
        )
    ]

    await bot.answer_inline_query(inline_query.id, results, cache_time=0)


async def bot_poller() -> None:
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(
        bot_poller(),
        account1.cb_poller(),
        account2.cb_poller(),
    )


if __name__ == "__main__":
    create_database_and_table(DB_NAME)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
