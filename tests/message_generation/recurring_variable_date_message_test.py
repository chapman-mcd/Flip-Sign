from flip_sign.message_generation import RecurringVariableDateMessage
from dateutil.easter import easter
import flip_sign.helpers
from PIL import Image
from unittest.mock import patch
from tests.helpers.draw_text_test import image_equal
import datetime
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())


# create test variable date function for Carnaval
def carnaval_date():
    now = datetime.datetime.now()
    this_year_end = datetime.datetime.combine(easter(now.year) - datetime.timedelta(days=46),
                                              datetime.datetime.min.time())
    if this_year_end < now:
        easter_date = datetime.datetime.combine(easter(now.year + 1) - datetime.timedelta(days=47),
                                                datetime.datetime.min.time())
    else:
        
        easter_date = this_year_end - datetime.timedelta(days=1)

    return easter_date.replace(tzinfo=LOCAL_TIMEZONE), easter_date.replace(tzinfo=LOCAL_TIMEZONE)


@patch(__name__ + '.datetime', wraps=datetime)
@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_recurring_date_carnaval(local_datetime, message_gen_datetime, helpers_datetime):
    # test 2023
    with Image.open('./message_generation/test_assets/Test_Variable_01.png') as answer:
        out_path = './message_generation/test_output/Test_Variable_01.png'
        fake_now = datetime.datetime(year=2023, month=2, day=3)
        local_datetime.datetime.now.return_value = fake_now
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        test_msg = RecurringVariableDateMessage(description="Carnaval", next_dates_func=carnaval_date,
                                                all_day=True, frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test 2024
    with Image.open('./message_generation/test_assets/Test_Variable_02.png') as answer:
        out_path = './message_generation/test_output/Test_Variable_02.png'
        fake_now = datetime.datetime(year=2023, month=3, day=10)
        local_datetime.datetime.now.return_value = fake_now
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        test_msg = RecurringVariableDateMessage(description="Carnaval", next_dates_func=carnaval_date,
                                                all_day=True, frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)


@patch(__name__ + '.datetime', wraps=datetime)
@patch(f'{flip_sign.message_generation.__name__}.datetime', wraps=datetime)
@patch(f'{flip_sign.helpers.__name__}.dt', wraps=datetime)
def test_recurring_date_bad_function(local_datetime, message_gen_datetime, helpers_datetime):
    # test not even a function
    with Image.open('./message_generation/test_assets/Test_Variable_01.png') as answer:
        out_path = './message_generation/test_output/Test_Variable_01.png'
        fake_now = datetime.datetime(year=2023, month=2, day=3)
        local_datetime.datetime.now.return_value = fake_now
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        test_msg = RecurringVariableDateMessage(description="Carnaval", next_dates_func="not_even_a_function",
                                                all_day=True)

        assert not test_msg

    # test improper function
    with Image.open('./message_generation/test_assets/Test_Variable_01.png') as answer:
        out_path = './message_generation/test_output/Test_Variable_01.png'
        fake_now = datetime.datetime(year=2023, month=2, day=3)
        local_datetime.datetime.now.return_value = fake_now
        helpers_datetime.datetime.now.return_value = fake_now
        message_gen_datetime.datetime.now.return_value = fake_now
        test_msg = RecurringVariableDateMessage(description="Carnaval", next_dates_func=lambda x: str(x),
                                                all_day=True)

        assert not test_msg
