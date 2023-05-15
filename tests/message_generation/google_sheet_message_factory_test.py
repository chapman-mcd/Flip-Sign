import flip_sign.message_generation as msg_gen
from flip_sign.variable_date_functions import mlk_day
from flip_sign.assets import root_dir
from unittest.mock import patch
import json

answers = [
    msg_gen.BasicTextMessage(text="Test", frequency=1.0),
    msg_gen.RecurringVariableDateMessage(description="Martin Luther King Jr Day", next_dates_func=mlk_day,
                                         all_day=True),
    msg_gen.BasicTextMessage(text="Message/Factory type not found.  Type:" + 'TotallyNotAValidMessage'),
    msg_gen.RecurringVariableDateMessage(description="Not A Valid Function",
                                         next_dates_func='totally_not_a_valid_function',
                                         all_day=True),
    msg_gen.AccuweatherAPIMessageFactory(location_description="Nameless, TN"),
    msg_gen.GoogleCalendarMessageFactory(calendar_id='calendar_id@google.com'),
    msg_gen.BasicTextMessage(text='Test other\\nkwargs', wrap_text=False)
]


def assert_accuweather_message_factory_equal(first_factory: msg_gen.AccuweatherAPIMessageFactory,
                                      second_factory: msg_gen.AccuweatherAPIMessageFactory):
    """
    Tests if two accuweather message factory objects are the same, for the purposes of unit testing.

    :param first_factory: (AccuweatherAPIMessageFactory) the left factory
    :param second_factory: (AccuweatherAPIMessageFactory) the right factory
    :return: (bool) whether the two factories are equal
    """

    assert first_factory.location_description == second_factory.location_description
    assert first_factory.headline == second_factory.headline
    assert first_factory.description == second_factory.description
    assert first_factory.weather_descriptions == second_factory.weather_descriptions
    assert first_factory.weather_dashboard == second_factory.weather_dashboard
    assert (first_factory.start_date - second_factory.start_date).total_seconds() < 1


def assert_basic_text_message_equal(first_message: msg_gen.BasicTextMessage, second_message: msg_gen.BasicTextMessage):
    """
    Asserts that two BasicTextMessage objects are equal, for the purposes of unit testing.

    :param first_message: (BasicTextMessage) the left message
    :param second_message: (BasicTextMessage) the right message
    :return: None
    """

    assert first_message.text == second_message.text
    assert first_message.font_parameters == second_message.font_parameters


def assert_variable_date_message_equal(first_message: msg_gen.RecurringVariableDateMessage,
                                       second_message: msg_gen.RecurringVariableDateMessage):
    """
    Asserts that two RecurringVariableDateMessage objects are equal, for the purposes of unit testing.

    :param first_message: (RecurringVariableDateMessage) the left message
    :param second_message: (RecurringVariableDateMessage) the right message
    :return: None
    """

    assert first_message.description == second_message.description
    assert first_message.next_dates_func == second_message.next_dates_func
    assert first_message.all_day == second_message.all_day


def assert_google_calendar_message_factory_equal(first_factory: msg_gen.GoogleCalendarMessageFactory,
                                          second_factory: msg_gen.GoogleCalendarMessageFactory):
    """
    Asserts that two GoogleCalendarMessageFactory objects are equal, for the purposes of unit testing.

    :param first_factory: (GoogleCalendarMessageFactory) the left factory
    :param second_factory: (GoogleCalendarMessageFactory) the right factor
    :return: None
    """

    assert first_factory.calendar_id == second_factory.calendar_id


def assert_message_gen_objects_equal(first_object, second_object):
    """
    Asserts that two message generation objects are equal, for the purposes of unit testing the
    GoogleSheetMessageFactory.

    :param first_object: the left object
    :param second_object: the right object
    :return: None
    """

    assert type(first_object) == type(second_object)

    if isinstance(first_object, msg_gen.GoogleCalendarMessageFactory):
        assert_func = assert_google_calendar_message_factory_equal
    elif isinstance(first_object, msg_gen.BasicTextMessage):
        assert_func = assert_basic_text_message_equal
    elif isinstance(first_object, msg_gen.RecurringVariableDateMessage):
        assert_func = assert_variable_date_message_equal
    elif isinstance(first_object, msg_gen.AccuweatherAPIMessageFactory):
        assert_func = assert_accuweather_message_factory_equal
    else:
        raise NotImplementedError

    assert_func(first_object, second_object)


with open(root_dir + "/../tests/message_generation/test_assets/google_sheet_responses.json", 'r') as f:
    results = json.load(f)


def test_google_sheet_message_factory():
    with patch('flip_sign.message_generation.build') as build_mock:
        build_mock.return_value.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = \
            results

        factory = msg_gen.GoogleSheetMessageFactory(sheet_id="blurgh")

        outputs = factory.generate_messages()

        assert len(outputs) == len(answers)

        for answer, output in zip(answers, outputs):
            assert_message_gen_objects_equal(answer, output)

        assert not outputs[3]  # confirm display=False for the message with bad function
