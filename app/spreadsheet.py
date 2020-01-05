import datetime
import json
import os
from typing import NamedTuple, List, Tuple

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from . import settings
from . import exceptions

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = os.environ.get('CREDS', False)
if creds:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds), scope)
else:
    creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.dirname(__file__) + '/../client_creds.json', scope)
client = gspread.authorize(creds)

expenses_sheet = client.open(settings.SHEET_NAME).get_worksheet(settings.SHEETS.get('expenses'))
incomes_sheet = client.open(settings.SHEET_NAME).get_worksheet(settings.SHEETS.get('incomes'))
categories_sheet = client.open(settings.SHEET_NAME).get_worksheet(settings.SHEETS.get('categories'))


class Expense(NamedTuple):
    """Structure of an expense added to Google Spreadsheets"""
    id: int
    date: str
    amount: int
    description: str
    category_name: str


def insert_expense(date_str: str, amount: int, description: str, category_name: str) -> Expense:
    latest, _ = next(get_latest_expenses())
    id = 1 if latest.id == '' else int(latest.id) + 1
    expense = Expense(*[id, date_str, amount, description, category_name])
    expenses_sheet.insert_row(expense, index=2)
    return expense


def delete_expense(id: int) -> Expense:
    g = get_latest_expenses()
    latest, row = next(g)
    if id < 1:
        raise exceptions.IncorrectId('id must be > 0')
    while latest.id != '' and int(latest.id) > id:
        latest, row = next(g)
    if latest.id == '' or int(latest.id) < id:
        raise ValueError(f'No expense with id={id}')
    else:
        expenses_sheet.delete_row(row)
        return latest


""" No need in this func since the following one is doing the same thing
def get_latest_expenses(number: int = 5) -> Dict[int, Expense]:
    return {row: Expense(*[expenses_sheet.cell(row, col).value for col in range(1, 6)]) for row in range(2, 2 + number)}
"""


def get_latest_expenses(count: int = None) -> Tuple[Expense, int]:
    row = 2
    expense = Expense(*[expenses_sheet.cell(row, col).value for col in range(1, 6)])
    if count and count <= 0:
        raise AttributeError('Count must be > 0')
    while expense.id != '':
        yield (expense, row)
        row += 1
        expense = Expense(*[expenses_sheet.cell(row, col).value for col in range(1, 6)])
        if count:
            count -= 1
            if count <= 0:
                break


def get_expenses_sum(until: datetime.date = datetime.date.today(), number_of_days: int = 1) -> int:
    # TODO: rewrite this func
    expenses_sum = 0
    g = get_latest_expenses()

    latest, _ = next(g)
    current_day = datetime.date(*[int(latest.date.split('.')[i]) for i in range(2, -1, -1)])
    while current_day > (until - datetime.timedelta(days=number_of_days)):
        expenses_sum += int(latest.amount)
        latest, _ = next(g)
        if len(latest.date.split('.')) < 3:
            break
        current_day = datetime.date(*[int(latest.date.split('.')[i]) for i in range(2, -1, -1)])
    return expenses_sum


def get_categories(global_categories: bool = True, of_expenses: bool = True) -> List[str]:
    if global_categories:
        col = 1 if of_expenses else 3
        return sorted(categories_sheet.col_values(col))[:-1]


if __name__ == '__main__':
    print(get_latest_expenses())
