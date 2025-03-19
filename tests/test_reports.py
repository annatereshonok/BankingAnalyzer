from unittest.mock import patch

import pandas as pd

from src.reports import spending_by_category


@patch("src.reports.reports_logger")
@patch("pandas.DataFrame.to_json")
def test_spending_by_category(mock_to_json, mock_logger, sample_transactions):
    result = spending_by_category(sample_transactions, "Еда")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2

    mock_to_json.assert_called_once()
    mock_logger.info.assert_called_once()


@patch("src.reports.reports_logger")
def test_spending_by_category_no_category(mock_logger, sample_transactions):
    result = spending_by_category(sample_transactions, "Развлечения")

    assert result.empty
    mock_logger.info.assert_called_once()


@patch("src.reports.reports_logger")
def test_spending_by_category_invalid_date(mock_logger, sample_transactions):
    result = spending_by_category(sample_transactions, "Еда", "31-02-2023")

    assert result.empty
    mock_logger.error.assert_called_once_with("Неправильный формат даты 31-02-2023")


@patch("src.reports.reports_logger")
def test_spending_by_category_missing_column(mock_logger):
    df = pd.DataFrame({"Категория": ["Еда"], "Сумма": [100]})
    result = spending_by_category(df, "Еда")

    assert result.empty
    mock_logger.error.assert_called_once_with("Ошибка: отсутствует столбец 'Дата платежа' или 'Категория.")
