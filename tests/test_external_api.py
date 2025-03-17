from unittest.mock import patch

import pytest
import requests

from src.external_api import get_currency_rate, get_stock_price


@patch("src.external_api.requests.get")
def test_get_currency_rate(mocked_get):
    mocked_get.return_value.status_code = 200
    mocked_get.return_value.json.return_value = {"rates": {"RUB": 100.0}}
    expected_value = 100.0

    assert get_currency_rate(base="RUB") == expected_value
    mocked_get.assert_called_once()


@patch("src.external_api.requests.get", side_effect=requests.exceptions.HTTPError())
def test_get_currency_http_error(mocked_get):
    with pytest.raises(requests.exceptions.RequestException, match="Ошибка при запросе к API"):
        get_currency_rate(base="RUB")


@patch("src.external_api.requests.get")
def test_get_currency_key_error(mocked_get):
    mocked_get.return_value.status_code = 200
    mocked_get.return_value.json.return_value = {}
    with pytest.raises(ValueError, match="Ошибка в данных API: нет ключа 'rate'"):
        get_currency_rate(base="RUB")


@patch("src.external_api.get_currency_rate")
@patch("src.external_api.yf.Ticker")
def test_get_stock_prices_fast_info(mock_ticker, mock_currency):
    mock_currency.return_value = 100
    mock_ticker.return_value.fast_info = {"last_price": 150}
    mock_ticker.return_value.info = {"currency": "USD"}

    result = get_stock_price("AAPL")
    assert result == 1.5


@patch("src.external_api.yf.Ticker")
def test_get_stock_prices_current_price(mock_ticker):
    mock_ticker.return_value.info = {"currency": "RUB", "currentPrice": 150}

    result = get_stock_price("AAPL")
    assert result == 150


@patch("src.external_api.get_currency_rate")
@patch("src.external_api.yf.Ticker")
def test_get_stock_prices_rub(mock_ticker, mock_currency):
    mock_ticker.return_value.fast_info = {"last_price": 150}
    mock_ticker.return_value.info = {"currency": "RUB"}

    result = get_stock_price("AAPL")
    assert result == 150


@patch("src.external_api.get_currency_rate")
@patch("src.external_api.yf.Ticker")
def test_get_stock_prices_undefined(mock_ticker, mock_currency):
    mock_currency.return_value = 100
    mock_ticker.return_value.fast_info = {}

    result = get_stock_price("AAPL")
    assert result is None


@patch("src.external_api.yf.Ticker", side_effect=ValueError)
def test_get_stock_prices_value_error(mock_ticker):
    result = get_stock_price("AAPL")
    assert result is None


@patch("src.external_api.yf.Ticker", side_effect=Exception)
def test_get_stock_prices_exception(mock_ticker):
    result = get_stock_price("AAPL")
    assert result is None


@patch("src.external_api.yf.Ticker", side_effect=KeyError)
def test_get_stock_prices_key_error(mock_ticker):
    result = get_stock_price("AAPL")
    assert result is None
