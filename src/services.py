import json
import re
from datetime import datetime
from itertools import groupby
from operator import itemgetter
from typing import Any, Dict, Hashable, List

from src.logging_config import services_logger


def best_cashback_categories(data: List[Dict[Hashable, Any]], year: str, month: str) -> str:
    """
    Анализирует транзакции и определяет, сколько можно заработать кэшбэка в каждой категории за указанный месяц.

    :param data: Список транзакций.
    :param year: Год для анализа (например, "2024").
    :param month: Месяц для анализа (например, "03").
    :return: Словарь с категориями и суммой кэшбэка.
    """
    try:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise TypeError("Аргумент data должен быть списком словарей.")
        if not isinstance(year, str) or not isinstance(month, str):
            raise TypeError("Аргументы year и month должны быть строками.")

        filtered_data = [
            item
            for item in data
            if datetime.strptime(item["Дата платежа"], "%d.%m.%Y").year == int(year)
            and datetime.strptime(item["Дата платежа"], "%d.%m.%Y").month == int(month)
        ]

        cashback = map(lambda x: (x["Категория"], x["Сумма платежа"] / 100), filtered_data)
        grouped_transactions = {
            key: round(sum(v for _, v in group), 2) for key, group in groupby(sorted(cashback), key=itemgetter(0))
        }
        return json.dumps(grouped_transactions, ensure_ascii=False, indent=4)
    except KeyError as e:
        services_logger.error(f"Отсутствует необходимый ключ в данных: {e}")
    except (ValueError, TypeError) as e:
        services_logger.error(f"Ошибка при обработке даты: {e}")
    except Exception as e:
        services_logger.error(f"Неизвестная ошибка: {e}")
    return "{}"


def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
    Рассчитывает отложенную сумму по операциям в заданном месяце.

    :param month: Месяц, по которому нужно фильтровать транзакции (формат "YYYY-MM").
    :param transactions: Список транзакций.
    :param limit: Лимит, используемый для расчета отложенной суммы.
    :return: Сумма отложенных средств.
    """
    try:
        pattern = r"^\d{4}-\d{2}$"
        if (
            not isinstance(month, str)
            or not bool(re.match(pattern, month))
            or not isinstance(transactions, list)
            or not isinstance(limit, int)
        ):
            services_logger.error("Некорректные типы данных для параметров")
            return 0.0

        filtered_data = filter(
            lambda item: datetime.strptime(item.get("Дата платежа", ""), "%d.%m.%Y")
            .strftime("%Y-%m")
            .startswith(month),
            transactions,
        )

        deferred_amount = sum(
            (
                (transaction["Сумма операции"] // limit + 1) * limit - transaction["Сумма операции"]
                if transaction["Сумма операции"] % limit != 0
                else 0
            )
            for transaction in filtered_data
        )

        services_logger.info(f"Расчет завершен успешно. Отложенная сумма: {deferred_amount}")
        return round(deferred_amount, 2)

    except KeyError as e:
        services_logger.error(f"Отсутствует необходимый ключ в данных: {e}")
    except (ValueError, TypeError) as e:
        services_logger.error(f"Ошибка при обработке данных: {e}")
    except Exception as e:
        services_logger.error(f"Неизвестная ошибка: {e}")
    return 0.0


def search_by_word(transactions: List[Dict[Hashable, Any]], search_words: str) -> str:
    """
    Ищет транзакции, содержащие указанные слова в описании.

    :param transactions: список транзакуий
    :param search_words: Строка для поиска в описании транзакции.
    :return: JSON-строка с найденными транзакциями.
    """
    try:
        filtered_data = filter(
            lambda item: re.findall(search_words, item.get("Описание", ""), flags=re.I), transactions
        )
        return json.dumps(list(filtered_data), ensure_ascii=False, indent=4)
    except Exception as e:
        services_logger.error(f"Ошибка при поиске транзакций: {e}")
        return "[]"


def search_by_phone(transactions: List[Dict[Hashable, Any]]) -> str:
    """
    Ищет транзакции, содержащие телефонные номера в описании.

    :param transactions: список транзакуий
    :return: JSON-строка с найденными транзакциями.
    """
    try:
        pattern = r"\+7\s?\d{3}\s?\d{2}-\d{2}-\d{2}"
        filtered_data = filter(lambda item: re.search(pattern, item.get("Описание", "")), transactions)
        return json.dumps(list(filtered_data), ensure_ascii=False, indent=4)
    except Exception as e:
        services_logger.error(f"Ошибка при поиске номеров телефонов: {e}")
        return "[]"


def search_by_client_name(transactions: List[Dict[Hashable, Any]]) -> str:
    """
    Ищет транзакции, содержащие имя и первую букву фамилии в описании.

    :param transactions: список транзакуий
    :return: JSON-строка с найденными транзакциями.
    """
    try:
        pattern = r"\b[А-ЯЁ][а-яё]+\s[А-Я]\."
        filtered_data = filter(lambda item: re.search(pattern, item.get("Описание", "")), transactions)
        return json.dumps(list(filtered_data), ensure_ascii=False, indent=4)
    except Exception as e:
        services_logger.error(f"Ошибка при поиске имен клиентов: {e}")
        return "[]"
