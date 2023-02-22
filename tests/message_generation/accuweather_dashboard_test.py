import flip_sign.helpers
from flip_sign.assets import root_dir
from flip_sign.message_generation import AccuweatherDashboard
from tests.helpers.draw_text_test import image_equal
import json
import datetime
from unittest.mock import patch
from PIL import Image

with open(root_dir + "/../tests/message_generation/test_assets/Nameless_Location_Resp_Json.txt") as f:
    nameless_tn_location_resp = json.loads(f.read())


@patch(f'{flip_sign.message_generation.__name__}.hlp.render_day',
       wraps=flip_sign.helpers.render_day)
@patch(f'{flip_sign.message_generation.__name__}.hlp.accuweather_api_request',
       wraps=flip_sign.helpers.accuweather_api_request)
@patch(f'{flip_sign.message_generation.__name__}.datetime.date', wraps=datetime.date)
def test_weather_dashboard_calls(mock_datetime, mock_accuweather, mock_render_day):
    fake_now = datetime.datetime(year=2023, month=2, day=9, hour=7, minute=15, second=38)
    fake_today = fake_now.date()
    mock_datetime.today.return_value = fake_today
    with open("./message_generation/test_assets/NamelessTN_5DayForecast_Metric.txt") as f:
        nameless_tn_forecast_resp = json.loads(f.read())
        mock_accuweather.return_value = nameless_tn_forecast_resp

    test_msg = AccuweatherDashboard(location=nameless_tn_location_resp, description="Home", start_date=fake_today,
                                    language="english", frequency=1.0)
    test_msg.render()

    calls = (
        {'high': 19.3, 'low': 2.6, 'chance_precipitation': 0.49, 'iso_weekday': 4, 'icon_name': 'partlycloudy',
         'language': 'english'},
        {'high': 13.4, 'low': -3.8, 'chance_precipitation': 0.07, 'iso_weekday': 5, 'icon_name': 'partlycloudy',
         'language': 'english'},
        {'high': 8.2, 'low': -3.7, 'chance_precipitation': 0.18, 'iso_weekday': 6, 'icon_name': 'mostlycloudy',
         'language': 'english'},
        {'high': 10.1, 'low': -3.8, 'chance_precipitation': 0.25, 'iso_weekday': 7, 'icon_name': 'partlycloudy',
         'language': 'english'},
        {'high': 14.6, 'low': -0.5, 'chance_precipitation': 0.07, 'iso_weekday': 1, 'icon_name': 'partlycloudy',
         'language': 'english'}
    )

    for call in calls:
        mock_render_day.assert_any_call(**call)


@patch(f'{flip_sign.message_generation.__name__}.hlp.accuweather_api_request',
       wraps=flip_sign.helpers.accuweather_api_request)
@patch(f'{flip_sign.message_generation.__name__}.datetime.date', wraps=datetime.date)
def test_weather_dashboard_output(mock_datetime, mock_accuweather):
    fake_now = datetime.datetime(year=2023, month=2, day=9, hour=7, minute=15, second=38)
    fake_today = fake_now.date()
    mock_datetime.today.return_value = fake_today
    with open("./message_generation/test_assets/NamelessTN_5DayForecast_Metric.txt") as f:
        nameless_tn_forecast_resp = json.loads(f.read())
        mock_accuweather.return_value = nameless_tn_forecast_resp

    # test dashboard in english
    with Image.open("./message_generation/test_assets/Dashboard_Answer_1.png") as answer:
        out_path = "./message_generation/test_output/Dashboard_Test_1.png"
        test_msg = AccuweatherDashboard(location=nameless_tn_location_resp, description="Home", start_date=fake_today,
                                        language="english", frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test dashboard in portuguese
    with Image.open("./message_generation/test_assets/Dashboard_Answer_2.png") as answer:
        out_path = "./message_generation/test_output/Dashboard_Test_2.png"
        test_msg = AccuweatherDashboard(location=nameless_tn_location_resp, description="Casa", start_date=fake_today,
                                        language="portugues", frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test dashboard with start date tomorrow
    with Image.open("./message_generation/test_assets/Dashboard_Answer_3.png") as answer:
        out_path = "./message_generation/test_output/Dashboard_Test_3.png"
        test_msg = AccuweatherDashboard(location=nameless_tn_location_resp, description="Home",
                                        start_date=fake_today + datetime.timedelta(days=1),
                                        language="english", frequency=1.0)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
