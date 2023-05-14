import flip_sign.variable_date_functions as vdf
from unittest.mock import patch
import datetime
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_mothers_day(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)
    answer = (datetime.datetime(2023, 5, 14, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 5, 14, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mothers_day() == answer

    # 2023 - mothers day right now
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 5, 14, 10, 35)
    answer = (datetime.datetime(2023, 5, 14, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 5, 14, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mothers_day() == answer

    # 2023 - after mothers day
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 10, 1)

    answer = (datetime.datetime(2024, 5, 12, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 5, 12, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mothers_day() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 5, 12, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 5, 12, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mothers_day() == answer

    # 2025
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 5, 11, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 5, 11, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mothers_day() == answer


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_thanksgiving(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)
    answer = (datetime.datetime(2023, 11, 23, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 11, 23, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.thanksgiving() == answer

    # 2023 after thanksgiving
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 12, 5)

    answer = (datetime.datetime(2024, 11, 28, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 11, 28, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.thanksgiving() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 11, 28, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 11, 28, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.thanksgiving() == answer

    # 2025
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 11, 27, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 11, 27, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.thanksgiving() == answer


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_carnaval(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)

    answer = (datetime.datetime(2023, 2, 21, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 2, 21, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.carnaval() == answer

    # 2023 after carnaval
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 6, 15)

    answer = (datetime.datetime(2024, 2, 13, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 2, 13, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.carnaval() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 2, 13, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 2, 13, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.carnaval() == answer

    # 2025
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 3, 4, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 3, 4, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.carnaval() == answer


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_fathers_day(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)

    answer = (datetime.datetime(2023, 6, 18, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 6, 18, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.fathers_day() == answer

    # 2023 after fathers day
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 10, 31)

    answer = (datetime.datetime(2024, 6, 16, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 6, 16, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.fathers_day() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 6, 16, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 6, 16, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.fathers_day() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 6, 15, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 6, 15, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.fathers_day() == answer


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_labor_day(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)

    answer = (datetime.datetime(2023, 9, 4, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 9, 4, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.labor_day() == answer

    # 2023 after labor day
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 12, 1)

    answer = (datetime.datetime(2024, 9, 2, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 9, 2, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.labor_day() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 9, 2, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 9, 2, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.labor_day() == answer

    # 2025
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 9, 1, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 9, 1, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.labor_day() == answer


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_memorial_day(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)

    answer = (datetime.datetime(2023, 5, 29, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 5, 29, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.memorial_day() == answer

    # 2023 after memorial day
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 9, 1)

    answer = (datetime.datetime(2024, 5, 27, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 5, 27, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.memorial_day() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 5, 27, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 5, 27, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.memorial_day() == answer

    # 2025
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 5, 26, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 5, 26, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.memorial_day() == answer


@patch(f'{vdf.__name__}.datetime', wraps=datetime)
def test_mlk_day(mock_datetime):
    # 2023
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 1, 1)

    answer = (datetime.datetime(2023, 1, 16, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2023, 1, 16, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mlk_day() == answer

    # 2023 after MLK day
    mock_datetime.datetime.now.return_value = datetime.datetime(2023, 7, 4)

    answer = (datetime.datetime(2024, 1, 15, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 1, 15, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mlk_day() == answer

    # 2024
    mock_datetime.datetime.now.return_value = datetime.datetime(2024, 1, 1)

    answer = (datetime.datetime(2024, 1, 15, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2024, 1, 15, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mlk_day() == answer

    # 2025
    mock_datetime.datetime.now.return_value = datetime.datetime(2025, 1, 1)

    answer = (datetime.datetime(2025, 1, 20, tzinfo=LOCAL_TIMEZONE),
              datetime.datetime(2025, 1, 20, 23, 59, tzinfo=LOCAL_TIMEZONE))

    assert vdf.mlk_day() == answer
