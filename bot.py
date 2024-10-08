import asyncio
import logging
import sys
import xml.etree.ElementTree as ET
from os import getenv
import sqlite3
import re

import requests
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from chaturbate_poller.chaturbate_client import ChaturbateClient
from aiogram.types import InputFile
from aiogram.types import FSInputFile
from chaturbate_poller.config_manager import ConfigManager
from constants import CBR_URL

config_manager = ConfigManager()

admin_str = getenv("ADMINS")
TOKEN = getenv("BOT_TOKEN")
CB_USERNAME = config_manager.get("CB_USERNAME", getenv("CB_USERNAME"))
CB_EVENTS_TOKEN = config_manager.get("CB_TOKEN", getenv("CB_EVENTS_TOKEN"))
CB_STATS_TOKEN = getenv("CB_STATS_TOKEN")
CONTACT_TG_USERNAME = getenv("CONTACT_TG_USERNAME")
REVIEWS_LINK = getenv("REVIEWS_LINK")
IMAGE_LINK = getenv("IMAGE_LINK")
ADMINS = admin_str.split(',')
DB_NAME = getenv("DB_NAME")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def create_database_and_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            user_name TEXT NOT NULL,
            nickname TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            tokens INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()


async def add_user(user_id, user_name, nickname):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    
    if result is None:
        cursor.execute('INSERT INTO users (user_id, user_name, nickname) VALUES (?, ?, ?)', (user_id, user_name, nickname))
        for admin in ADMINS:
            await bot.send_message(admin, f"<code>{user_name} был скрышен в базу данных!</code>")
    else:
        print(f"User with ID {user_id} already exists.")

    conn.commit()
    conn.close()


def add_transaction(tokens):
    print("Вход")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO "transactions" (tokens) VALUES (?)', (tokens,))


    conn.commit()
    conn.close()


def get_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, user_name, nickname FROM users")
    users = cursor.fetchall()

    text = '<b>Список пользователей:</b>\n\n'

    i = 1
    for user in users:
        user_id, user_name, nickname = user
        if nickname is not None:
            text += f"{i}. <a href='https://t.me/{nickname}'>{user_name}</a>\n"
        else:
            text += f"{i}. <a href='tg://user?id={user_id}'>{user_name}</a> - ID: <code>{user_id}</code>\n"
        i += 1

    conn.close()
    return text

def get_users_amount():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()

    conn.close()

    return count

def get_transactions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), SUM(tokens) FROM transactions")
    count, total_sum = cursor.fetchone()

    conn.close()

    return count, total_sum


def get_balance():
    try:
        response = requests.get(f"https://chaturbate.com/statsapi/?username={CB_USERNAME}&token={CB_STATS_TOKEN}")
        if response.status_code != 200:
            return None
        
        if 'token_balance' not in response.json():
            return None
        
        return response.json()['token_balance']
    except:
        return None


def get_rate():
    try:
        response = requests.get(CBR_URL)
        if response.status_code != 200:
            return 0
        
        root = ET.fromstring(response.content)

        valute = root.find(".//Valute[@ID='R01235']")

        if valute is not None:
            value = valute.find('Value').text
            return float(value.replace(',', '.'))
        else:
            return 0

    except Exception as e:
        print(e)
        return 0


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    nickname = None
    if message.from_user.username:
        nickname = message.from_user.username
    await add_user(message.from_user.id, message.from_user.full_name, nickname)
    await message.answer(f"Привет, <b>{message.from_user.full_name}</b>!\nОтправь мне сумму токенов или просто напиши <code>КУРС</code> :з")


@dp.message()
async def message_handler(message: Message) -> None:
    rate = get_rate()

    rate_25 = round((rate * 0.92), 2)
    rate_50 = round((rate * 0.93), 2)
    rate_100 = round((rate * 0.945), 2)
    rate_250 = round((rate * 0.96), 2)
    rate_500 = round((rate * 0.97), 2)

    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="🔥 Совершить обмен!", url=f"https://t.me/{CONTACT_TG_USERNAME}"))

    nickname = None
    if message.from_user.username:
        nickname = message.from_user.username
    await add_user(message.from_user.id, message.from_user.full_name, nickname)
    if not message.text:
        return await message.answer("<b>Пожалуйста, отправьте количество токенов которые Вы хотите обменять, либо отправьте <code>КУРС</code>!</b>")
    
    if message.text.lower() == "курс":
        text = f"<b>Минимальная сумма обмена - 25$</b> <i>500 токенов</i>\n\n<b>Курс за $1:</b>\n<i>от $25 - {rate_25} руб.\nот $50 - {rate_50} руб.\nот $100 - {rate_100}\nот 250 - {rate_250} руб.\nот 500 - {rate_500} руб</i>\n\nЧтобы узнать точную сумму, которую Вы получите нужно просто отправить количество токенов  чат"
        for admin in ADMINS:
            try:
                if message.from_user.username:
                    await bot.send_message(admin, f"<a href='https://t.me/{message.from_user.username}'>ЮЗЕР {message.from_user.full_name}</a> запросил курс")
                elif message.from_user.id:
                    await bot.send_message(admin, f"<a href='tg://user?id={message.from_user.id}'>ЮЗЕР {message.from_user.full_name}</a> запросил курс")
                else:
                    await bot.send_message(admin, f"ЮЗЕР запросил курс")
            except:
                pass
        return await message.answer_photo(IMAGE_LINK, caption=text, reply_markup=keyboard.as_markup())

    if message.text == "!дамп":
        if str(message.from_user.id) in ADMINS:
            db_file = FSInputFile('database.db')

            for admin in ADMINS:
                await bot.send_document(admin, db_file, caption=f"<code>Дамп базы данных запрошенный админом</code><b> {message.from_user.full_name}</b>")
            return
        
    if message.text == "!юзеры":
        if str(message.from_user.id) in ADMINS:
            user_list = get_users()
            return await message.answer(user_list, disable_web_page_preview=True)
        
    if message.text == "!транзакции":
        if str(message.from_user.id) in ADMINS:
            count, total = get_transactions()
            return await message.answer(f"<b>Количество транзакций:</b> <code>{count}</code>\n<b>Токенов обменяли: </b><code>{total}</code>")

    if message.text == "!стата":
        if str(message.from_user.id) in ADMINS:
            users_count = get_users_amount()
            count, total = get_transactions()
            return await message.answer(f"<b>Количество пользователей:</b> <code>{users_count[0]}</code>\n\n<b>Количество транзакций:</b> <code>{count}</code>\n<b>Токенов обменяли: </b><code>{total}</code>")


    if message.text.startswith("!транзакция"):
        if str(message.from_user.id) in ADMINS:
            tokens = ''.join(re.findall(r'\d+', message.text))
            add_transaction(int(tokens))
            for admin in ADMINS:
                await bot.send_message(admin, f"<code>Транзакция на {tokens} была внесена в базу админом</code><b> {message.from_user.full_name}</b>")
            return

    try:
        tokens = int(message.text.strip())
    except:
        return await message.answer("<b>Сумма токенов должна быть числом!</b>")

    dollars = tokens * 0.05

    if rate <= 0:
        return await message.answer("<b>😲 Не удалось получить курс :(</b>", parse_mode="HTML")
    
    if dollars < 25:
        return await message.answer("<b>😔 Минимальная сумма к обмену - 500 токенов</b>", parse_mode="HTML")
    
    if dollars >= 25 and dollars < 50:
        rate = rate_25

    if dollars >= 50 and dollars < 100:
        rate = rate_50

    if dollars >= 100 and dollars < 250:
        rate = rate_100

    if dollars >= 250 and dollars < 500:
        rate = rate_250

    if dollars >= 500:
        rate = rate_500

    for admin in ADMINS:
        try:
            if message.from_user.username:
                await bot.send_message(admin, f"<a href='https://t.me/{message.from_user.username}'>ЮЗЕР {message.from_user.full_name}</a> запросил курс для <code>{tokens}</code> тк\nЕму предложено <code>{round((dollars * rate), 2)} руб.</code>")
            elif message.from_user.id:
                await bot.send_message(admin, f"<a href='tg://user?id={message.from_user.id}'>ЮЗЕР {message.from_user.full_name}</a> запросил курс для <code>{tokens}</code> тк\nЕму предложено <code>{round((dollars * rate), 2)} руб.</code>")
            else:
                await bot.send_message(admin, f"ЮЗЕР запросил курс для <code>{tokens}</code> тк\nЕму предложено <code>{round((dollars * rate), 2)} руб.</code>")
        except:
            pass

    text = f"<b>💱 Ваш курс:</b> {rate} руб. / доллар\n<b>💳 Вы получите:</b> {round((rate * dollars), 2)} руб.\n<b>\n<a href='{REVIEWS_LINK}'>⭐ ОТЗЫВЫ</a>\n<a href='t.me/{CONTACT_TG_USERNAME}'>💬 СОВЕРШИТЬ ОБМЕН</a></b>"
    await message.answer_photo(IMAGE_LINK, caption=text, reply_markup=keyboard.as_markup())


async def bot_poller() -> None:
    await dp.start_polling(bot)


async def chaturbate_poller():
    async with ChaturbateClient(CB_USERNAME, CB_EVENTS_TOKEN) as client:
        url = None

        while True:
            response = await client.fetch_events(url)

            for event in response.events:
                if event.method == "tip":
                    balance = get_balance()

                    tip = event.object.tip
                    user = event.object.user

                    add_transaction(int(tip.tokens))

                    text = f"<b>💸 <a href='https://chaturbate.com/{user.username}'>{user.username}</a> отправил {tip.tokens} тк. 💸</b>"
                    if balance is not None:
                        text += f'\n\n<b><i>Баланс аккаунта: {balance}</i></b>'

                    for admin in ADMINS:
                        await bot.send_message(admin, text, disable_web_page_preview=True)

            url = str(response.next_url)

async def main():
    await asyncio.gather(bot_poller(), chaturbate_poller())


if __name__ == "__main__":
    create_database_and_table()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
