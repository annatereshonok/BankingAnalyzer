import json
from unittest.mock import patch

import pandas as pd

from src.main import events_page, get_exchange_stock, main_page


@patch("src.main.get_currency_rate")
@patch("src.main.get_stock_price")
def test_get_exchange_stock(mock_get_stock, mock_get_currency):
    mock_get_currency.side_effect = lambda x: 90.0 if x == "USD" else 98.5
    mock_get_stock.side_effect = lambda x: 150.0 if x == "AAPL" else 2800.0 if x == "GOOGL" else 700.0

    result = get_exchange_stock({})

    expected_currencies = [{"USD": 90.0}, {"EUR": 98.5}]

    assert result["currency_rates"] == expected_currencies
    assert any(stock["stock"] == "AAPL" for stock in result["stock_prices"])
    assert any(stock["stock"] == "GOOGL" for stock in result["stock_prices"])


@patch(
    "src.main.user_settings",
    new_callable=lambda: {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]},
)
@patch("src.main.read_file")
@patch("src.main.get_filtered_transactions")
@patch("src.main.get_greeting", return_value="Добрый день")
@patch("src.views.get_currency_rate", side_effect=lambda x: 90.0 if x == "USD" else 98.5)
@patch("src.main.get_currency_rate", side_effect=lambda x: 90.0 if x == "USD" else 98.5)
@patch("src.main.get_stock_price", side_effect=lambda x: 150.0 if x == "AAPL" else 2800.0)
def test_main_page(
    mock_get_stock,
    mock_get_currency,
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
    "src.main.user_settings",
    new_callable=lambda: {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]},
)
@patch("src.main.read_file")
@patch("src.main.get_filtered_transactions")
@patch("src.views.get_currency_rate", side_effect=lambda x: 90.0 if x == "USD" else 98.5)
@patch("src.main.get_currency_rate", side_effect=lambda x: 90.0 if x == "USD" else 98.5)
@patch("src.main.get_stock_price", side_effect=lambda x: 150.0 if x == "AAPL" else 2800.0)
def test_events_page(
    mock_get_stock,
    mock_get_currency,
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
