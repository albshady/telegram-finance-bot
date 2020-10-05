import datetime
import json
import os
from typing import NamedTuple, List, Tuple, Union

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from app import settings, exceptions

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


class SpreadsheetItem(NamedTuple):
    id: int
    date: str
    amount: int
    description: str
    category_name: str


class Expense(SpreadsheetItem):
    """Structure of an expense added to Google Spreadsheets"""


class Income(SpreadsheetItem):
    """Structure of an income added to Google Spreadsheets"""


def insert(date_str: str, amount: int, description: str, category: str, is_expense=True) -> Union[Expense, Income]:
    (klass, sheet) = (Expense, expenses_sheet) if is_expense else (Income, incomes_sheet)

    try:
        latest, _ = next(get_latest_items(of_expenses=is_expense))
    except StopIteration:
        id = 1
    else:
        id = int(latest.id) + 1

    item = klass(*[id, date_str, amount, description, category])
    sheet.insert_row(item, index=settings.FIRST_ROW)
    return item


def delete_expense(id: int) -> Expense:
    g = get_latest_items()
    latest, row_number = next(g)
    if id < 1:
        raise exceptions.IncorrectId('id must be > 0')
    while latest.id != '' and int(latest.id) > id:
        latest, row_number = next(g)
    if latest.id == '' or int(latest.id) < id:
        raise ValueError(f'No expense with id={id}')
    else:
        expenses_sheet.delete_row(row_number)
        return latest


def transform_amount(amount_raw: str) -> int:
    try:
        amount = int(amount_raw)
    except ValueError:
        amount = ''
        for letter in amount_raw:
            try:
                int(letter)
            except ValueError:
                if letter == '-':
                    amount += letter
            else:
                amount += letter
    return amount


def transform_params(params: list) -> List:
    amount_str = params.pop(2)
    params.insert(2, transform_amount(amount_str))
    return params


def get_latest_items(count: int = None, of_expenses: bool = True) -> Tuple[Expense or Income, int]:
    row_number = settings.FIRST_ROW
    (klass, sheet) = (Expense, expenses_sheet) if of_expenses else (Income, incomes_sheet)

    if count and count <= 0:
        raise AttributeError('Count must be > 0')

    params = [sheet.cell(row_number, col).value for col in range(1, 6)]
    item = klass(*transform_params(params))

    while item.id != '':
        yield (item, row_number)
        row_number += 1
        params = [sheet.cell(row_number, col).value for col in range(1, 6)]
        item = klass(*transform_params(params))
        if count:
            count -= 1
            if count <= 0:
                break


def get_latest_items_sum(until: datetime.date = datetime.date.today(), days: int = 1, of_expenses: bool = True) -> int:
    items_sum = 0
    g = get_latest_items(of_expenses=of_expenses)

    try:
        latest, _ = next(g)
    except StopIteration:
        return items_sum
    latest_date = latest.date.split('.')
    if len(latest_date) < 3:
        return items_sum

    current_day = datetime.date(*([int(param) for param in reversed(latest_date)]))
    checkpoint = until - datetime.timedelta(days=days)

    while current_day > checkpoint:
        items_sum += int(latest.amount)
        try:
            latest, _ = next(g)
        except StopIteration:
            break
        else:
            latest_date = latest.date.split('.')
            if len(latest_date) < 3:
                break
            current_day = datetime.date(*([int(param) for param in reversed(latest_date)]))

    return items_sum


def get_categories() -> Tuple[List[str], List[str]]:
    expenses = sorted(categories_sheet.col_values(settings.EXPENSES_COLUMN)[1:])
    incomes = sorted(categories_sheet.col_values(settings.INCOMES_COLUMN)[1:])
    return expenses, incomes
