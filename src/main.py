import json
import os
from typing import Any, Dict, Hashable

from src.external_api import get_currency_rate, get_stock_price
from src.utils import get_date_interval, get_date_interval_events, get_greeting, read_file
from src.views import (
    get_cards_info,
    get_category_amount,
    get_filtered_transactions,
    get_top_5_transactions,
    get_transaction_exchange,
    get_transfers_and_cash,
)

base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "..", "user_settings.json")

with open(file_path, "r", encoding="utf-8") as f:
    user_settings = json.load(f)


def get_exchange_stock(result: Dict[Hashable, Any]) -> Dict[Hashable, Any]:
    result["currency_rates"] = [
        {currency: get_currency_rate(currency)} for currency in user_settings["user_currencies"]
    ]

    # Добавляем информацию об акциях
    result["stock_prices"] = [
        {"stock": stock, "price": get_stock_price(stock)} for stock in user_settings["user_stocks"]
    ]
    return result


def main_page(input_date: str) -> str:
    result = dict()

    # Добавляем приветствие
    result["greeting"] = get_greeting()

    # Читаем и фильтруем данные
    transactions = read_file("operations.xlsx")
    start, end = get_date_interval(input_date)
    transactions = get_filtered_transactions(transactions, start, end)

    if transactions.empty:
        result["cards"] = []
        result["top_transactions"] = []
        result["currency_rates"] = [
            {currency: get_currency_rate(currency)} for currency in user_settings["user_currencies"]
        ]
        result["stock_prices"] = [{stock: get_stock_price(stock)} for stock in user_settings["user_stocks"]]
        return ""

    # Вытаскиваем расходы
    expenses = transactions[transactions["Сумма платежа"] < 0].copy()
    expenses["Сумма платежа"] = expenses["Сумма платежа"].abs()
    expenses = get_transaction_exchange(expenses)

    # Добавляем информацию о картах
    result["cards"] = get_cards_info(expenses)

    # Добавляем информацию о топ-5 транзакциях
    result["top_transactions"] = get_top_5_transactions(expenses)

    # Добавляем информацию о курсах валют и акциях
    result = get_exchange_stock(result)

    return json.dumps(result, ensure_ascii=False, indent=2)


def events_page(input_date: str, range_type: str = "M") -> str:
    transactions = read_file("operations.xlsx")
    start, end = get_date_interval_events(input_date, range_type=range_type)
    transactions = get_filtered_transactions(transactions, start, end)
    transactions = get_transaction_exchange(transactions)

    result = {"expenses": {}, "income": {}}

    # Работаем с расходами
    # Добавляем общую сумму расходов
    expenses = transactions[transactions["Сумма платежа_ex"] < 0]
    expenses.loc[:, "Сумма платежа_ex"] = abs(expenses["Сумма платежа_ex"])
    result["expenses"]["total_amount"] = round(float(expenses["Сумма платежа_ex"].sum()))

    # Добавляем расходы по категориям
    category_expenses = get_category_amount(expenses, income=False)
    result["expenses"]["main"] = category_expenses

    # Добавляем раздел «Переводы и наличные»
    transfers_and_cash = get_transfers_and_cash(expenses)
    result["expenses"]["transfers_and_cash"] = transfers_and_cash

    # Работаем с поступлениями
    # Добавляем общую сумму поступлений
    income = transactions[transactions["Сумма платежа_ex"] > 0]
    result["income"]["total_amount"] = round(float(income["Сумма платежа_ex"].sum()))

    # Добавляем расходы по категориям
    category_income = get_category_amount(income, income=True)
    result["income"]["main"] = category_income

    # Добавляем информацию о курсах валют и акциях
    result = get_exchange_stock(result)

    return json.dumps(result, ensure_ascii=False, indent=2)


# if __name__ == "__main__":
# transactions = read_file("operations.xlsx")
#     print(main_page(input_date="2021-05-20 17:30:24"))
# print(events_page(input_date="2021-05-20 17:30:24"))
