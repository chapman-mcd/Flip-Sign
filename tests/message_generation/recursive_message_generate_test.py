import flip_sign.message_generation as msg_gen
import flip_sign.variable_date_functions as vdf
from tests.message_generation.google_sheet_message_factory_test import assert_message_gen_objects_equal
from unittest.mock import patch
from flip_sign.assets import root_dir
from pathlib import Path
import datetime
import config
from tzlocal import get_localzone_name
from pytz import timezone

LOCAL_TIMEZONE = timezone(get_localzone_name())

# Test Map - Originally Provide a single GoogleSheet Object
# GoogleSheet
#   Google Calendar
#       EphemeralDateMessage
#       AccuweatherFactory
#           Dashboard
#           Headline
#   GoogleDrive
#       Image1
#       Image2
#   RecurringFixed
#   RecurringVariable
#   AccuweatherFactory
#       Dashboard
#       Headline
#       Description (1)
#   GoogleSheet
#       DateMatch
#       RecurringFixed


today = datetime.date.today()

answers = [
    msg_gen.EphemeralDateMessage(description="Test Event", start=datetime.datetime(2056, 1, 1, tzinfo=LOCAL_TIMEZONE),
                                 end=datetime.datetime(2056, 1, 1, tzinfo=LOCAL_TIMEZONE), all_day=True),
    msg_gen.AccuweatherDashboard(location={"some json": "lol"}, description="Someplace", start_date=today,
                                 language=config.WEATHER_LANGUAGE),
    msg_gen.AccuweatherDescription(location={"some json": "lol"}, description="Someplace", headline=True),
    msg_gen.ImageMessage(image=Path(root_dir + "/../tests/helpers/test_assets/Test_Align_01.png")),
    msg_gen.ImageMessage(image=Path(root_dir + "/../tests/helpers/test_assets/Test_Align_02.png")),
    msg_gen.RecurringFixedDateMessage(description="Christmas", base_date_start="1999-12-25"),
    msg_gen.RecurringVariableDateMessage(description="Carnaval", next_dates_func=vdf.carnaval, all_day=True),
    msg_gen.AccuweatherDashboard(location={"some other json": "lol"}, description="Someplace Else", start_date=today,
                                 language=config.WEATHER_LANGUAGE),
    msg_gen.AccuweatherDescription(location={"some other json": "lol"}, description="Someplace Else", headline=True),
    msg_gen.AccuweatherDescription(location={"some other json": "lol"}, description="Someplace Else",
                                   date=today, day_or_night='day'),
    msg_gen.DateMatchTextMessage(text="This is Date-Match"),
    msg_gen.RecurringFixedDateMessage(description="Just Another Day", base_date_start="2001-08-14")
]


@patch.object(msg_gen.GoogleSheetMessageFactory, attribute='generate_messages')
@patch.object(msg_gen.GoogleDriveImageMessageFactory, attribute='generate_messages')
@patch.object(msg_gen.GoogleCalendarMessageFactory, attribute='generate_messages')
@patch.object(msg_gen.AccuweatherAPIMessageFactory, attribute='generate_messages')
def test_recursive_message_generate(accuweather_mock, google_calendar_mock, google_drive_mock, google_sheet_mock):
    google_sheet_mock.side_effect = [
        [msg_gen.GoogleCalendarMessageFactory(calendar_id="blurgh@calendar.google.com"),
         msg_gen.GoogleDriveImageMessageFactory(drive_folder="blurgh in parents"),
         msg_gen.RecurringFixedDateMessage(description="Christmas", base_date_start="1999-12-25"),
         msg_gen.RecurringVariableDateMessage(description="Carnaval", next_dates_func=vdf.carnaval, all_day=True),
         msg_gen.AccuweatherAPIMessageFactory(location_description="Someplace Else"),
         msg_gen.GoogleSheetMessageFactory(sheet_id="blurgh2")],
        [msg_gen.DateMatchTextMessage(text="This is Date-Match"),
         msg_gen.RecurringFixedDateMessage(description="Just Another Day", base_date_start="2001-08-14")]
    ]

    google_drive_mock.return_value = [
        msg_gen.ImageMessage(image=Path(root_dir + "/../tests/helpers/test_assets/Test_Align_01.png")),
        msg_gen.ImageMessage(image=Path(root_dir + "/../tests/helpers/test_assets/Test_Align_02.png"))]

    accuweather_mock.side_effect = [
        [msg_gen.AccuweatherDashboard(location={"some json": "lol"}, description="Someplace",
                                      start_date=today, language=config.WEATHER_LANGUAGE),
         msg_gen.AccuweatherDescription(location={"some json": "lol"}, description="Someplace",
                                        headline=True)],
        [msg_gen.AccuweatherDashboard(location={"some other json": "lol"}, description="Someplace Else",
                                      start_date=today, language=config.WEATHER_LANGUAGE),
         msg_gen.AccuweatherDescription(location={"some other json": "lol"}, description="Someplace Else",
                                        headline=True),
         msg_gen.AccuweatherDescription(location={"some other json": "lol"}, description="Someplace Else",
                                        date=today, day_or_night='day')]
    ]

    google_calendar_mock.return_value = [
        msg_gen.EphemeralDateMessage(description="Test Event",
                                     start=datetime.datetime(2056, 1, 1, tzinfo=LOCAL_TIMEZONE),
                                     end=datetime.datetime(2056, 1, 1, tzinfo=LOCAL_TIMEZONE),
                                     all_day=True),
        msg_gen.AccuweatherAPIMessageFactory(location_description="Someplace")
    ]

    outputs = msg_gen.recursive_message_generate(to_be_processed=[msg_gen.GoogleSheetMessageFactory(sheet_id="init")])

    assert len(answers) == len(outputs)

    for answer, output in zip(answers, outputs):
        assert_message_gen_objects_equal(answer, output)
