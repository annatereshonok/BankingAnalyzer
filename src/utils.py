import os
from datetime import date, datetime, timedelta
from typing import Tuple

import pandas as pd

from src.logging_config import utils_logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = "data"


def read_file(filename: str) -> pd.DataFrame:
    """
    Читает файл Excel и загружает данные в DataFrame.

    :param filename: Имя файла, который нужно прочитать.
    :return: DataFrame с данными из файла или пустой DataFrame в случае ошибки.
    :raises FileNotFoundError: Если файл не найден.
    :raises ValueError: Если файл пуст или содержит некорректные данные.
    """
    try:
        filepath = os.path.join(BASE_DIR, DATA_FOLDER, filename)
        transactions = pd.read_excel(filepath)
        if transactions.empty:
            utils_logger.error(f"Файл {filename} c транзакциями пуст.")
            return pd.DataFrame()
        return transactions
    except FileNotFoundError:
        utils_logger.error(f"Файл {filename} не найден.")
        return pd.DataFrame()
    except (TypeError, ValueError, pd.errors.ParserError) as e:
        utils_logger.error(f"Ошибка обработки данных в файле {filename}: {e}")
        return pd.DataFrame()
    return pd.DataFrame()


def get_greeting() -> str:
    """
    Возвращает приветствие в зависимости от текущего времени суток.

    :return: Строка с приветствием ("Доброе утро", "Добрый день", "Добрый вечер", "Доброй ночи").
    """
    hour = datetime.now().hour
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_date_interval(input_date: str) -> Tuple[date, date]:
    """
    Возвращает кортеж с первой датой текущего месяца и сегодняшней датой.

    :return: Кортеж (дата первого дня месяца, сегодняшняя дата).
    """
    if not isinstance(input_date, str):
        raise ValueError("Дата должна быть строкой")
    if not input_date.strip():
        raise ValueError("Дата не может быть пустой")

    try:
        end = datetime.strptime(input_date, "%Y-%m-%d %H:%M:%S")
        start = end.replace(day=1)
    except ValueError:
        raise ValueError("Некорректный формат даты")
    return start, end


def get_date_interval_events(input_date: str, range_type: str = "M") -> Tuple[datetime, datetime]:
    """
    Возвращает начальную и конечную дату в зависимости от заданного диапазона.

    :param input_date: Дата в формате "%Y-%m-%d %H:%M:%S"
    :param range_type: Диапазон (W - неделя, M - месяц, Y - год, ALL - всё до указанной даты)
    :return: Кортеж (start_date, end_date)
    """
    if not isinstance(input_date, str):
        raise ValueError("Дата должна быть строкой")
    if not input_date.strip():
        raise ValueError("Дата не может быть пустой")

    try:
        end_date = datetime.strptime(input_date, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError("Некорректный формат даты")

    if range_type == "W":
        start_date = end_date - timedelta(days=end_date.weekday())
    elif range_type == "M":
        start_date = end_date.replace(day=1)
    elif range_type == "Y":
        start_date = end_date.replace(month=1, day=1)
    elif range_type == "ALL":
        start_date = datetime.min
    else:
        raise ValueError("Некорректный диапазон. Используйте W, M, Y или ALL.")

    return start_date, end_date
