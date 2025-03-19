from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from src.utils import get_date_interval, get_date_interval_events, get_greeting, read_file


@patch("src.utils.pd.read_excel")
def test_read_file(mock_pd, transactions):
    mock_pd.return_value = pd.DataFrame(transactions)
    result = read_file(filename="transactions_dummy.xlsx")
    assert len(result) == 5


def test_read_file_filenotfound_error():
    result = read_file(filename="transactions_not_found.xlsx")
    expected_value = pd.DataFrame()
    pd.testing.assert_frame_equal(result, expected_value)


@patch("src.utils.pd.read_excel", side_effect=TypeError)
def test_read_file_type_error(mock_pd):
    result = read_file(filename="transactions_type_error.xlsx")
    pd.testing.assert_frame_equal(result, pd.DataFrame())


def test_get_date_interval_success():
    input_date = "2021-03-15 17:05:00"
    result = get_date_interval(input_date)
    expected_result = (
        datetime.strptime("2021-03-01 17:05:00", "%Y-%m-%d %H:%M:%S"),
        datetime.strptime("2021-03-15 17:05:00", "%Y-%m-%d %H:%M:%S"),
    )
    assert result == expected_result


def test_get_date_interval_error(get_date_interval_fixture):
    input_date, exp_info = get_date_interval_fixture
    with pytest.raises(ValueError, match=exp_info):
        get_date_interval(input_date)


def test_get_date_interval_events(get_date_interval_events_fixture_pos):
    input_date, date_interval, expected_result = get_date_interval_events_fixture_pos
    result = get_date_interval_events(input_date, date_interval)
    assert result == expected_result


def test_get_date_interval_events_error(get_date_interval_events_fixture):
    input_date, input_interval, exp_info = get_date_interval_events_fixture
    with pytest.raises(ValueError, match=exp_info):
        get_date_interval_events(input_date, input_interval)


@patch("src.utils.datetime")
def test_greeting(mocked_hour, get_greeting_fixture):
    mocked_hour.now.return_value.hour, expected_result = get_greeting_fixture
    result = get_greeting()
    assert result == expected_result
