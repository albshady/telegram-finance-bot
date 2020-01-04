""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import re
from typing import NamedTuple

import pytz

from . import exceptions
from . import spreadsheet
from .settings import CURRENCY, TIMEZONE


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str
    description: str


def add_expense(raw_message: str) -> spreadsheet.Expense:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    parsed_message = _parse_message(raw_message)
    categories = spreadsheet.get_categories(of_expenses=True)

    category = parsed_message.category_text.title() if parsed_message.category_text.title() in categories else 'Другое'

    inserted = spreadsheet.insert_expense(
        date_str=_get_now_formatted(),
        amount=parsed_message.amount,
        description=parsed_message.description,
        category_name=category,
    )
    return inserted


def get_today_statistics() -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    result = spreadsheet.get_expenses_sum(until=datetime.date.today(), number_of_days=1)
    # base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы сегодня: {result} {CURRENCY}.\n"
            f"За текущий месяц: /month")


def get_month_statistics() -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    result = spreadsheet.get_expenses_sum(until=datetime.date.today(), number_of_days=datetime.date.today().day)
    # base_today_expenses = result[0] if result[0] else 0
    return (
        f"Расходы в текущем месяце:\n"
        f"всего — {result} {CURRENCY}\n"
        # f"базовые — {base_today_expenses} {CURRENCY}. из "
        # f"{now.day * _get_budget_limit()} {CURRENCY}"
    )


def get_latest(number=5) -> str:
    """Возвращает последние несколько расходов"""
    latest = spreadsheet.get_latest_expenses(number)
    message = 'Последние сохранённые траты:\n\n'
    for key in latest.keys():
        expense = latest[key]
        message += f'{expense.date}: {expense.amount} {CURRENCY} на {expense.category_name} ' \
                   f'— нажми /del{key} для удаления\n\n'
    return message


def delete_expense(id: int) -> str:
    """Удаляет сообщение по его идентификатору"""
    try:
        spreadsheet.delete_expense(id)
    except AttributeError:
        message = 'Пожалуйста, введи корректный id записи'
    except ValueError:
        message = f'Записи о расходе с id={id} не существует'
    else:
        message = 'Удалено!'
    return message


def get_categories(global_categories: bool = True, of_expenses: bool = True) -> str:
    categories = spreadsheet.get_categories(global_categories=global_categories, of_expenses=of_expenses)
    message = "Категории трат:\n\n".join([c + '\n' for c in categories])
    return message


def _parse_message(raw_message: str) -> Message:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.match(r"([\d]+)\s*(\S*)\s*(\(.*\))?", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n1500 такси"
        )

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    description = regexp_result.group(3)
    if description:
        description = description.strip()[1:-1].lower()
    return Message(amount=int(amount), category_text=category_text, description=description)


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%d.%m.%Y")


def _get_now_datetime():
    """Возвращает сегодняшний datetime с учётом времненной зоны из settings."""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    return now


# def _get_budget_limit() -> int:
#     """Возвращает дневной лимит трат для основных базовых трат"""
#     return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]
