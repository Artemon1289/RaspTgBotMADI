import ast
import json
from datetime import datetime, timedelta

import bs4
import requests

WEEK_URL = "https://raspisanie.madi.ru/tplan/calendar.php"
# get запрос, для получения списка групп
GROUPS_URL = "https://raspisanie.madi.ru/tplan/tasks/task3,7_fastview.php"
# post запрос, для получения списка расписания
TABLE_URL = "https://raspisanie.madi.ru/tplan/tasks/tableFiller.php"

table = {}


def get_groups_dict():
    groups_site = requests.get(GROUPS_URL)

    groups_soup = bs4.BeautifulSoup(groups_site.text, "html.parser")
    if groups_soup.text == "":
        return -1

    groups_soup = groups_soup.find("ul").find_all("li")
    groups_dict = clean_groups(groups_soup)
    groups_dict = json.loads(groups_dict.lower())
    groups_dict = {v: k for k, v in groups_dict.items()}
    return groups_dict
    pass


def clean_groups(groups_str):
    groups_str = str(groups_str)
    groups_str = groups_str.replace(',', ',\n')
    groups_str = groups_str.replace('<li value=', '')
    groups_str = groups_str.replace('</li>', '"')
    groups_str = groups_str.replace('">', '": "')
    groups_str = groups_str.replace('[', '{')
    groups_str = groups_str.replace(']', '}')
    groups_str = groups_str.replace('   ', '')
    groups_str = groups_str.replace('  ', '')
    groups_str = groups_str.replace(' ', '')
    return groups_str


def get_group_id(group_name, dictionary):
    group_id = (dictionary.get(str(group_name)))
    if group_id is None:
        return -1
    else:
        return group_id
    pass


def get_rasp(group_id):
    # добавляем id группы в запрос
    cur_data = "{'tab': '7', 'gp_id': '" + str(group_id) + "'}"

    # Записываем ответ на наш запрос
    request = requests.post(TABLE_URL, data=ast.literal_eval(cur_data))

    # Находим фрагмент с расписанием
    table_soup = bs4.BeautifulSoup(request.text, "html.parser").select_one(
        ".timetable")

    # table_soup = table_soup.find_all("td", {"colspan": True})
    # print(table_soup)
    return table_soup.text
    pass


def get_week_type():
    req = requests.get(WEEK_URL)
    if "\\u0447" in req.text:
        return "Числитель"
    if "\\u0437" in req.text:
        return "Знаменатель"
    else:
        return "ЧЗХ"
    pass


def get_week_day_str(week_day):
    if week_day == 0:
        return "Понедельник"
    elif week_day == 1:
        return "Вторник"
    elif week_day == 2:
        return "Среда"
    elif week_day == 3:
        return "Четверг"
    elif week_day == 4:
        return "Пятница"
    elif week_day == 5:
        return "Суббота"
    else:
        return "Полнодневные занятия"


def get_rasp_from_text(text, week_day):
    cur_week_day_str = get_week_day_str(week_day)
    next_week_day_str = get_week_day_str(week_day + 1)

    lines = []
    cur_day_found = False

    for line in text.split("\n"):
        if cur_week_day_str in line:
            cur_day_found = True

        if next_week_day_str in line or "Полнодневные занятия" in line:
            return lines

        if cur_day_found:
            lines.append(line)


def get_cur_week_strings(lines, week_type):
    result = []
    for line in lines:
        if week_type in line or "Еженедельно" in line:
            result.append(line)
    return result


def main(group_name="1мбд", week_day=0, shift=None):

    if shift is not None:
        # Получение нужной даты
        week_day = (datetime.now().date() + timedelta(days=shift)).weekday()

    # создаём словарь групп
    groups_dict = get_groups_dict()
    if groups_dict == -1:
        return "Не удалось получить список групп"

    # Берём id группы по названию группы из словаря групп
    group_id = get_group_id(group_name, groups_dict)
    if group_id == -1:
        return "Такой группы нет"

    # Запрашиваем расписание по id группы
    table_rasp = get_rasp(group_id)

    # Проверяем нашли ли мы расписание на сайте
    if table_rasp is None:
        message = """Не удалось получить расписание с сайта.\nПроверьте 
        выложили ли его?\n"""
        message += "https://raspisanie.madi.ru/tplan/r/?task=7"
        return message
        pass

    # Оставляем только нужные строки из расписания
    rasp_lines = get_rasp_from_text(table_rasp, week_day)

    rasp = get_cur_week_strings(rasp_lines, get_week_type())

    return rasp
    pass


if __name__ == '__main__':
    mes = main(week_day=datetime.today().weekday())
    print(mes)
