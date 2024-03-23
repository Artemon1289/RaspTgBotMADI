import sqlite3


# Функция для создания таблицы пользователей в базе данных SQLite
def create_user_table():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users
                      (user_id INTEGER PRIMARY KEY, group_name TEXT)''')
    conn.commit()
    conn.close()


# Функция для добавления информации о пользователе в базу данных SQLite
def add_user_data(user_id, group_name):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()

    # Проверяем, есть ли пользователь уже в базе данных
    cursor.execute("SELECT COUNT(*) FROM users WHERE user_id=?", (user_id,))
    count = cursor.fetchone()[0]

    if count > 0:
        # Если пользователь уже есть в базе данных, обновляем его группу
        cursor.execute("UPDATE users SET group_name=? WHERE user_id=?", (group_name, user_id))
    else:
        # Если пользователь отсутствует в базе данных, добавляем его
        cursor.execute("INSERT INTO users (user_id, group_name) VALUES (?, ?)", (user_id, group_name))

    conn.commit()
    conn.close()


# Функция для получения информации о пользователе из базы данных SQLite
def get_user_data(user_id):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        return None
