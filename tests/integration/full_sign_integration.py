from flip_sign.run_sign import run_sign
from flip_sign.displays import FlipDotDisplay
from flip_sign.assets import root_dir, keys
from flip_sign.transitions import simple_transition
from unittest.mock import patch
import datetime
import serial
from PIL import Image
import flip_sign.config as config
import logging

initial_sheet = input("Enter sheet_id for initial google sheet:")
config.WAIT_TIME = datetime.timedelta(seconds=30)

logging.basicConfig(filename=root_dir + "/../tests/integration/integration_test.log",
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


def save_to_cache(image: Image.Image):
    """
    Saves file to local cache for integration testing purposes.  For patching on top of FlipDotDisplay.show

    :param image: (PIL.Image)
    :return: None
    """

    now = datetime.datetime.now().isoformat().replace(".", "_")
    image.save(fp=root_dir + "/cache/integration_test/" + now + ".png")


with patch.object(FlipDotDisplay, attribute="show") as display_mock:
    display_mock.side_effect = save_to_cache
    with patch.dict(keys, {'GoogleSheet': initial_sheet}):
        with patch('flip_sign.run_sign.serial') as serial_mock:
            with patch('flip_sign.displays.transitions.select_transition_function') as transition_mock:
                transition_mock.return_value = simple_transition
                run_sign()
