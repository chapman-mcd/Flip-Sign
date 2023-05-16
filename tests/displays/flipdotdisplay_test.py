from flip_sign.assets import root_dir
from flip_sign.displays import FlipDotDisplay
from unittest.mock import MagicMock
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



