import ast
import json

import bs4
import requests

WEEK_URL = "https://raspisanie.madi.ru/tplan/calendar.php"
GROUPS_URL = "https://raspisanie.madi.ru/tplan/tasks/task3,7_fastview.php"  # get запрос, для получения списка групп
TABLE_URL = "https://raspisanie.madi.ru/tplan/tasks/tableFiller.php"  # post запрос, для получения списка расписания

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


def clean_table(rasp_soup):
    table_str = str(rasp_soup)
    table_str = table_str.replace('<td>', '')
    table_str = table_str.replace('</td>', '')

    table_str = table_str.replace('</b>', '')
    table_str = table_str.replace('<b>', '')

    table_str = table_str.replace('<tr>', '')
    table_str = table_str.replace('</tr>', '\n')

    table_str = table_str.replace('<th colspan="6">', '')
    table_str = table_str.replace('</th>', '')

    table_str = table_str.replace('<td style="white-space:pre-wrap">', '')
    table_str = table_str.replace('<td colspan="2" rowspan="1">', '')

    table_str = table_str.replace('<table class="timetable">', '')
    table_str = table_str.replace('</table>', '')

    table_str = table_str.replace('<\', \'\', \'>', '')
    table_str = table_str.replace('             ', ' ')
    # print(table_str)
    return table_str


def final_clean(day_rasp):
    day_rasp = day_rasp.replace('\', \'\', \'', '\n')
    day_rasp = day_rasp.replace('\'', '')
    day_rasp = day_rasp.replace('.,', '.')
    return day_rasp


def get_group_id(group_name, dictionary):
    group_id = (dictionary.get(str(group_name)))
    if group_id is None:
        return -1
    else:
        return group_id
    pass


def get_table(group_id):
    # добавляем id группы в запрос
    cur_data = "{'tab': '7', 'gp_id': '" + str(group_id) + "'}"

    # Записываем ответ на наш запрос
    request = requests.post(TABLE_URL, data=ast.literal_eval(cur_data))

    # Находим фрагмент с расписанием
    table_soup = bs4.BeautifulSoup(request.text, "html.parser").select_one(".timetable")

    # table_soup = table_soup.find_all("td", {"colspan": True})
    # print(table_soup)
    return table_soup
    pass


def get_week_type(switch):
    req = requests.get(WEEK_URL)
    if not switch:
        if "\\u0447" in req.text:
            return "Числитель"
        if "\\u0437" in req.text:
            return "Знаменатель"
    else:
        if "\\u0447" in req.text:
            return "Знаменатель"
        if "\\u0437" in req.text:
            return "Числитель"


def get_weekday(weekday):
    weekday %= 7
    if weekday == 0:
        return "Понедельник"
    elif weekday == 1:
        return "Вторник"
    elif weekday == 2:
        return "Среда"
    elif weekday == 3:
        return "Четверг"
    elif weekday == 4:
        return "Пятница"
    elif weekday == 5:
        return "Суббота"
    elif weekday == 6:
        return "Воскресенье"
    pass


def get_lines_between_strings(soup, day):
    # Получаем день недели
    string_begin = get_weekday(day)

    # Получаем следующий день недели
    string_end = get_weekday(day + 1)

    text = str(soup)
    lines = []
    found_begin = False
    for line in text.split("\n"):
        if string_begin in line:
            found_begin = True
        if found_begin:
            lines.append(line)
        if string_end in line or "Полнодневные занятия" in line:
            found_begin = False
            break
    if found_begin:
        lines.pop()  # remove the string_end line if it was included
    return lines


def remove_target_strings(text, target_string):
    lines = text.split("\n")
    result = []
    for line in lines:
        if target_string in line or "Еженедельно" in line:
            result.append(line)
    return "\n".join(result)


def main(group_name="1мБД", day=None, week_type=None, switch_wt=False):

    if group_name is None:
        return "Настройте название группы"
    else:
        group_name = group_name.lower()

    if day is None and week_type is None:
        # создаём словарь групп
        # ключ - id
        # значение - название группы
        groups_dict = get_groups_dict()

        if groups_dict == -1:
            return -1

        # Берём id группы по названию группы из словаря групп
        group_id = get_group_id(group_name, groups_dict)

        if group_id == -1:
            return 0
        else:
            return 1

    # Получаем тип недели
    if week_type is None:
        week_type = get_week_type(switch_wt)

    # создаём словарь групп
    # ключ - id
    # значение - название группы
    groups_dict = get_groups_dict()

    if groups_dict == -1:
        return "Не удалось получить список групп"

    # Берём id группы по названию группы из словаря групп
    group_id = get_group_id(group_name, groups_dict)

    if group_id == -1:
        return "Такой группы нет"

    # Запрашиваем расписание по id группы
    table_rasp = get_table(group_id)

    # Проверяем нашли ли мы расписание на сайте
    if table_rasp is None:
        message = "Не удалось получить расписание с сайта.\nПроверьте выложили ли его?\n"
        message += "https://raspisanie.madi.ru/tplan/r/?task=7"
        return message
        pass

    # Оставляем только нужные строки из расписания
    table_lines = get_lines_between_strings(table_rasp, day)

    # Получаем только строки сегодняшнего дня
    day_rasp = clean_table(table_lines)

    # Удаляем строки расписания без текущего типа недели
    day_rasp = remove_target_strings(day_rasp, week_type)

    day_rasp = final_clean(day_rasp)

    # Выводим расписание
    message = "Группа\n" + group_name
    message += "\n" + week_type
    message += "\n" + "Расписание:\n\n"
    message += get_weekday(day)
    message += "\n"

    if day_rasp == "":
        message += "На выбранный день пар нет"
    else:
        message += day_rasp

    return message
    pass


if __name__ == '__main__':
    main()
