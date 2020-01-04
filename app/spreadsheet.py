import datetime
import os
from typing import NamedTuple, List, Dict

import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]


creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.dirname(__file__) + '/../client_secret.json', scope)
client = gspread.authorize(creds)

expense_sheet = client.open('Budget').get_worksheet(0)
categories_sheet = client.open('Budget').get_worksheet(1)


class Expense(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    date: str
    amount: int
    description: str
    category_name: str


def insert_expense(date_str: str, amount: int, description: str, category_name: str) -> Expense:
    print(date_str)
    expense = Expense(*[date_str, amount, description, category_name])
    expense_sheet.insert_row(expense, index=2)
    return expense


def delete_expense(row: int) -> None:
    if row < 2:
        raise AttributeError
    expense_sheet.delete_row(row)


def get_latest_expenses(number: int = 5) -> Dict:
    return {row: Expense(*[expense_sheet.cell(row, col).value for col in range(1, 5)]) for row in range(2, 2 + number)}


def get_expenses():
    pointer = 2
    while True:
        expense = Expense(*[expense_sheet.cell(pointer, col).value for col in range(1, 5)])
        yield expense
        pointer += 1


def get_expenses_sum(until: datetime.date = datetime.date.today(), number_of_days: int = 1) -> int:
    # TODO: rewrite this func
    expenses_sum = 0
    g = get_expenses()

    latest = next(g)
    current_day = datetime.date(*[int(latest.date.split('.')[i]) for i in range(2, -1, -1)])
    while current_day > (until - datetime.timedelta(days=number_of_days)):
        expenses_sum += int(latest.amount)
        latest = next(g)
        if len(latest.date.split('.')) < 3:
            break
        current_day = datetime.date(*[int(latest.date.split('.')[i]) for i in range(2, -1, -1)])
    return expenses_sum


def get_categories(global_categories: bool = True, of_expenses: bool = True) -> List[str]:
    if global_categories:
        col = 1 if of_expenses else 3
        return sorted(categories_sheet.col_values(col))[:-1]

