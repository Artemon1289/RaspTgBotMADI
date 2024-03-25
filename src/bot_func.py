import datetime

import parser
import database

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

week_type = "Числитель"
back_key = InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data="change_week_type")]])


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
        day_info = parser.get_weekday(int(query.data))
        user_id = query.from_user.id
        group = database.get_user_data(user_id)
        mes = parser.main(group_name=group, day=int(query.data), week_type=week_type)
        await query.edit_message_text(mes, reply_markup=back_key)
        await log(id=user_id, group=group, function=day_info)

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
            user_id = query.from_user.id
            group = database.get_user_data(user_id)

            if group is not None:
                mes = parser.main(group_name=group, day=shift_day, switch_wt=sw)
                await log(user_id, group, query.data)
            else:
                mes = "Сначала задайте название группы"
        try:
            await query.edit_message_text(mes, reply_markup=back_key)
        except Exception as e:
            print(e)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    group_msg = update.message.text

    answer = parser.main(group_name=group_msg)
    if answer == -1:
        mes = "Не удалось проверить группу, попробуйте позже"
    elif answer == 0:
        mes = "Не удалось найти группу " + group_msg
    else:
        user_id = update.message.from_user.id
        group = update.message.text
        database.add_user_data(user_id, group)
        mes = "Группа успешно сохранена: " + group
    await update.message.reply_text(text=mes, reply_markup=back_key)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    await update.message.reply_text("""Используйте /start для начала работы с ботом.""")


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


async def log(id, group, function):
    with open('groups_log.txt', 'a') as f:
        f.write(f'{id} - {group} - {function} - {datetime.datetime.now()}\n')
