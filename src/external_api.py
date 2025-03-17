import os
from typing import Optional

import requests
import yfinance as yf
from dotenv import load_dotenv

from src.logging_config import api_logger

load_dotenv()

API_KEY = os.getenv("CURRENCY_API_KEY")
HEADERS = {"apikey": API_KEY}
CURRENCY_RATE_URL = "https://api.apilayer.com/exchangerates_data/latest?"


def get_currency_rate(base: str) -> float:
    """
    Получает курс валюты по отношению к российскому рублю (RUB).

    :param base: Базовая валюта (например, "USD", "EUR").
    :return: Курс валюты к RUB в виде float.
    :raises requests.RequestException: Если произошла ошибка при запросе к API.
    :raises ValueError: Если API вернул некорректные данные или отсутствует курс.
    """
    payload = {"symbols": "RUB", "base": base}

    try:
        api_logger.info(f"Запрос курса валюты: {base} -> RUB")
        response = requests.get(CURRENCY_RATE_URL, headers=HEADERS, params=payload)
        response.raise_for_status()
        rate = response.json()["rates"]["RUB"]
        api_logger.info(f"Курс {base} -> RUB: {rate}")
        return float(rate)
    except requests.RequestException as e:
        api_logger.error(f"Ошибка запроса к API валют: {e}")
        raise requests.RequestException("Ошибка при запросе к API")
    except KeyError:
        api_logger.error("Ошибка данных API: отсутствует ключ 'rate'")
        raise ValueError("Ошибка в данных API: нет ключа 'rate'")


def get_stock_price(ticker_symbol: str) -> Optional[float]:
    """
    Получает текущую цену акции для заданного тикера.

    :param ticker_symbol: Символ тикера (например, "AAPL", "TSLA").
    :return: Цена акции в виде float или None, если данные недоступны.
    :raises ValueError: Если API вернул некорректные данные.
    """
    try:
        api_logger.info(f"Запрос цены акции: {ticker_symbol}")
        ticker = yf.Ticker(ticker_symbol)
        currency = ticker.info.get("currency")

        if currency and currency != "RUB":
            exchange_rate = get_currency_rate(base=currency)
        else:
            exchange_rate = 1
            api_logger.warning(f"Валюта для {ticker_symbol} не найдена или RUB")

        if "last_price" in ticker.fast_info:
            price = ticker.fast_info["last_price"]
        elif "currentPrice" in ticker.info:
            price = ticker.info["currentPrice"]
        else:
            api_logger.warning(f"Цена для {ticker_symbol} недоступна")
            return None

        price_rub = price / exchange_rate
        api_logger.info(f"Цена {ticker_symbol} в RUB: {round(price_rub, 2)}")
        return round(price_rub, 2)
    except KeyError as e:
        api_logger.error(f"KeyError - отсутствует ключ {e} в данных {ticker_symbol}")
    except ValueError as e:
        api_logger.error(f"ValueError - некорректные данные для {ticker_symbol}: {e}")
    except Exception as e:
        api_logger.error(f"Ошибка получения цены {ticker_symbol}: {e}")
    return None
