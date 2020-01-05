""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import re
from typing import NamedTuple

import pytz

from . import exceptions, spreadsheet, settings


MONTHS_MAP = {
    1: 'январе',
    2: 'феврале',
    3: 'марте',
    4: 'апреле',
    5: 'мае',
    6: 'июне',
    7: 'июле',
    8: 'августе',
    9: 'сентябре',
    10: 'октябре',
    11: 'ноябре',
    12: 'декабре',
}


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    is_expense: bool
    amount: int
    category_text: str
    description: str


def add_income(raw_message: str) -> spreadsheet.Income:

    parsed_message = _parse_message(raw_message)
    categories = spreadsheet.get_categories(of_expenses=False)

    category = parsed_message.category_text.title() if parsed_message.category_text.title() in categories else 'Другое'

    inserted = spreadsheet.insert(
        date_str=_get_now_formatted(),
        amount=parsed_message.amount,
        description=parsed_message.description,
        category_name=category,
        is_expense=False,
    )
    return inserted


def add_expense(raw_message: str) -> spreadsheet.Expense:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    parsed_message = _parse_message(raw_message)
    categories = spreadsheet.get_categories(of_expenses=True)

    category = parsed_message.category_text.title() if parsed_message.category_text.title() in categories else 'Другое'

    inserted = spreadsheet.insert(
        date_str=_get_now_formatted(),
        amount=parsed_message.amount,
        description=parsed_message.description,
        category_name=category,
        is_expense=True,
    )
    return inserted


def get_today_statistics() -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    until = datetime.date.today()

    expenses = spreadsheet.get_latest_items_sum(until=until, days=1, of_expenses=True)
    incomes = spreadsheet.get_latest_items_sum(until=until, days=1, of_expenses=False)
    return (
        f"Расходы сегодня: {expenses} {settings.CURRENCY}.\n"
        f"Доходы сегодня: {incomes} {settings.CURRENCY}.\n"
        f"Итого: {incomes - expenses} {settings.CURRENCY}\n"
        f"За текущий месяц: /month"
    )


def get_month_statistics() -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    until = datetime.date.today()
    day = datetime.date.today().day
    current_month = MONTHS_MAP[datetime.date.today().month]

    expenses = spreadsheet.get_latest_items_sum(until=until, days=day, of_expenses=True)
    incomes = spreadsheet.get_latest_items_sum(until=until, days=day, of_expenses=False)
    return (
        f"Расходы в {current_month}: {expenses} {settings.CURRENCY}.\n"
        f"Доходы в {current_month}: {incomes} {settings.CURRENCY}.\n"
        f"Итого: {incomes - expenses} {settings.CURRENCY}"
    )


def get_latest(number=5) -> str:
    """Возвращает последние несколько расходов"""
    gen = spreadsheet.get_latest_items(number)
    latest = {row: expense for expense, row in gen}
    message = "Последние сохранённые траты:\n\n"
    for key in latest.keys():
        expense = latest[key]
        message += (f"{expense.date}: {expense.amount} {settings.CURRENCY} на {expense.category_name} "
                    f"— нажми /del{key} для удаления\n\n")
    return message


def delete_expense(id: int) -> str:
    """Удаляет сообщение по его идентификатору"""
    try:
        spreadsheet.delete_expense(id)
    except exceptions.IncorrectId:
        message = "Пожалуйста, введи корректный id записи"
    except ValueError:
        message = f"Записи о расходе с id={id} не существует"
    else:
        message = "Удалено!"
    return message


def get_categories(global_categories: bool = True) -> str:
    expense_categories = spreadsheet.get_categories(global_categories=global_categories, of_expenses=True)
    income_categories = spreadsheet.get_categories(global_categories=global_categories, of_expenses=False)
    print(expense_categories)
    print(income_categories)
    message = "*Категории трат:*\n\n"
    message += ''.join([f'- {c}\n' for c in expense_categories])
    message += "\n\n*Категории доходов:*\n\n"
    message += ''.join([f'- {c}\n' for c in income_categories])
    return message


def _parse_message(raw_message: str) -> Message:
    """Парсит текст пришедшего сообщения о новом расходе или доходе"""
    regexp_result = re.match(r'^(/i)?\s*([\d]+)\s*(\S*)\s*(\(.*\))?$', raw_message)  # should be .* instead of \S*

    if not regexp_result or not regexp_result.group(2) or not regexp_result.group(3):
        if regexp_result and regexp_result.group(1):
            error_message = (
                "Не могу понять сообщение. Напишите сообщение в формате, "
                "например:\n\\i 1500 стипендия"
            )
        else:
            error_message = (
                "Не могу понять сообщение. Напишите сообщение в формате, "
                "например:\n1500 такси"
            )
        raise exceptions.NotCorrectMessage(error_message)

    is_expense = False if regexp_result.group(1) else True
    amount = regexp_result.group(2).replace(" ", "")
    category_text = regexp_result.group(3).strip().lower()
    description = regexp_result.group(4)
    if description:
        description = description.strip()[1:-1].lower()
    return Message(is_expense=is_expense, amount=int(amount), category_text=category_text, description=description)


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%d.%m.%Y")


def _get_now_datetime():
    """Возвращает сегодняшний datetime с учётом времненной зоны из settings."""
    tz = pytz.timezone(settings.TIMEZONE)
    now = datetime.datetime.now(tz)
    return now


# def _get_budget_limit() -> int:
#     """Возвращает дневной лимит трат для основных базовых трат"""
#     return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]
