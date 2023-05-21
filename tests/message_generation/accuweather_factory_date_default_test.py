# issues with date default being set
from flip_sign.assets import root_dir
from unittest.mock import patch
import json
import datetime
import flip_sign.message_generation as msg_gen


with open(root_dir + "/../tests/message_generation/test_assets/accuweather_location_response_paris.json") as f:
    paris_location = json.load(f)


nyd_2005 = datetime.date(2005, 1, 1)


# test originally failed since date was set on package import (in the class) and not when the object was
# instantiated
@patch(f'{msg_gen.__name__}.datetime', wraps=datetime)
@patch('flip_sign.helpers.accuweather_api_request')
def test_default_date_from_import(api_request_mock, datetime_mock):
    api_request_mock.return_value = paris_location
    datetime_mock.date.today.return_value = nyd_2005

    factory = msg_gen.AccuweatherAPIMessageFactory(location_description="Paris, France", weather_dashboard=False,
                                                   weather_descriptions=True)

    messages = factory.generate_messages()

    assert len(messages) == 3
    for i, message in enumerate(messages):
        assert type(message) == msg_gen.AccuweatherDescription
        assert message.location == paris_location
        assert message.description == "Saint-Merri"
        assert not message.headline
        if i in [0, 1]:
            assert message.date == nyd_2005
            if i == 0:
                pass
                assert message.day_or_night == 'Day'
            else:
                assert message.day_or_night == 'Night'
        if i == 3:
            assert message.date == nyd_2005 + datetime.timedelta(days=1)
            assert message.day_or_night == 'Day'
