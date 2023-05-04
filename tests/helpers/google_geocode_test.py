from flip_sign.assets import root_dir
from unittest.mock import patch
import flip_sign.helpers as hlp
import pytest

responses = []
for i in range(5):
    with open(root_dir + "/../tests/helpers/test_assets/google_location_response_" + str(i) + ".txt", "rb") as f:
        responses.append(f.read())

answers = [{'lat': 48.856614, 'lng': 2.3522219},
           {'lat': 35.7191585, 'lng': -85.4169211},
           {'lat': -22.9404548, 'lng': -43.19726319999999},
           {'lat': 51.5033779, 'lng': -0.0765787},
           {'lat': 51.5033779, 'lng': -0.0765787}]  # last test needs to raise an error, answer is not applicable

tests = ["Paris, France", "38585", "22241-125", "SE1 2UP", "94327u1fda is not a place"]


@patch('flip_sign.helpers.urlopen')
def test_geocode_to_lat_long(urlopen_mock):
    urlopen_mock.return_value.read.side_effect = responses

    for test, answer in zip(tests[:-1], answers[:-1]):
        result = hlp.geocode_to_lat_long(test)
        assert result == answer

    with pytest.raises(ValueError):
        _ = hlp.geocode_to_lat_long(tests[-1])

    # confirm results cached
    urlopen_mock.reset_mock()
    urlopen_mock.read.side_effect = responses
    for test, answer in zip(tests[:-1], answers[:-1]):
        result = hlp.geocode_to_lat_long(test)
        assert result == answer

    urlopen_mock.assert_not_called()


