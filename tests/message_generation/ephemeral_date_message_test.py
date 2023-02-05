# this set of tests also carries the tests for the base DateMessage subclass, since it is not feasible to test directly
from flip_sign.message_generation import EphemeralDateMessage, linear_decline_frequency_date_message
import flip_sign.helpers
from PIL import Image
from unittest.mock import patch
from tests.helpers.draw_text_test import image_equal
import datetime


def test_bad_frequency(caplog):
    dt_now = datetime.datetime.now()
    interval = datetime.timedelta(hours=3)
    test = EphemeralDateMessage(description="Blurgh", start=dt_now - interval, end=dt_now + interval,
                                all_day=False, frequency=None)
    assert not test
    assert caplog.records[-1].getMessage() == "Frequency must be float or callable.  Frequency:" + str(None)


def test_all_dates_in_past(caplog):
    dt_now = datetime.datetime.now()
    interval = datetime.timedelta(hours=3)
    test = EphemeralDateMessage(description="Blurgh", start=dt_now - interval*2, end=dt_now - interval,
                                all_day=False, frequency=1.0)
    assert not test
    assert caplog.records[-1].getMessage() == "EphemeralDateMessage fully in the past.  Description:" + "Blurgh"


def test_linear_decline_frequency():
    assert linear_decline_frequency_date_message(10) == 1.0

    assert linear_decline_frequency_date_message(370) == 0.1

    assert linear_decline_frequency_date_message(197) - 0.5 < 0.01


# Mirror time deltas from calendar test
fake_now = datetime.datetime(year=2022, month=1, day=29, hour=10, minute=30)


@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_date_messages(mock_datetime):
    mock_datetime.datetime.now.return_value = fake_now
    # test a non-all-day event in the near future
    with Image.open('./message_generation/test_assets/Test_01.png') as answer:
        out_path = './message_generation/test_output/Test_01.png'
        test_date_01 = datetime.datetime(year=2022, month=1, day=30, hour=13, minute=10)
        time_delta_01 = datetime.timedelta(hours=5)
        test_msg = EphemeralDateMessage(description="Trip to Uranus and Neptune", start=test_date_01,
                                        end=test_date_01 + time_delta_01, all_day=False)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test an all-day event in the mid-future
    with Image.open('./message_generation/test_assets/Test_02.png') as answer:
        out_path = './message_generation/test_output/Test_02.png'
        test_date_02 = datetime.datetime(year=2022, month=2, day=15)
        time_delta_02 = datetime.timedelta(days=1)
        test_msg = EphemeralDateMessage(description="Trip to Uranus and Neptune", start=test_date_02,
                                        end=test_date_02 + time_delta_02, all_day=True)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test a non-all-day event happening now
    with Image.open('./message_generation/test_assets/Test_03.png') as answer:
        out_path = './message_generation/test_output/Test_03.png'
        test_date_03 = fake_now - datetime.timedelta(hours=2)
        test_msg = EphemeralDateMessage(description="Trip to Uranus and Neptune", start=test_date_03,
                                        end=test_date_03 + time_delta_01, all_day=False)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)


# test various text description scenarios
# normal / short
# too long
# super-long word on first line
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_date_message_descriptions(mock_datetime):
    mock_datetime.datetime.now.return_value = fake_now
    # test a description that is too long
    with Image.open('./message_generation/test_assets/Test_04.png') as answer:
        out_path = './message_generation/test_output/Test_04.png'
        test_date_01 = datetime.datetime(year=2022, month=1, day=30, hour=13, minute=10)
        time_delta_01 = datetime.timedelta(hours=5)
        too_long_description = "This text is too long.  Like, way too long.  Way way way too long."
        test_msg = EphemeralDateMessage(description=too_long_description, start=test_date_01,
                                        end=test_date_01 + time_delta_01, all_day=False)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test a description with a really long word in it
    with Image.open('./message_generation/test_assets/Test_05.png') as answer:
        out_path = './message_generation/test_output/Test_05.png'
        long_word_description = "Mississippianish is long."
        test_msg = EphemeralDateMessage(description=long_word_description, start=test_date_01,
                                        end=test_date_01 + time_delta_01, all_day=False)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)


@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_date_message_fully_future(mock_datetime, caplog):
    mock_datetime.datetime.now.return_value = fake_now
    test_start = fake_now - datetime.timedelta(days=3)
    test_end = fake_now - datetime.timedelta(days=2)
    test_desc = "Blurgh"
    test_msg = EphemeralDateMessage(description=test_desc, start=test_start,
                                    end=test_end, all_day=False)
    assert not test_msg
    assert caplog.records[-1].getMessage() == "EphemeralDateMessage fully in the past.  Description:" + test_desc



