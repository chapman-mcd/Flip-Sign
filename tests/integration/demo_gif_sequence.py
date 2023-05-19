from flip_sign.displays import FlipDotDisplay
import flip_sign.message_generation as msg_gen
from flip_sign.assets import root_dir
from flip_sign.transitions import simple_transition, dissolve_changes_only
from flip_sign.helpers import add_months
from pathlib import Path
from unittest.mock import patch, MagicMock
import datetime
import serial
from PIL import Image


mock_serial = input("Mock serial interface?:(y/n)").lower()[0] == 'y'

now = datetime.datetime.now().astimezone()
grandma_birthday = now + datetime.timedelta(days=10)
uruguay_trip = add_months(now, 1) + datetime.timedelta(days=5)

datetime.datetime.now().date()

nyan_cat_path = Path(root_dir + "/cache/google_drive_images/Nyan_Cat_Signscape.png")

rj_weather = {'DailyForecasts': [
    {'RealFeelTemperature': {'Maximum': {'Value': 28}, 'Minimum': {'Value': 23}},
     'Day': {'PrecipitationProbability': 20, 'Icon': 3}, 'Date': now.date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': 30}, 'Minimum': {'Value': 26}},
     'Day': {'PrecipitationProbability': 0, 'Icon': 1}, 'Date': (now + datetime.timedelta(days=1)).date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': 29}, 'Minimum': {'Value': 26}},
     'Day': {'PrecipitationProbability': 40, 'Icon': 5}, 'Date': (now + datetime.timedelta(days=2)).date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': 26}, 'Minimum': {'Value': 22}},
     'Day': {'PrecipitationProbability': 60, 'Icon': 12},
     'Date': (now + datetime.timedelta(days=3)).date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': 25}, 'Minimum': {'Value': 24}},
     'Day': {'PrecipitationProbability': 95, 'Icon': 15}, 'Date': (now + datetime.timedelta(days=4)).date().isoformat()}
]}

avon_weather = {'DailyForecasts': [
    {'RealFeelTemperature': {'Maximum': {'Value': 2}, 'Minimum': {'Value': -5}},
     'Day': {'PrecipitationProbability': 0, 'Icon': 32}, 'Date': now.date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': -1}, 'Minimum': {'Value': -8}},
     'Day': {'PrecipitationProbability': 100, 'Icon': 19},
     'Date': (now + datetime.timedelta(days=1)).date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': -2}, 'Minimum': {'Value': -10}},
     'Day': {'PrecipitationProbability': 40, 'Icon': 19},
     'Date': (now + datetime.timedelta(days=2)).date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': -12}, 'Minimum': {'Value': -15}},
     'Day': {'PrecipitationProbability': 10, 'Icon': 31},
     'Date': (now + datetime.timedelta(days=3)).date().isoformat()},
    {'RealFeelTemperature': {'Maximum': {'Value': 2}, 'Minimum': {'Value': -5}},
     'Day': {'PrecipitationProbability': 60, 'Icon': 24},
     'Date': (now + datetime.timedelta(days=4)).date().isoformat()}
]}

# define two local transition functions - only here because there are no unit tests
def push_up(current_state, desired_state):
    """
    A transition function that raises the desired state up from the bottom of the screen, "pushing" the current state
    off the top.  One blank line is inserted between.
    :param current_state: a message object
    :param desired_state: a message object
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """

    current_state=current_state.get_image()
    desired_state=desired_state.get_image()

    output = []

    current_state_y_val = -1
    desired_state_y_val = current_state.size[1]

    # while the desired image has not reached the top
    while desired_state_y_val >= 0:
        # initialize next image
        next = Image.new("1", current_state.size, color=0)
        # paste current state at its y valute
        next.paste(current_state, (0, current_state_y_val))
        # paste desired state at its y value
        next.paste(desired_state, (0, desired_state_y_val))
        # increment y vales
        current_state_y_val -= 1
        desired_state_y_val -= 1
        # append output
        output.append(next)

    output.append(desired_state)
    # return the output
    return output


def push_down(current_state, desired_state):
    """
    A transition function that raises the desired state down from the top of the screen, "pushing" the current state
    off the bottom.  One blank line is inserted between.
    :param current_state: a message object
    :param desired_state: a message object
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    current_state=current_state.get_image()
    desired_state=desired_state.get_image()

    output = []

    current_state_y_val = 1
    desired_state_y_val = 0 - current_state.size[1]

    # while the desired image has not reached the top
    while desired_state_y_val <= 0:
        # initialize next image
        next = Image.new("1", current_state.size, color=0)
        # paste current state at its y valute
        next.paste(current_state, (0, current_state_y_val))
        # paste desired state at its y value
        next.paste(desired_state, (0, desired_state_y_val))
        # increment y vales
        current_state_y_val += 1
        desired_state_y_val += 1
        # append output
        output.append(next)

    # return the output
    return output


def save_to_cache(image: Image.Image):
    """
    Saves file to local cache for integration testing purposes.  For patching on top of FlipDotDisplay.show

    :param image: (PIL.Image)
    :return: None
    """

    now = datetime.datetime.now().isoformat().replace(".", "_")
    image.save(fp=root_dir + "/cache/demo_gif_test/" + now + ".png")


messages = [
    msg_gen.RecurringFixedDateMessage(description="Grandma's Birthday", base_date_start=grandma_birthday,
                                      base_date_end=grandma_birthday, all_day=True, frequency=1.0),
    msg_gen.RecurringFixedDateMessage(description="Trip to Uruguay", base_date_start=uruguay_trip,
                                      base_date_end=uruguay_trip, all_day=True, frequency=1.0),
    msg_gen.AccuweatherDashboard(location={'Key': 'fake_location_lol'}, description='Rio de Janeiro',
                                 start_date=now.date(), language='portugues', frequency=1.0),
    msg_gen.ImageMessage(image=nyan_cat_path, frequency=1.0),
    msg_gen.AccuweatherDashboard(location={'Key': 'another_fake_double_lol'}, description='Avon',
                                 start_date=now.date(), language='english', frequency=1.0),
    msg_gen.BasicTextMessage(text="I call it a bargain:\nthe best I ever had", wrap_text=False),
    msg_gen.ImageMessage(image=Image.new('1', (168, 21), 1)),
    msg_gen.ImageMessage(image=Image.new('1', (168, 21), 0))
]

if mock_serial:
    serial_interface = MagicMock()
else:
    port = "/dev/ttyS0"
    serial_interface = serial.Serial(port=port, baudrate=57600, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS,
                                     timeout=1, stopbits=serial.STOPBITS_ONE)

display = FlipDotDisplay(serial_interface=serial_interface)


def run_show():
    for message in messages:
        display.update(message)


with patch('flip_sign.message_generation.hlp.accuweather_api_request') as accuweather_mock:
    accuweather_mock.side_effect = [rj_weather, avon_weather]
    with patch('flip_sign.transitions.select_transition_function') as select_function_mock:
        select_function_mock.side_effect = [simple_transition,
                                            simple_transition,
                                            dissolve_changes_only,
                                            push_up,
                                            push_down,
                                            simple_transition,
                                            simple_transition,
                                            simple_transition]
        if mock_serial:
            with patch.object(FlipDotDisplay, attribute="show") as display_mock:
                display_mock.side_effect = save_to_cache
                run_show()
        else:
            run_show()
