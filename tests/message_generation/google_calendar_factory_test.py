from flip_sign.assets import keys, root_dir
from unittest.mock import patch, MagicMock
from flip_sign.message_generation import GoogleCalendarMessageFactory, EphemeralDateMessage, \
    AccuweatherAPIMessageFactory
import datetime
import json
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())


with open(root_dir + "/../tests/message_generation/test_assets/google_calendar_responses_2.json") as f:
    results = json.load(f)

answers = [EphemeralDateMessage(description='Paris Trip (Fake)', start=(datetime.datetime(2023, 3, 7)
                                                                        .replace(tzinfo=LOCAL_TIMEZONE)),
                                end=datetime.datetime(2023, 3, 8).replace(tzinfo=LOCAL_TIMEZONE), all_day=True),
           AccuweatherAPIMessageFactory(location_description="Paris, France", start_date=datetime.date(2023, 3, 7)),
           EphemeralDateMessage(description='Chapman’s Friends Visit', start=(datetime.datetime(2023, 3, 11)
                                                                              .replace(tzinfo=LOCAL_TIMEZONE)),
                                end=(datetime.datetime(2023, 3, 17).replace(tzinfo=LOCAL_TIMEZONE)), all_day=True),
           EphemeralDateMessage(description="Luiza’s Birthday",
                                start=datetime.datetime.fromisoformat('2023-03-11T14:30:00-06:00'),
                                end=datetime.datetime.fromisoformat('2023-03-11T16:30:00-06:00'), all_day=False),
           EphemeralDateMessage(description="Tax Day", start=(datetime.datetime(2023, 4, 15)
                                                              .replace(tzinfo=LOCAL_TIMEZONE)),
                                end=(datetime.datetime(2023, 4, 15).replace(tzinfo=LOCAL_TIMEZONE)), all_day=True),
           EphemeralDateMessage(description="Pride Month", start=(datetime.datetime(2023, 6, 1)
                                                                  .replace(tzinfo=LOCAL_TIMEZONE)),
                                end=datetime.datetime(2023, 6, 30).replace(tzinfo=LOCAL_TIMEZONE), all_day=True)]


def assert_ephemeral_date_message_equal(first_message: EphemeralDateMessage, second_message: EphemeralDateMessage):
    """
    Tests if two ephemeral date message objects are the same, for the purposes of unit testing.

    :param first_message: (EphemeralDateMessage) the left message
    :param second_message: (EphemeralDateMessage) the right message
    :return: (bool) whether the two messages are equal
    """

    assert first_message.description == second_message.description
    assert (first_message.start - second_message.start).total_seconds() < 1
    assert (first_message.end - second_message.end).total_seconds() < 1
    assert first_message.all_day == second_message.all_day


def assert_accuweather_message_factory_equal(first_factory: AccuweatherAPIMessageFactory,
                                      second_factory: AccuweatherAPIMessageFactory):
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


def test_calendar_factory():
    with patch('flip_sign.message_generation.build') as build_mock:
        build_mock.return_value.events.return_value.list.return_value.execute.return_value.get.return_value = results[0]

        next_mocks = []
        for result in results[1:]:
            next_mock = MagicMock()
            next_mock.execute.return_value.get.return_value = result
            next_mocks.append(next_mock)
        next_mocks.append(None)

        build_mock.return_value.events.return_value.list_next.side_effect = next_mocks

        cal_factory_obj = GoogleCalendarMessageFactory(keys['Google_Calendar_Test'])
        messages = cal_factory_obj.generate_messages()

        assert len(messages) == len(answers)

        for result, answer in zip(messages, answers):
            if isinstance(result, EphemeralDateMessage):
                assert_ephemeral_date_message_equal(result, answer)
            elif isinstance(result, AccuweatherAPIMessageFactory):
                assert_accuweather_message_factory_equal(result, answer)