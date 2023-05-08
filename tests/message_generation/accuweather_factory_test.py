from flip_sign.assets import root_dir
from unittest.mock import patch
from flip_sign.message_generation import AccuweatherAPIMessageFactory, AccuweatherDescription, BasicTextMessage
import json
import datetime

with open(root_dir + "/../tests/message_generation/test_assets/accuweather_location_response_paris.json") as f:
    paris_location = json.load(f)


@patch('flip_sign.helpers.accuweather_api_request')
def test_paris_dashboard_basic(api_request_mock):
    api_request_mock.return_value = paris_location

    factory = AccuweatherAPIMessageFactory(location_description="Paris, France")

    messages = factory.generate_messages()

    assert len(messages) == 1
    assert messages[0].location == paris_location
    assert messages[0].description == "Saint-Merri"
    assert messages[0].language == "english"

    api_request_mock.assert_called()


@patch('flip_sign.helpers.accuweather_api_request')
def test_paris_dashboard_descriptions(api_request_mock):
    api_request_mock.return_value = paris_location

    factory = AccuweatherAPIMessageFactory(location_description="Paris, France", weather_dashboard=False,
                                           weather_descriptions=True)

    messages = factory.generate_messages()

    assert len(messages) == 3
    for i, message in enumerate(messages):
        assert type(message) == AccuweatherDescription
        assert message.location == paris_location
        assert message.description == "Saint-Merri"
        if i in [0, 1]:
            assert message.date == datetime.date.today()
            if i == 0:
                pass
                assert message.day_or_night == 'Day'
            else:
                assert message.day_or_night == 'Night'
        if i == 3:
            assert message.date == datetime.date.today() + datetime.timedelta(days=1)
            assert message.day_or_night == 'Day'


@patch('flip_sign.helpers.accuweather_api_request')
def test_paris_dashboard_headline(api_request_mock):
    api_request_mock.return_value = paris_location

    factory = AccuweatherAPIMessageFactory(location_description="Paris, France", weather_dashboard=False,
                                           weather_descriptions=False, headline=True)

    messages = factory.generate_messages()

    assert len(messages) == 1
    assert messages[0].location == paris_location
    assert messages[0].description == "Saint-Merri"
    assert messages[0].headline


@patch('flip_sign.helpers.geocode_to_lat_long')
def test_location_api_error(geocode_mock):
    geocode_mock.side_effect = ValueError

    factory = AccuweatherAPIMessageFactory(location_description="fhqwhgads", weather_dashboard=False,
                                           weather_descriptions=False, headline=True)

    messages = factory.generate_messages()

    assert len(messages) == 1

    assert type(messages[0]) == BasicTextMessage
    assert messages[0].text == "Error geocoding location: " + "fhqwhgads"
    assert messages[0]  # proxy for confirming that the message displayed (e.g. with frequency=1)

    geocode_mock.assert_called()
