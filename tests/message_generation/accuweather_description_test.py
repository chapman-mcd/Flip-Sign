import flip_sign.helpers
from flip_sign.assets import root_dir
from flip_sign.message_generation import AccuweatherDescription
import json
import pytest
import datetime
from unittest.mock import patch

with open(root_dir + "/../tests/message_generation/test_assets/Nameless_Location_Resp_Json.txt") as f:
    nameless_tn_location_resp = json.loads(f.read())


@patch(f'{flip_sign.message_generation.__name__}.hlp.accuweather_api_request',
       wraps=flip_sign.helpers.accuweather_api_request)
@patch(f'{flip_sign.message_generation.__name__}.datetime.date', wraps=datetime.date)
def test_weather_description(mock_datetime, mock_accuweather):
    fake_now = datetime.datetime(year=2023, month=2, day=9, hour=7, minute=15, second=38)
    fake_today = fake_now.date()
    mock_datetime.today.return_value = fake_today
    with open("./message_generation/test_assets/NamelessTN_5DayForecast_Metric.txt") as f:
        nameless_tn_forecast_resp = json.loads(f.read())
        mock_accuweather.return_value = nameless_tn_forecast_resp
        locstr = nameless_tn_location_resp['LocalizedName']

    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=True)
    test_msg.render()
    test_msg.get_image().save("./message_generation/test_output/Test_Weather_Desc_01.png")
    assert test_msg.text == locstr + ":" + nameless_tn_forecast_resp['Headline']['Text']

    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=False, date=fake_now,
                                      day_or_night='day')
    test_msg.render()
    test_msg.get_image().save("./message_generation/test_output/Test_Weather_Desc_02.png")
    assert test_msg.text == locstr + ":Today(D): " + nameless_tn_forecast_resp['DailyForecasts'][0]['Day']['LongPhrase']

    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=False, date=fake_now,
                                      day_or_night='night')
    test_msg.render()
    test_msg.get_image().save("./message_generation/test_output/Test_Weather_Desc_03.png")
    assert test_msg.text == locstr + ":Today(N): " + \
                                                nameless_tn_forecast_resp['DailyForecasts'][0]['Night']['LongPhrase']

    fake_tomorrow = datetime.date(year=2023, month=2, day=10)
    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=False, date=fake_tomorrow,
                                      day_or_night='day')
    test_msg.render()
    test_msg.get_image().save("./message_generation/test_output/Test_Weather_Desc_04.png")
    assert test_msg.text == locstr + ":Tomorrow(D): " + \
                                                nameless_tn_forecast_resp['DailyForecasts'][1]['Day']['LongPhrase']

    fake_tomorrow = datetime.date(year=2023, month=2, day=11)
    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=False, date=fake_tomorrow,
                                      day_or_night='day')
    test_msg.render()
    test_msg.get_image().save("./message_generation/test_output/Test_Weather_Desc_04.png")
    assert test_msg.text == locstr + ":2023-02-11(D): " + \
                                                nameless_tn_forecast_resp['DailyForecasts'][2]['Day']['LongPhrase']

    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, description="Home", headline=False,
                                      date=fake_now, day_or_night='day')
    test_msg.render()
    test_msg.get_image().save("./message_generation/test_output/Test_Weather_Desc_05.png")
    assert test_msg.text == "Home:Today(D): " + nameless_tn_forecast_resp['DailyForecasts'][0]['Day']['LongPhrase']

    fake_too_far = datetime.date(year=2050, month=1, day=1)
    with pytest.raises(ValueError) as exc_info:
        test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=False, date=fake_too_far,
                                          day_or_night='day')
        test_msg.render()
    assert exc_info.value.args[0] == "Weather Description Obj: Provided date not found in API response."


def test_logging_with_bad_input(caplog):
    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=False)
    assert not test_msg
    assert test_msg.init_failure
    correct_log_response = "Improper WeatherDescription construction.  Location:" + str(nameless_tn_location_resp)
    assert caplog.records[-1].getMessage() == correct_log_response


@patch(f'{flip_sign.message_generation.__name__}.hlp.accuweather_api_request',
       wraps=flip_sign.helpers.accuweather_api_request)
def test_string_rep(mock_accuweather):
    with open("./message_generation/test_assets/NamelessTN_5DayForecast_Metric.txt") as f:
        nameless_tn_forecast_resp = json.loads(f.read())
        mock_accuweather.return_value = nameless_tn_forecast_resp
        locstr = nameless_tn_location_resp['LocalizedName']

    test_msg = AccuweatherDescription(location=nameless_tn_location_resp, headline=True)

    string_answer = ''.join(["AccuweatherDescription: ",
                             "description=" + locstr + ", ",
                             "headline=True, ",
                             "date=None, day_or_night=Day"])

    assert str(test_msg) == string_answer

