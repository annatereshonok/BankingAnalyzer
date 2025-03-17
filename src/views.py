import re
from datetime import date
from typing import Any, Dict, Hashable, List, Optional

import pandas as pd

from src.external_api import get_currency_rate
from src.logging_config import views_logger

# from src.utils import read_file


def get_card_number(card_number: str) -> str:
    """
    Извлекает последние 4 цифры номера карты.

    :param card_number: Полный номер карты в виде строки.
    :return: Последние 4 цифры номера карты или сообщение об ошибке.
    """
    try:
        card_clean = re.findall(r"\d+", str(card_number))
        return card_clean[0][-4:] if card_clean else "Нет информации о карте"
    except TypeError:
        views_logger.error("Ошибка: неверный формат номера карты")


def get_filtered_transactions(transactions: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """
    Фильтрует транзакции, оставляя только расходы в заданном диапазоне дат.

    :param transactions: DataFrame с данными о транзакциях.
    :param start: Дата начала периода.
    :param end: Дата окончания периода.
    :return: Отфильтрованный DataFrame с транзакциями за указанный период.
    """
    try:
        if transactions.empty:
            views_logger.warning("Передан пустой DataFrame с транзакциями.")
            return pd.DataFrame()

        transactions = transactions.copy()
        transactions["Дата платежа_dt"] = pd.to_datetime(transactions["Дата платежа"], dayfirst=True, errors="coerce")
        transactions = transactions.dropna(subset=["Дата платежа_dt"])
        transactions = transactions[
            (transactions["Дата платежа_dt"] >= start) & (transactions["Дата платежа_dt"] <= end)
        ]
        transactions["Номер карты"] = transactions["Номер карты"].fillna("Нет информации о карте")
        return transactions
    except KeyError as e:
        views_logger.error(f"Ошибка: отсутствует столбец {e}")
    except ValueError as e:
        views_logger.error(f"Ошибка обработки даты: {e}")
    return pd.DataFrame()


def get_transaction_exchange(transactions: pd.DataFrame) -> pd.DataFrame:
    """
    Конвертирует суммы платежей в рубли по текущему курсу валют.

    :param transactions: DataFrame с транзакциями.
    :return: DataFrame с добавленным столбцом конвертированной суммы платежа.
    """
    try:
        if transactions.empty:
            views_logger.warning("Передан пустой DataFrame для конвертации.")
            return transactions

        currencies = transactions["Валюта платежа"].unique()
        currency_map = {currency: get_currency_rate(currency) if currency != "RUB" else 1 for currency in currencies}

        transactions = transactions.copy()
        transactions["exchange_rate"] = transactions["Валюта платежа"].map(currency_map)
        transactions["Сумма платежа_ex"] = transactions["Сумма платежа"] / transactions["exchange_rate"]
        return transactions
    except KeyError:
        views_logger.error("Ошибка: отсутствует столбец 'Валюта платежа' или 'Сумма платежа'.")
    return transactions


def get_card_sum_cashback(transactions: pd.DataFrame, card_number: Optional[str]) -> (float, float):
    """
    Вычисляет сумму расходов и начисленный кэшбэк по указанной карте или по всем картам.

    :param transactions: DataFrame с транзакциями.
    :param card_number: Номер карты (если None, рассчитывается по всем картам).
    :return: Кортеж (сумма расходов, начисленный кэшбэк).
    """
    try:
        if transactions.empty:
            return 0.0, 0.0

        if card_number:
            transactions = transactions[transactions["Номер карты"] == card_number]

        transactions_sum = round(transactions["Сумма платежа_ex"].sum(), 2)
        transactions_cashback = round(transactions_sum / 100, 2)
        return float(transactions_sum), float(transactions_cashback)
    except KeyError:
        views_logger.error("Ошибка: отсутствует столбец 'Номер карты' или 'Сумма платежа_ex'.")
    return 0.0, 0.0


def get_cards_info(transactions: pd.DataFrame) -> List[Dict[Hashable, Any]]:
    """
    Собирает информацию по картам: сумма расходов и начисленный кэшбэк.

    :param transactions: DataFrame с транзакциями.
    :return: Список словарей с данными по картам.
    """
    try:
        if transactions.empty:
            return []

        cards_info = []
        cards_numbers = transactions["Номер карты"].dropna().unique()
        for card_number in cards_numbers:
            last_digits = get_card_number(card_number)
            total_spent, cashback = get_card_sum_cashback(transactions, card_number)
            cards_info.append({"last_digits": last_digits, "total_spent": total_spent, "cashback": cashback})
        return cards_info
    except KeyError:
        views_logger.error("Ошибка: отсутствует столбец 'Номер карты'.")
    return []


def get_top_5_transactions(transactions: pd.DataFrame) -> List[Dict[Hashable, Any]]:
    """
    Получает топ-5 самых крупных расходов.

    :param transactions: DataFrame с транзакциями.
    :return: Список словарей с данными по 5 самым крупным расходам.
    """
    try:
        if transactions.empty:
            return []

        transaction_cols = ["Дата платежа", "Сумма платежа_ex", "Категория", "Описание"]
        transaction_cols_json = ["date", "amount", "category", "description"]
        transaction_cols_map = dict(zip(transaction_cols, transaction_cols_json))

        top_transactions = transactions.sort_values(by="Сумма платежа_ex", ascending=False).head(5)
        top_transactions = top_transactions[transaction_cols].rename(columns=transaction_cols_map)

        return top_transactions.to_dict(orient="records")
    except KeyError as e:
        views_logger.error(f"Ошибка: отсутствует столбец {e}")
    except ValueError as e:
        views_logger.error(f"Ошибка обработки данных: {e}")
    return []


def get_category_amount(transactions: pd.DataFrame, income: bool) -> List[Dict[Hashable, Any]]:
    """
    Анализирует транзакции и вычисляет суммы по категориям, выделяя топ-7 категорий
    и объединяя остальные в категорию "Остальное".

    :param income: True, если потупления, False - расходы
    :param transactions: DataFrame с транзакциями, содержащий столбцы 'Категория' и 'Сумма платежа_ex'.
    :return: Список с одним словарем, содержащим суммы по топ-7 категориям и категории "Остальное".
    """
    try:
        if transactions.empty:
            views_logger.warning("Передан пустой DataFrame с транзакциями.")
            return [{}]

        # Группируем данные по категориям и сортируем по убыванию суммы платежей
        transactions_grouped = transactions.groupby("Категория", as_index=False)["Сумма платежа_ex"].sum()
        transactions_grouped = transactions_grouped.sort_values(by="Сумма платежа_ex", ascending=False)

        if income:
            top_categories_dict = round(transactions_grouped.set_index("Категория")["Сумма платежа_ex"], 2).to_dict()
            return top_categories_dict

        # Определяем количество доступных категорий (не больше 7)
        num_top_categories = min(len(transactions_grouped), 7)
        most_amounted = transactions_grouped.head(num_top_categories)["Категория"].tolist()

        # Добавляем новую колонку, группируя остальные категории под "Остальное"
        transactions_grouped["category_cropped"] = transactions_grouped["Категория"].apply(
            lambda x: x if x in most_amounted else "Остальное"
        )

        # Формируем словарь для топовых категорий
        top_categories = transactions_grouped[transactions_grouped["category_cropped"] != "Остальное"]
        top_categories_dict = round(top_categories.set_index("category_cropped")["Сумма платежа_ex"], 2).to_dict()

        # Считаем сумму для категории "Остальное", если она есть
        rest_sum = transactions_grouped.loc[
            transactions_grouped["category_cropped"] == "Остальное", "Сумма платежа_ex"
        ].sum()
        if rest_sum > 0:
            top_categories_dict["Остальное"] = round(float(rest_sum), 2)

        return [top_categories_dict]

    except KeyError as e:
        views_logger.error(f"Ошибка: отсутствует необходимый столбец в DataFrame - {e}")
    except Exception as e:
        views_logger.error(f"Непредвиденная ошибка в get_category_amount: {e}")

    return [{}]


def get_transfers_and_cash(transactions: pd.DataFrame) -> List[Dict[Hashable, Any]]:
    """
    Фильтрует транзакции по категориям "Переводы" и "Наличные",
    группирует их и вычисляет сумму платежей в каждой категории.

    :param transactions: DataFrame с транзакциями
    :return: Список из одного словаря с суммами платежей по выбранным категориям
    """
    try:
        if transactions.empty:
            views_logger.warning("Передан пустой DataFrame с транзакциями.")
            return [{}]
        filtered_transactions = transactions[transactions["Категория"].isin(["Переводы", "Наличные"])]
        if filtered_transactions.empty:
            views_logger.info("Нет транзакций с категориями 'Переводы' или 'Наличные'.")
            return [{}]
        grouped_transactions = (
            filtered_transactions.groupby("Категория")["Сумма платежа_ex"].sum().round(2).sort_values(ascending=False)
        )
        return [grouped_transactions.to_dict()]

    except KeyError as e:
        views_logger.error(f"Ошибка: отсутствует ожидаемый ключ в DataFrame - {e}")
    except Exception as e:
        views_logger.exception(f"Неожиданная ошибка в get_transfers_and_cash: {e}")

    return [{}]


# if __name__ == "__main__":
#     transactions = read_file("operations.xlsx")
#     transactions["Сумма платежа_ex"] = abs(transactions["Сумма платежа"])
#     print(get_transfers_and_cash(transactions))
