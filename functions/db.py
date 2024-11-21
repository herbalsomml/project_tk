import sqlite3
from functions.bot import send_message_to_admins


def execute_query(db_name, query, params=(), fetch_one=False, fetch_all=False):
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        conn.commit()


def create_database_and_table(db_name):
    queries = [
        '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            user_name TEXT NOT NULL,
            nickname TEXT
        )
        '''
    ]
    for query in queries:
        execute_query(db_name, query)


async def add_user(db_name, admins, bot, user_id, user_name, nickname):
    user_exists_query = 'SELECT 1 FROM users WHERE user_id = ?'
    add_user_query = 'INSERT INTO users (user_id, user_name, nickname) VALUES (?, ?, ?)'

    if not execute_query(db_name, user_exists_query, (user_id,), fetch_one=True):
        execute_query(db_name, add_user_query, (user_id, user_name, nickname))
        await send_message_to_admins(bot, f"<code>{user_name} был добавлен в базу данных!</code>")
    else:
        pass



def get_users(db_name):
    get_users_query = "SELECT user_id, user_name, nickname FROM users"
    users = execute_query(db_name, get_users_query, fetch_all=True)

    text = '<b>Список пользователей:</b>\n'
    for i, (user_id, user_name, nickname) in enumerate(users, start=1):
        if nickname:
            text += f"{i}. <a href='https://t.me/{nickname}'>{user_name}</a>\n"
        else:
            text += f"{i}. <a href='tg://user?id={user_id}'>{user_name}</a> - ID: <code>{user_id}</code>\n"

    return text


def get_users_amount(db_name):
    get_count_query = "SELECT COUNT(*) FROM users"
    count = execute_query(db_name, get_count_query, fetch_one=True)
    return count[0] if count else 0

