import datetime
import logging
import os
import sqlite3

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

import parser


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


# Состояние смены типа недели (по умолчанию числитель)
week_type = "Числитель"

back_key = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="change_week_type")]])


# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Определяем, используем ли мы токен для тестирования (debug)
debug = 1  # Установите на 0, если вы хотите использовать основной токен

# Определяем имя файла с токеном в зависимости от переменной debug
token_filename = 'test_token.txt' if debug else 'main_token.txt'

# Проверяем, существует ли файл с токеном
if not os.path.isfile(token_filename):
    raise FileNotFoundError(f"Файл {token_filename} не найден.")

# Читаем токен из файла
with open(token_filename, 'r') as file:
    TOKEN = file.read().strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with multiple inline buttons attached."""
    await update.message.reply_text("Выберите опцию:", reply_markup=get_menu_keyboard())


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    global week_type  # Делаем week_type глобальной переменной

    query = update.callback_query
    await query.answer()

    if query.data == "change_week_type":
        # Меняем тип недели при каждом нажатии
        week_type = "Числитель" if week_type == "Знаменатель" else "Знаменатель"
        # Изменяем текст кнопки
        try:
            await query.edit_message_reply_markup(reply_markup=get_menu_keyboard())
        except Exception as e:
            print(e)
    elif query.data == "set_cur_week_type":
        new_week_type = parser.get_week_type(switch=False)
        if week_type != new_week_type:
            week_type = new_week_type
            await query.edit_message_reply_markup(get_menu_keyboard())
    elif query.data == "settings":
        await query.edit_message_text(text="Введите название группы:", reply_markup=back_key)
    elif query.data.isnumeric():
        user_id = query.from_user.id
        bd_group = get_user_data(user_id)
        mes = parser.main(group_name=bd_group, day=int(query.data), week_type=week_type)
        await query.edit_message_text(mes, reply_markup=back_key)
    else:
        today_wd = datetime.datetime.now().weekday()
        if query.data == "ПЗВЧР":
            shift_day = today_wd - 2
            if today_wd == 0 or today_wd == 1:
                sw = True
            else:
                sw = False

        elif query.data == "Вчера":
            shift_day = today_wd - 1
            if today_wd == 0:
                sw = True
            else:
                sw = False

        elif query.data == "Завтра":
            shift_day = today_wd + 1
            if today_wd == 6:
                sw = True
            else:
                sw = False

        elif query.data == "ПЗВТР":
            shift_day = today_wd + 2
            if today_wd == 5 or today_wd == 6:
                sw = True
            else:
                sw = False
        else:
            shift_day = today_wd
            sw = False

        if shift_day == 6:
            mes = "По воскресеньям не учимся"
        else:
            # При необходимости, получите информацию о пользователе из базы данных
            user_id = query.from_user.id
            group = get_user_data(user_id)

            if group is not None:
                mes = parser.main(group_name=group, day=shift_day, switch_wt=sw)
            else:
                mes = "Сначала задайте название группы"
        try:
            await query.edit_message_text(mes, reply_markup=back_key)
        except Exception as e:
            print(e)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group_msg = update.message.text

    answ = parser.main(group_name=group_msg)
    if answ == -1:
        mes = "Не удалось проверить группу, попробуйте позже"
    elif answ == 0:
        mes = "Не удалось найти группу " + group_msg
    else:
        user_id = update.message.from_user.id
        group = update.message.text
        add_user_data(user_id, group)
        mes = "Группа успешно сохранена: " + group
    await update.message.reply_text(text=mes, reply_markup=back_key)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("""Используйте /start для начала работы с ботом.""")


def main() -> None:
    # Перед использованием базы данных, убедитесь, что таблица создана
    create_user_table()

    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def get_menu_keyboard():
    global week_type

    menu_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ПЗВЧР", callback_data="ПЗВЧР"),
            InlineKeyboardButton("Вчера", callback_data="Вчера"),
            InlineKeyboardButton("Сегодня", callback_data="Сегодня"),
            InlineKeyboardButton("Завтра", callback_data="Завтра"),
            InlineKeyboardButton("ПЗВТР", callback_data="ПЗВТР"),
        ],
        [
            InlineKeyboardButton("ПН", callback_data=0),
            InlineKeyboardButton("ВТ", callback_data=1),
            InlineKeyboardButton("СР", callback_data=2),
            InlineKeyboardButton("ЧТ", callback_data=3),
            InlineKeyboardButton("ПТ", callback_data=4),
            InlineKeyboardButton("СБ", callback_data=5),
        ],
        [
            InlineKeyboardButton(f"Текущий тип недели",
                                 callback_data="set_cur_week_type"),
            InlineKeyboardButton(f"{week_type}",
                                 callback_data="change_week_type"),
        ],
        [InlineKeyboardButton("Настройка группы", callback_data="settings"), ],
    ])
    return menu_keyboard


if __name__ == "__main__":
    main()
