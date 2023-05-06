import flip_sign.helpers
import datetime as dt
import pytest
from unittest.mock import patch, MagicMock
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())

fake_now = dt.datetime(year=2022, month=1, day=29, hour=10, minute=30).replace(tzinfo=LOCAL_TIMEZONE)

# write tests for helper add_years
def test_time_addition_helpers():
    # simple case
    start_date = dt.datetime(year=2020, month=1, day=30).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.add_months(start_date, 2) == \
        dt.datetime(year=2020, month=3, day=30).replace(tzinfo=LOCAL_TIMEZONE)

    # leap year case
    start_date = dt.datetime(year=2020, month=1, day=30).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.add_months(start_date, 1) == \
        dt.datetime(year=2020, month=2, day=29).replace(tzinfo=LOCAL_TIMEZONE)

    # every year august -> november case
    start_date = dt.datetime(year=2020, month=8, day=31).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.add_months(start_date, 3) == \
        dt.datetime(year=2020, month=11, day=30).replace(tzinfo=LOCAL_TIMEZONE)

    # simple add years
    start_date = dt.datetime(year=2020, month=6, day=29).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.add_years(start_date, 1) == \
        dt.datetime(year=2021, month=6, day=29).replace(tzinfo=LOCAL_TIMEZONE)

    # leap year add years
    start_date = dt.datetime(year=2020, month=2, day=29).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.add_years(start_date, 1) == \
        dt.datetime(year=2021, month=2, day=28).replace(tzinfo=LOCAL_TIMEZONE)


@patch(f'{flip_sign.helpers.__name__}.dt', wraps=dt)
def test_simple_time_deltas(mock_datetime):
    mock_datetime.datetime.now.return_value = fake_now
    # test a non-all-day event in the near future
    test_date_01 = dt.datetime(year=2022, month=1, day=30, hour=13, minute=10).replace(tzinfo=LOCAL_TIMEZONE)
    time_delta_01 = dt.timedelta(hours=5)
    assert flip_sign.helpers.countdown_format(test_date_01,
                                              test_date_01 + time_delta_01,
                                              all_day=False) == ('1d ', '2h ')

    # test an all-day event in the near future
    time_delta_02 = dt.timedelta(days=1)
    assert flip_sign.helpers.countdown_format(test_date_01,
                                              test_date_01 + time_delta_02,
                                              all_day=True) == ('1d ', '   ')

    # test an all-day event in the mid-future
    test_date_02 = dt.datetime(year=2022, month=2, day=15).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.countdown_format(test_date_02,
                                              test_date_02 + time_delta_02,
                                              all_day=True) == ('2wk', '3d ')

    # test a non-all-day event happening now
    test_date_03 = fake_now - dt.timedelta(hours=2)
    assert flip_sign.helpers.countdown_format(test_date_03,
                                              test_date_03 + time_delta_01,
                                              all_day=False) == ('Now', '   ')

    # test an all-day event happening now
    test_date_04 = fake_now.replace(hour=00, minute=00)
    assert flip_sign.helpers.countdown_format(test_date_04,
                                              test_date_04 + dt.timedelta(days=1),
                                              all_day=True) == ('Now', '   ')

    # test a non-all-day event in the near future
    test_date_05 = dt.datetime(year=2022, month=1, day=29, hour=21, minute=13).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.countdown_format(test_date_05,
                                              test_date_05 + time_delta_01,
                                              all_day=False) == ('10h', '43m')

    # test an all-day event using the concept of months
    test_date_06 = dt.datetime(year=2022, month=12, day=2).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.countdown_format(test_date_06,
                                              test_date_06 + time_delta_02,
                                              all_day=True) == ('10M', '3d ')


@patch(f'{flip_sign.helpers.__name__}.dt', wraps=dt)
def test_human_feel_time_deltas(mock_datetime):
    mock_datetime.datetime.now.return_value = fake_now
    # use idea of months in common parlance (july 5 is one month after june 5)
    test_date_01b = dt.datetime(year=2022, month=4, day=30).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.countdown_format(test_date_01b,
                                              test_date_01b + dt.timedelta(days=1),
                                              all_day=True) == ('3mo', '1d ')

    # skip reporting weeks if countdown time is longer than one month
    test_date_02b = dt.datetime(year=2022, month=4, day=25).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.countdown_format(test_date_02b,
                                              test_date_02b + dt.timedelta(days=1),
                                              all_day=True) == ('2mo', '27d')


@patch(f'{flip_sign.helpers.__name__}.dt', wraps=dt)
def test_tricky_time_deltas(mock_datetime):
    mock_datetime.datetime.now.return_value = fake_now
    # how to handle days which don't exist in the appropriate target month?
    # 1 month after january 29th is the last day of february (in this case the 28th)
    # as a result, March 5th is 1 month and 5 days after January 29th.
    test_date_01c = dt.datetime(year=2022, month=3, day=5).replace(tzinfo=LOCAL_TIMEZONE)
    assert flip_sign.helpers.countdown_format(test_date_01c,
                                              test_date_01c + dt.timedelta(days=1),
                                              all_day=True) == ('1mo', '5d ')

    # test skipping insignificant time deltas (e.g. no reporting 9 months and 15 seconds)
    test_date_02c = (dt.datetime(year=2022, month=10, day=29, hour=10, minute=30, second=15)
                     .replace(tzinfo=LOCAL_TIMEZONE))
    assert flip_sign.helpers.countdown_format(test_date_02c, test_date_02c + dt.timedelta(hours=1), all_day=False)


@patch(f'{flip_sign.helpers.__name__}.dt', wraps=dt)
def test_time_delta_errors(mock_datetime):
    mock_datetime.datetime.now.return_value = fake_now
    # end time before start time
    test_date_01d = dt.datetime(year=2022, month=2, day=15).replace(tzinfo=LOCAL_TIMEZONE)
    with pytest.raises(ValueError) as e_info:
        flip_sign.helpers.countdown_format(test_date_01d,
                                           test_date_01d + dt.timedelta(days=-10),
                                           all_day=True)

    # test providing a time which is further in the future than allowed
    test_date_02d = dt.datetime(year=2045, month=2, day=15).replace(tzinfo=LOCAL_TIMEZONE)
    with pytest.raises(ValueError) as e_info:
        flip_sign.helpers.countdown_format(test_date_02d,
                                           test_date_02d + dt.timedelta(days=15),
                                           all_day=True)

    # test event in the past
    test_date_03d = dt.datetime(year=1999, month=12, day=31).replace(tzinfo=LOCAL_TIMEZONE)
    with pytest.raises(ValueError) as e_info:
        flip_sign.helpers.countdown_format(test_date_03d,
                                           test_date_03d + dt.timedelta(days=15),
                                           all_day=True)