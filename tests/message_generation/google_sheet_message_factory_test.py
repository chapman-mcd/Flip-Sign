import flip_sign.message_generation as msg_gen
from flip_sign.variable_date_functions import mlk_day
from tests.helpers.draw_text_test import image_equal
from flip_sign.assets import root_dir
from unittest.mock import patch
from googleapiclient.errors import HttpError
import json
from collections import namedtuple

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


def assert_fixed_date_message_equal(first_message: msg_gen.RecurringFixedDateMessage,
                                    second_message: msg_gen.RecurringFixedDateMessage):
    """
    Asserts that two RecurringFixedDateMessage objects are equal, for the purposes of unit testing.

    :param first_message: (RecurringFixedDateMessage) the left message
    :param second_message: (RecurringFixedDateMessage) the right message
    :return: None
    """

    assert first_message.description == second_message.description
    assert first_message.base_start == second_message.base_start
    assert first_message.base_end == second_message.base_end
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


def assert_google_drive_image_message_factory_equal(first_factory: msg_gen.GoogleDriveImageMessageFactory,
                                                    second_factory: msg_gen.GoogleDriveImageMessageFactory):
    """
    Asserts that two GoogleDriveImageMessageFactory objects are equal, for the purposes of unit testing.

    :param first_factory: (GoogleDriveImageMessageFactory) the left factory
    :param second_factory: (GoogleDriveImageMessageFactory) the right factory
    :return: None
    """

    assert first_factory.drive_folder == second_factory.drive_folder


def assert_date_match_text_message_equal(first_message: msg_gen.DateMatchTextMessage,
                                         second_message: msg_gen.DateMatchTextMessage):
    """
    Asserts that two DateMatchTextMessage objects are equal, for the purposes of unit testing.

    :param first_message: (DateMatchTextMessage) the left message
    :param second_message: (DateMatchTextMessage) the right message
    :return: None
    """

    assert first_message.text == second_message.text


def assert_image_message_equal(first_message: msg_gen.ImageMessage, second_message: msg_gen.ImageMessage):
    """
    Asserts that two ImageMessage objects are equal, for the purposes of unit testing.

    :param first_message: (ImageMessage) the left message
    :param second_message: (ImageMessage) the right message
    :return: None
    """

    assert image_equal(first_message.get_image(), second_message.get_image())


def assert_ephemeral_date_message_equal(first_message: msg_gen.EphemeralDateMessage,
                                        second_message: msg_gen.EphemeralDateMessage):
    """
    Asserts that two EphemeralDateMessage objects are equal, for the purposes of unit testing.

    :param first_message: (EphemeralDateMessage) the left message
    :param second_message: (EphemeralDateMessage) the right message
    :return: None
    """

    assert first_message.description == second_message.description
    assert first_message.start == second_message.start
    assert first_message.end == second_message.end
    assert first_message.all_day == second_message.all_day


def assert_accuweather_dashboard_equal(first_message: msg_gen.AccuweatherDashboard,
                                       second_message: msg_gen.AccuweatherDashboard):
    """
    Asserts that two AccuweatherDashboard message objects are equal, for the purposes of unit testing.

    :param first_message: (AccuweatherDashboard) the left message
    :param second_message: (AccuweatherDashboard) the right message
    :return: None
    """

    assert first_message.location == second_message.location
    assert first_message.description == second_message.description
    assert first_message.start_date == second_message.start_date
    assert first_message.language == second_message.language


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
    elif isinstance(first_object, msg_gen.RecurringFixedDateMessage):
        assert_func = assert_fixed_date_message_equal
    elif isinstance(first_object, msg_gen.DateMatchTextMessage):
        assert_func = assert_date_match_text_message_equal
    elif isinstance(first_object, msg_gen.GoogleDriveImageMessageFactory):
        assert_func = assert_google_drive_image_message_factory_equal
    elif isinstance(first_object, msg_gen.ImageMessage):
        assert_func = assert_image_message_equal
    elif isinstance(first_object, msg_gen.EphemeralDateMessage):
        assert_func = assert_ephemeral_date_message_equal
    elif isinstance(first_object, msg_gen.AccuweatherDashboard):
        assert_func = assert_accuweather_dashboard_equal
    else:
        raise ValueError("Unsupported type: " + str(type(first_object)))

    assert_func(first_object, second_object)


def test_google_sheet_message_factory():
    with open(root_dir + "/../tests/message_generation/test_assets/google_sheet_responses.json", 'r') as f:
        results = json.load(f)

    with patch('flip_sign.message_generation.build') as build_mock:
        build_mock.return_value.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = \
            results

        factory = msg_gen.GoogleSheetMessageFactory(sheet_id="blurgh")

        outputs = factory.generate_messages()

        assert len(outputs) == len(answers)

        for answer, output in zip(answers, outputs):
            assert_message_gen_objects_equal(answer, output)

        assert not outputs[3]  # confirm display=False for the message with bad function


harder_test_answers = [
    msg_gen.BasicTextMessage(text='Test other\\nkwargs', wrap_text=False),
    msg_gen.BasicTextMessage(text="Test No First Argument"),
    msg_gen.GoogleDriveImageMessageFactory(drive_folder="fhqwhgads in parents"),
    msg_gen.RecurringFixedDateMessage(description='Christmas', base_date_start='1999-12-25'),
    msg_gen.DateMatchTextMessage(text="This is Date-Match")
]


def test_harder_google_sheet_message_factory():
    with open(root_dir + "/../tests/message_generation/test_assets/google_sheet_responses_harder.json", 'r') as f:
        results = json.load(f)

    with patch('flip_sign.message_generation.build') as build_mock:
        build_mock.return_value.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = \
            results

        factory = msg_gen.GoogleSheetMessageFactory(sheet_id="blurgh")

        outputs = factory.generate_messages()

        assert len(outputs) == len(harder_test_answers)

        for answer, output in zip(harder_test_answers, outputs):
            assert_message_gen_objects_equal(answer, output)


# returns HttpError when sheet is not found
def test_sheet_not_found():
    with patch('flip_sign.message_generation.build') as build_mock:
        response_type = namedtuple(typename="response", field_names=['status', 'reason'])
        response = response_type(status=1999, reason="Somebody set us up the bomb.")

        build_mock.return_value.spreadsheets.return_value.values.return_value.get.return_value.execute.side_effect =\
            HttpError(resp=response, content=b'blurgh')

        factory = msg_gen.GoogleSheetMessageFactory(sheet_id="blurgh")

        outputs = factory.generate_messages()

        assert len(outputs) == 1

        error_text = "Error generating messages from google sheet.  Sheet id: " + "blurgh"

        assert_message_gen_objects_equal(outputs[0], msg_gen.BasicTextMessage(error_text))