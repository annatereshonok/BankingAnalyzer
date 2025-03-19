import json

from src.services import (
    best_cashback_categories,
    investment_bank,
    search_by_client_name,
    search_by_phone,
    search_by_word,
)


def test_best_cashback_valid_data(transactions_data):
    result = best_cashback_categories(transactions_data, "2024", "03")
    expected = {"Продукты": 80.0, "Транспорт": 20.0}
    assert json.loads(result) == expected


def test_best_cashback_no_matching_data(transactions_data):
    result = best_cashback_categories(transactions_data, "2023", "03")
    assert json.loads(result) == {}


def test_best_cashback_invalid_data_type():
    result = best_cashback_categories("invalid_data", "2024", "03")
    assert result == "{}"


def test_best_cashback_invalid_date_format():
    invalid_data = [{"Дата платежа": "2024-03-15", "Категория": "Продукты", "Сумма платежа": 5000}]
    result = best_cashback_categories(invalid_data, "2024", "03")
    assert json.loads(result) == {}


def test_best_cashback_missing_keys():
    invalid_data = [{"Категория": "Продукты", "Сумма платежа": 5000}]
    result = best_cashback_categories(invalid_data, "2024", "03")
    assert json.loads(result) == {}


def test_investment_bank(investment_bank_fixture):
    month, transactions, limit, expected = investment_bank_fixture
    result = investment_bank(month, transactions, limit)
    assert result == expected


def test_investment_bank_error(investment_bank_fixture_error):
    month, transactions, limit, expected = investment_bank_fixture_error
    result = investment_bank(month, transactions, limit)
    assert result == expected


def test_search_by_word(search_word_fixture):
    result = search_by_word(search_word_fixture, "метро")
    expected = '[{"Описание": "Метро Санкт-Петербург"}, {"Описание": "Метро Мск"}]'
    assert json.loads(result) == json.loads(expected)


def test_test_search_by_word_exception(search_word_fixture):
    result = search_by_word(search_word_fixture, "что-то")
    expected = "[]"
    assert json.loads(result) == json.loads(expected)


def test_search_by_phone(search_word_fixture):
    result = search_by_phone(search_word_fixture)
    expected = '[{"Описание": "Перевод +7 987 65-43-21"}]'
    assert json.loads(result) == json.loads(expected)


def test_search_by_phone_exception():
    result = search_by_phone([])
    expected = "[]"
    assert json.loads(result) == json.loads(expected)


def test_search_by_client_name(search_word_fixture):
    result = search_by_client_name(search_word_fixture)
    expected = '[{"Описание": "Оплата Василий П."}, {"Описание": "Оплата Петр В."}]'
    assert json.loads(result) == json.loads(expected)


def test_search_by_client_name_exception():
    result = search_by_client_name([])
    expected = "[]"
    assert json.loads(result) == json.loads(expected)
