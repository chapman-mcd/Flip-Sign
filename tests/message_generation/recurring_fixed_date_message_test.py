from flip_sign.message_generation import RecurringFixedDateMessage, linear_decline_frequency_date_message
import flip_sign.helpers
from PIL import Image
from unittest.mock import patch
from tests.helpers.draw_text_test import image_equal
import datetime
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())


@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_how_long_till_christmas(message_gen_datetime, helpers_datetime):
    # test christmas in 2 days
    with Image.open('./message_generation/test_assets/Test_Recurring_01.png') as answer:
        out_path = './message_generation/test_output/Test_Recurring_01.png'
        fake_now = datetime.datetime(year=1999, month=12, day=23, hour=18, minute=15)
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        christmas_start = datetime.datetime(year=2001, month=12, day=25).replace(tzinfo=LOCAL_TIMEZONE)
        test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start=christmas_start,
                                             base_date_end=christmas_start, all_day=True, frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test it's christmas
    with Image.open('./message_generation/test_assets/Test_Recurring_02.png') as answer:
        out_path = './message_generation/test_output/Test_Recurring_02.png'
        fake_now = datetime.datetime(year=1999, month=12, day=25, hour=18, minute=15)
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        christmas_start = datetime.datetime(year=2001, month=12, day=25).replace(tzinfo=LOCAL_TIMEZONE)
        test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start=christmas_start,
                                             base_date_end=christmas_start, all_day=True, frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test a long time until christmas
    with Image.open('./message_generation/test_assets/Test_Recurring_03.png') as answer:
        out_path = './message_generation/test_output/Test_Recurring_03.png'
        fake_now = datetime.datetime(year=1999, month=12, day=27, hour=18, minute=15)
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        christmas_start = datetime.datetime(year=2001, month=12, day=25).replace(tzinfo=LOCAL_TIMEZONE)
        test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start=christmas_start,
                                             base_date_end=christmas_start, all_day=True, frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)


@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_new_defaults(message_gen_datetime, helpers_datetime):
    # test christmas in 2 days
    with Image.open('./message_generation/test_assets/Test_Recurring_01.png') as answer:
        out_path = './message_generation/test_output/Test_Recurring_01.png'
        fake_now = datetime.datetime(year=1999, month=12, day=23, hour=18, minute=15)
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        christmas_start = datetime.datetime(year=2001, month=12, day=25).replace(tzinfo=LOCAL_TIMEZONE)
        test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start=christmas_start, frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)



@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_provide_christmas_as_date_string(message_gen_datetime, helpers_datetime):
    # test christmas in 2 days
    fake_now = datetime.datetime(year=1999, month=12, day=23, hour=18, minute=15)
    helpers_datetime.datetime.now.return_value = fake_now
    message_gen_datetime.datetime.now.return_value = fake_now
    test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start="1999-12-25")
    assert test_msg.base_start == datetime.datetime(1999, 12, 25).replace(tzinfo=LOCAL_TIMEZONE)
    assert test_msg


@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_provide_christmas_as_datetime_string(message_gen_datetime, helpers_datetime):
    # test a long time until christmas
    with Image.open('./message_generation/test_assets/Test_Recurring_03.png') as answer:
        out_path = './message_generation/test_output/Test_Recurring_03.png'
        fake_now = datetime.datetime(year=1999, month=12, day=27, hour=18, minute=15)
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start="1999-12-25T11:35:57-08:00",
                                             frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)


@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_bad_datetime_string(message_gen_datetime, helpers_datetime):
    # test bad datetime string
    fake_now = datetime.datetime(year=1999, month=12, day=27, hour=18, minute=15)
    helpers_datetime.datetime.now.return_value = fake_now
    message_gen_datetime.datetime.now.return_value = fake_now
    test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start="lol ISO8601",
                                         frequency=1.0)
    assert not test_msg
    assert test_msg.init_failure


def test_string_representation():
    test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start="1999-12-25")

    assert str(test_msg) == "RecurringFixedDateMessage: description=Christmas, base_date_start=1999-12-25"

    christmas_start = datetime.datetime(year=2001, month=12, day=25).replace(tzinfo=LOCAL_TIMEZONE)
    test_msg = RecurringFixedDateMessage(description="Christmas", base_date_start=christmas_start, frequency=1.0)

    assert str(test_msg) == "RecurringFixedDateMessage: description=Christmas, base_date_start=" + str(christmas_start)
