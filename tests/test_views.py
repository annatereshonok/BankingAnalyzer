import json
from unittest.mock import patch

import pandas as pd

from src.views import (
    events_page,
    get_card_number,
    get_card_sum_cashback,
    get_cards_info,
    get_category_amount,
    get_exchange_stock,
    get_filtered_transactions,
    get_top_5_transactions,
    get_transaction_exchange,
    get_transfers_and_cash,
    main_page,
)


def test_get_card_number():
    assert get_card_number("*5678") == "5678"
    assert get_card_number("9876") == "9876"
    assert get_card_number("") == "Нет информации о карте"
    assert get_card_number("abcd") == "Нет информации о карте"


def test_get_filtered_transactions(filtered_transactions_fixture):
    transactions, start_date, end_date, expected_result = filtered_transactions_fixture
    transactions = pd.DataFrame(transactions)
    filtered = get_filtered_transactions(transactions, start_date, end_date)
    assert len(filtered) == expected_result


@patch("src.views.get_currency_rate", side_effect=lambda x: 10 if x == "CNY" else 1)
def test_get_transaction_exchange(mock_get_currency_rate, transactions):
    transactions = pd.DataFrame(transactions).head(2)
    exchanged = get_transaction_exchange(transactions)

    assert "Сумма платежа_ex" in exchanged.columns
    assert float(exchanged.loc[exchanged["Валюта платежа"] == "RUB", "Сумма платежа_ex"].iloc[0]) == -160.89
    assert float(exchanged.loc[exchanged["Валюта платежа"] == "CNY", "Сумма платежа_ex"].iloc[0]) == -10


@patch("src.views.get_currency_rate", side_effect=lambda x: 10 if x == "CNY" else 1)
def test_get_transaction_exchange_error(mock_get_currency_rate, transaction_exchange_error_fixture):
    transactions = pd.DataFrame(transaction_exchange_error_fixture)
    exchanged = get_transaction_exchange(transactions)
    assert len(exchanged) == 2


def test_get_card_sum_cashback(transactions):
    transactions = pd.DataFrame(transactions)
    transactions["Сумма платежа_ex"] = transactions["Сумма платежа"]

    total, cashback = get_card_sum_cashback(transactions, None)
    assert total == sum(transactions["Сумма платежа"])
    assert cashback == round(total / 100, 2)


def test_get_card_sum_cashback_error(card_sum_cashback_fixture):
    transactions, card_number, exp_total, exp_cashback = card_sum_cashback_fixture
    transactions = pd.DataFrame(transactions)

    total, cashback = get_card_sum_cashback(transactions, card_number)
    assert total == exp_total
    assert cashback == exp_cashback


def test_get_cards_info(transactions):
    transactions = pd.DataFrame(transactions)
    transactions["Сумма платежа_ex"] = transactions["Сумма платежа"]
    cards_info = get_cards_info(transactions)
    assert len(cards_info) == 2
    assert cards_info[0]["last_digits"] == "7197"


def test_get_cards_info_key_error(cards_info_key_error_fixture):
    transactions, expected_result = cards_info_key_error_fixture
    transactions = pd.DataFrame(cards_info_key_error_fixture)
    cards_info = get_cards_info(transactions)
    assert cards_info == expected_result


def test_get_top_5_transactions(transactions):
    transactions = pd.DataFrame(transactions)
    transactions["Сумма платежа_ex"] = transactions["Сумма платежа"].abs()
    top_5 = get_top_5_transactions(transactions)
    assert len(top_5) == 5
    assert top_5[0]["amount"] == 160.89


def test_get_top_5_transactions_key_error(transactions):
    transactions = pd.DataFrame(transactions)
    top_5 = get_top_5_transactions(transactions)
    assert top_5 == []


def test_get_category_amount(transactions):
    transactions = pd.DataFrame(transactions)
    transactions["Сумма платежа_ex"] = transactions["Сумма платежа"]
    category_amount = get_category_amount(transactions, income=False)
    assert isinstance(category_amount, list)
    assert len(category_amount[0]) > 0


def test_get_category_amount_key_error():
    transactions = pd.DataFrame([])
    category_amount = get_category_amount(transactions, income=False)
    assert category_amount == [{}]


def test_get_transfers_and_cash(transactions):
    transactions = pd.DataFrame(transactions)
    transactions["Сумма платежа_ex"] = transactions["Сумма платежа"]
    transfers_cash = get_transfers_and_cash(transactions)
    assert len(transfers_cash[0]) > 0
    assert "Переводы" in transfers_cash[0]
    assert "Наличные" in transfers_cash[0]


def test_get_transfers_and_cash_key_error():
    transactions = pd.DataFrame([])
    transfers_cash = get_transfers_and_cash(transactions)
    assert transfers_cash == [{}]


@patch("src.views.get_currency_rate")
@patch("src.views.get_stock_price")
def test_get_exchange_stock(mock_get_stock, mock_get_currency):
    mock_get_currency.side_effect = lambda x: 90.0 if x == "USD" else 98.5
    mock_get_stock.side_effect = lambda x: 150.0 if x == "AAPL" else 2800.0 if x == "GOOGL" else 700.0

    result = get_exchange_stock({})

    expected_currencies = [{"USD": 90.0}, {"EUR": 98.5}]

    assert result["currency_rates"] == expected_currencies
    assert any(stock["stock"] == "AAPL" for stock in result["stock_prices"])
    assert any(stock["stock"] == "GOOGL" for stock in result["stock_prices"])


@patch(
    "src.views.user_settings",
    new_callable=lambda: {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]},
)
@patch("src.views.read_file")
@patch("src.views.get_filtered_transactions")
@patch("src.views.get_greeting", return_value="Добрый день")
@patch("src.views.get_currency_rate", side_effect=lambda x: 90.0 if x == "USD" else 98.5)
@patch("src.views.get_stock_price", side_effect=lambda x: 150.0 if x == "AAPL" else 2800.0)
def test_main_page(
    mock_get_stock,
    mock_get_currency_view,
    mock_get_greeting,
    mock_get_filtered_transactions,
    mock_read_file,
    mock_user_settings,
):
    transactions = [
        {
            "Дата операции": "31.12.2021 16:44:00",
            "Дата платежа": "31.12.2021",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -160.89,
            "Валюта операции": "RUB",
            "Сумма платежа": -160.89,
            "Валюта платежа": "RUB",
            "Кэшбэк": "nan",
            "Категория": "Переводы",
            "MCC": 5411.0,
            "Описание": "Колхоз",
            "Бонусы (включая кэшбэк)": 3,
            "Округление на инвесткопилку": 0,
            "Сумма операции с округлением": 160.89,
        },
        {
            "Дата операции": "31.12.2021 01:20:42",
            "Дата платежа": "31.12.2021",
            "Номер карты": "*5091",
            "Статус": "OK",
            "Сумма операции": -100,
            "Валюта операции": "CNY",
            "Сумма платежа": -100,
            "Валюта платежа": "CNY",
            "Кэшбэк": "nan",
            "Категория": "Наличные",
            "MCC": 5399.0,
            "Описание": "Ozon.ru",
            "Бонусы (включая кэшбэк)": 5,
            "Округление на инвесткопилку": 0,
            "Сумма операции с округлением": 100,
        },
        {
            "Дата операции": "31.12.2021 01:20:42",
            "Дата платежа": "31.12.2021",
            "Номер карты": "*5091",
            "Статус": "OK",
            "Сумма операции": 100,
            "Валюта операции": "RUB",
            "Сумма платежа": 100,
            "Валюта платежа": "CNY",
            "Кэшбэк": "nan",
            "Категория": "Магазин",
            "MCC": 5399.0,
            "Описание": "Ozon.ru",
            "Бонусы (включая кэшбэк)": 5,
            "Округление на инвесткопилку": 0,
            "Сумма операции с округлением": 100,
        },
    ]
    mock_read_file.return_value = pd.DataFrame(transactions)
    mock_get_filtered_transactions.return_value = pd.DataFrame(transactions)

    result = main_page("2021-12-31 01:23:42")
    result_dict = json.loads(result)

    assert len(result_dict["cards"]) > 0
    assert len(result_dict["top_transactions"]) > 0
    assert result_dict["currency_rates"] == [{"USD": 90.0}, {"EUR": 98.5}]
    assert result_dict["stock_prices"] == [{"stock": "AAPL", "price": 150.0}, {"stock": "GOOGL", "price": 2800.0}]


@patch(
    "src.views.user_settings",
    new_callable=lambda: {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]},
)
@patch("src.views.read_file")
@patch("src.views.get_filtered_transactions")
@patch("src.views.get_currency_rate", side_effect=lambda x: 90.0 if x == "USD" else 98.5)
@patch("src.views.get_stock_price", side_effect=lambda x: 150.0 if x == "AAPL" else 2800.0)
def test_events_page(
    mock_get_stock,
    mock_get_currency_view,
    mock_get_filtered_transactions,
    mock_read_file,
    user_settings,
):
    transactions = [
        {
            "Дата операции": "31.12.2021 16:44:00",
            "Дата платежа": "31.12.2021",
            "Номер карты": "*7197",
            "Статус": "OK",
            "Сумма операции": -160.89,
            "Валюта операции": "RUB",
            "Сумма платежа": -160.89,
            "Валюта платежа": "RUB",
            "Кэшбэк": "nan",
            "Категория": "Переводы",
            "MCC": 5411.0,
            "Описание": "Колхоз",
            "Бонусы (включая кэшбэк)": 3,
            "Округление на инвесткопилку": 0,
            "Сумма операции с округлением": 160.89,
        },
        {
            "Дата операции": "31.12.2021 01:20:42",
            "Дата платежа": "31.12.2021",
            "Номер карты": "*5091",
            "Статус": "OK",
            "Сумма операции": -100,
            "Валюта операции": "CNY",
            "Сумма платежа": -100,
            "Валюта платежа": "CNY",
            "Кэшбэк": "nan",
            "Категория": "Наличные",
            "MCC": 5399.0,
            "Описание": "Ozon.ru",
            "Бонусы (включая кэшбэк)": 5,
            "Округление на инвесткопилку": 0,
            "Сумма операции с округлением": 100,
        },
        {
            "Дата операции": "31.12.2021 01:20:42",
            "Дата платежа": "31.12.2021",
            "Номер карты": "*5091",
            "Статус": "OK",
            "Сумма операции": 100,
            "Валюта операции": "RUB",
            "Сумма платежа": 100,
            "Валюта платежа": "CNY",
            "Кэшбэк": "nan",
            "Категория": "Магазин",
            "MCC": 5399.0,
            "Описание": "Ozon.ru",
            "Бонусы (включая кэшбэк)": 5,
            "Округление на инвесткопилку": 0,
            "Сумма операции с округлением": 100,
        },
    ]
    mock_read_file.return_value = pd.DataFrame(transactions)
    mock_get_filtered_transactions.return_value = pd.DataFrame(transactions)

    result = events_page("2021-12-31 01:23:42")
    result_dict = json.loads(result)

    assert "expenses" in result_dict
    assert "income" in result_dict
    assert result_dict["currency_rates"] == [{"USD": 90.0}, {"EUR": 98.5}]
    assert result_dict["stock_prices"] == [{"stock": "AAPL", "price": 150.0}, {"stock": "GOOGL", "price": 2800.0}]
