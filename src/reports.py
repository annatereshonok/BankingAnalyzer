import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

import pandas as pd

from src.logging_config import reports_logger

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_reports")
os.makedirs(LOG_DIR, exist_ok=True)


def save_report(file_name: Optional[str] = None):
    """Создайте декоратор для функций-отчетов, который записывает в файл результат,
    который возвращает функция, формирующая отчет.

    :params file_name: Название файла.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            report_file = file_name or f"report_{datetime.today().strftime('%Y-%m-%d')}.json"
            report_file = os.path.join(LOG_DIR, report_file)
            result.to_json(report_file, orient="records", force_ascii=False, indent=4)

            reports_logger.info(f"Отчёт сохранён в файл: {report_file}")
            return result

        return wrapper

    return decorator if file_name is None else decorator(file_name)


@save_report()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Возвращает DataFrame с тратами по категории за последние 3 месяца.

    :param transactions: DataFrame с данными о транзакциях.
    :param category: Интересующая категория.
    :param date: Дата в формате "%Y-%m-%d".
    :return: Отфильтрованный DataFrame с транзакциями за указанный период.
    """
    if date is None:
        date = datetime.today().strftime("%Y-%m-%d")

    try:
        date = datetime.strptime(date, "%Y-%m-%d")
        three_months_ago = date - timedelta(days=90)
        try:
            transactions["Дата платежа_dt"] = pd.to_datetime(
                transactions["Дата платежа"], dayfirst=True, errors="coerce"
            )
            filtered_transactions = transactions[
                (transactions["Дата платежа_dt"] >= three_months_ago) & (transactions["Категория"] == category)
            ]
            filtered_transactions = filtered_transactions.drop("Дата платежа_dt", axis=1)
            return filtered_transactions
        except KeyError:
            reports_logger.error("Ошибка: отсутствует столбец 'Дата платежа' или 'Категория.")
    except ValueError:
        reports_logger.error(f"Неправильный формат даты {date}")

    return pd.DataFrame()
