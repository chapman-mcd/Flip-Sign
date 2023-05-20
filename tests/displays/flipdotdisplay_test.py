from flip_sign.assets import root_dir
from flip_sign.message_generation import BasicTextMessage, ImageMessage
from flip_sign.displays import FlipDotDisplay
from tests.helpers.draw_text_test import image_equal
from tests.message_generation.google_sheet_message_factory_test import assert_message_gen_objects_equal
import flip_sign.transitions as transitions
from unittest.mock import MagicMock, patch
from urllib.error import URLError
from serial import Serial
from PIL import Image


def test_show_nyan_cat():
    with open(root_dir + "/../tests/displays/test_assets/serial_nyan_answer.txt", 'rb') as f:
        nyan_cat_answer = f.read()

    nyan_cat = Image.open(root_dir + "/../tests/displays/test_assets/Nyan_Cat_Signscape.png").convert(mode="1")

    serial_mock = MagicMock(spec=Serial)
    display = FlipDotDisplay(serial_interface=serial_mock)
    display.show(nyan_cat)

    serial_mock.write.assert_called_with(nyan_cat_answer)


# test proper calls to self.show - first test simpletransition
@patch.object(FlipDotDisplay, attribute="show")
@patch('flip_sign.displays.transitions.select_transition_function')
def test_update_simple_transition(transition_function_mock, flip_dot_mock):
    transition_function_mock.return_value = transitions.simple_transition
    next_message = BasicTextMessage("This is a test.  This is only a test.")
    next_message_copy = BasicTextMessage("This is a test.  This is only a test.")
    next_message_copy.render()

    serial_mock = MagicMock(spec=Serial)
    display = FlipDotDisplay(serial_interface=serial_mock)
    successful_update = display.update(next_message=next_message)

    assert successful_update
    assert image_equal(flip_dot_mock.call_args.kwargs['image'], next_message_copy.get_image())
    assert_message_gen_objects_equal(display.current_message, next_message)  # confirm self.current_message updated
    assert image_equal(display.current_state, next_message_copy.get_image())  # confirm self.current_state updated


# next test dissolve_changes_only
@patch.object(FlipDotDisplay, attribute="show")
@patch('flip_sign.displays.transitions.select_transition_function')
def test_update_dissolve_transition(transition_function_mock, flip_dot_mock):
    transition_function_mock.return_value = transitions.dissolve_changes_only
    next_message = BasicTextMessage("This is a test.  This is only a test.")
    next_message_copy = BasicTextMessage("This is a test.  This is only a test.")
    next_message_copy.render()

    serial_mock = MagicMock(spec=Serial)
    display = FlipDotDisplay(serial_interface=serial_mock)
    flip_dot_mock.reset_mock()  # clear out the call to show a blank image during setup
    successful_update = display.update(next_message=next_message)

    blank_image_message = ImageMessage(image=Image.new('1', (168, 21), 0))

    image_transition = transitions.dissolve_changes_only(blank_image_message, next_message_copy)

    assert successful_update
    assert image_equal(flip_dot_mock.call_args.kwargs['image'], next_message_copy.get_image())  # confirm right answer
    assert len(flip_dot_mock.call_args_list) == len(image_transition)  # confirm show called the proper number of times


# test error handling: next_message.render throws error
@patch.object(FlipDotDisplay, attribute="show")
@patch('flip_sign.displays.transitions.select_transition_function')
def test_value_error_handling(transition_function_mock, flip_dot_mock):
    transition_function_mock.return_value = transitions.simple_transition
    next_message_mock = MagicMock(spec=BasicTextMessage)
    next_message_mock.render.side_effect = ValueError  # DateMessages can raise value error if in the past

    serial_mock = MagicMock(spec=Serial)
    display = FlipDotDisplay(serial_interface=serial_mock)
    flip_dot_mock.reset_mock()  # clear out the call to show a blank image during setup
    successful_update = display.update(next_message=next_message_mock)

    assert not successful_update
    flip_dot_mock.assert_not_called()


# test error handling: next_message.render throws URLError (no internet / cable unplugged)
# Accuweather message renders can throw URLError if internet down
@patch.object(FlipDotDisplay, attribute="show")
@patch('flip_sign.displays.transitions.select_transition_function')
def test_url_error_handling(transition_function_mock, flip_dot_mock):
    transition_function_mock.return_value = transitions.simple_transition
    next_message_mock = MagicMock(spec=BasicTextMessage)
    next_message_mock.render.side_effect = URLError(reason="Somebody set us up the bomb.")

    serial_mock = MagicMock(spec=Serial)
    display = FlipDotDisplay(serial_interface=serial_mock)
    flip_dot_mock.reset_mock()  # clear out the call to show a blank image during setup
    successful_update = display.update(next_message=next_message_mock)

    assert not successful_update
    flip_dot_mock.assert_not_called()


# test display.cycle_dots method
@patch('time.sleep')
@patch.object(FlipDotDisplay, attribute="show")
def test_cycle_dots(flip_dot_mock, time_mock):
    serial_mock = MagicMock(spec=Serial)
    display = FlipDotDisplay(serial_interface=serial_mock)
    next_message = BasicTextMessage("This is a test.  This is only a test.")
    display.update(next_message=next_message)
    flip_dot_mock.reset_mock()

    display.cycle_dots()

    assert len(time_mock.call_args_list) == 3
    assert len(flip_dot_mock.call_args_list) == 3
    for i, (args, kwargs) in enumerate(flip_dot_mock.call_args_list):
        if i == 1:
            assert image_equal(kwargs['image'], Image.new('1', (168, 21), 1))
        else:
            image_equal(kwargs['image'], Image.new('1', (168, 21), 0))

    assert image_equal(display.current_state, Image.new('1', (168, 21), 0))
    blank_image_message = ImageMessage(image=Image.new('1', (168, 21), 0))
    assert_message_gen_objects_equal(display.current_message, blank_image_message)


