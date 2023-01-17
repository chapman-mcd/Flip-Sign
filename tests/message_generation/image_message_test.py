from flip_sign.message_generation import ImageMessage, linear_decline_frequency_image_message
from PIL import Image
from pathlib import Path
from tests.helpers.draw_text_test import image_equal
from unittest.mock import MagicMock
import datetime
from collections import namedtuple


def test_same_image_returned():
    with Image.open("./helpers/test_assets/Test_01.png") as answer:
        image_message = ImageMessage(image=answer)
        assert image_equal(image_message.get_image(), answer)

        test_01_path = Path("./helpers/test_assets/Test_01.png")
        image_message = ImageMessage(image=test_01_path)
        assert image_equal(image_message.get_image(), answer)

    with Image.open("./helpers/test_assets/signscape_1.png").convert("1") as answer:
        image_message = ImageMessage(image=answer)
        assert image_equal(image_message.get_image(), answer)

def test_frequency_function_called():
    frequency_function = MagicMock(return_value=1.0)
    with Image.open("./helpers/test_assets/Test_01.png") as answer:
        _ = ImageMessage(image=answer, frequency=frequency_function)
        frequency_function.assert_called_with(answer)


def test_frequency_function():
    now_timestamp = datetime.datetime.now().timestamp()
    spec_return = namedtuple('modified_time', ['st_mtime'])
    path_object = MagicMock(return_value=None, spec=Path)
    # check an object created recently
    path_object.stat = MagicMock(return_value=spec_return(now_timestamp - 20*24*60*60))
    assert linear_decline_frequency_image_message(path_object) == 1.0

    # check an object created a long time ago
    path_object.stat = MagicMock(return_value=spec_return(now_timestamp - 400*24*60*60))
    assert linear_decline_frequency_image_message(path_object) == 0.25

    # check an object created 7mo ago
    path_object.stat = MagicMock(return_value=spec_return(now_timestamp - 210*24*60*60))
    assert linear_decline_frequency_image_message(path_object) - 0.5 < 0.01

    # check a PIL.Image object
    image_object = MagicMock(return_value=None, spec=Image.Image)
    assert linear_decline_frequency_image_message(image_object) == 0.5


def test_wrong_image_size(caplog):
    rickroll_path = Path("./helpers/test_assets/rickroll.jpeg")
    rickroll = ImageMessage(rickroll_path, 1.0)
    assert not rickroll  # message should not display because it's the wrong size
    assert caplog.records[-1].getMessage() == "Image is the wrong size.  Image:" + str(rickroll_path)


def test_improper_input(caplog):
    test = ImageMessage(None, 1.0)
    assert not test
    assert caplog.records[-1].getMessage() == "Invalid image passed, must be Image or Path. Passed:" + str(None)

    test = ImageMessage(Path("./helpers/test_assets/Test_01.png"), None)
    assert not test
    assert caplog.records[-1].getMessage() == "Invalid frequency passed, must be callable or float. Passed:" + str(None)


def test_bad_input(caplog):
    # first test in the main image load
    invalid_path = Path("./not_a_real_file.exe")
    test = ImageMessage(invalid_path, 1.0)
    assert not test
    assert caplog.records[-1].getMessage() == "Error opening image. Image:" + str(invalid_path)

    test = ImageMessage(invalid_path)
    assert not test
    assert caplog.records[-1].getMessage() == "Error calculating frequency. Image:" + str(invalid_path)

    not_image_file = Path("./helpers/test_assets/nameless_tn_location_resp.txt")
    test = ImageMessage(not_image_file, 1.0)
    assert not test
    assert caplog.records[-1].getMessage() == "Error opening image. Image:" + str(not_image_file)
