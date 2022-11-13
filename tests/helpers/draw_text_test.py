import flip_sign.helpers as hlp
from PIL import Image, ImageChops
from unittest.mock import patch, MagicMock
import os

press_start_path = r'../flip_sign/assets/fonts/PressStart2P.ttf'
dat_dot_path = r'../flip_sign/assets/fonts/DatDot_edited_v1.ttf'

default_wrap_parameters = (hlp.wrap_parameter_set(press_start_path, 16, 1, False, False, {}),
                           hlp.wrap_parameter_set(press_start_path, 9, 1, False, False, {}),
                           hlp.wrap_parameter_set(press_start_path, 8, 1, False, False, {}),
                           hlp.wrap_parameter_set(dat_dot_path, 8, -2, False, False, {}),
                           hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, False, {}),
                           hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, True, {}))


logging_mock = MagicMock()
@patch("logging.getLogger", logging_mock)
def test_draw_text_best_parameters():
    full_sign_size = (168, 21)
    print(os.getcwd())
    # test a long message using wrap_text=False
    text = "\n".join(['You wrote a note with chalk on my door,',
                      "a message I'd known long before:",
                     "'On any given day you'll find me gone'"])
    with Image.open("./helpers/test_assets/Test_01.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=None, wrap_text=False)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test a standard calendar-type message
    text = ['Retorno às    5d ', 'Aulas Day     16h']
    with Image.open("./helpers/test_assets/Test_02.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=1, wrap_text=False)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test a calendar message with all lowercase (does not work properly unless fixed_spacing=1)
    text = ['all lowercase 8mo', 'mess          16d']
    with Image.open("./helpers/test_assets/Test_03.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=1, wrap_text=False)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test a message that is too long with a custom placeholder
    text = "".join(["O mar ta bonito ta cheio de caminho pedala pedala pedala pedalinho.",
                   " me leva pra longe bem devagarinho lorem ipsum lorem ipsum lorem ipsum"])
    custom_wrap_parameters_1 = (hlp.wrap_parameter_set(press_start_path, 16, 1, False, False, {}),
                                hlp.wrap_parameter_set(press_start_path, 9, 1, False, False, {}),
                                hlp.wrap_parameter_set(press_start_path, 8, 1, False, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, False, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, True, {'placeholder': '[-]'}))
    with Image.open("./helpers/test_assets/Test_04.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=custom_wrap_parameters_1, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=None, wrap_text=True)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()
        pass

    # test a message that is too long with the default placeholder
    with Image.open("./helpers/test_assets/Test_05.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=None, wrap_text=True)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test a message that fits in a medium font
    text = "I call it a bargain: the best I ever had"
    with Image.open("./helpers/test_assets/Test_06.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=None, wrap_text=True)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test a message that fits in a large font
    text = "A doo-da-ee!!"
    with Image.open("./helpers/test_assets/Test_07.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=True, align='center',
                                             fixed_spacing=None, wrap_text=True)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test a message that does not fit, with wrap_text=False (gets to end of params_order)
    # check message written matches and also that a message is written to the log
    text = "O mar ta bonito ta cheio de caminho pedala\npedala pedala pedalinho. me leva pra longe bem\ndevagarinho lorem ipsum lorem ipsum lorem ipsum"
    #text = "\n".join(["O mar ta bonito ta cheio de caminho pedala",
    #                  "pedala pedala pedalinho. me leva pra longe bem",
    #                  "devagarinho lorem ipsum lorem ipsum lorem ipsum"])
    log_text = "draw_text_best_parameters reached end of params_order without fitting, text: " + text
    with Image.open("./helpers/test_assets/Test_08.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             center_vertical=True, center_horizontal=False, align='left',
                                             fixed_spacing=None, wrap_text=False)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()
    logging_mock('flip_sign.helpers').warning.assert_called_with(log_text)

    # test simple weather stub at large size
    weather_stub_size = (58, 21)
    text = "Rio"
    with Image.open("./helpers/test_assets/Test_09.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=weather_stub_size,
                                             text=text, center_vertical=True, center_horizontal=True, align='left',
                                             fixed_spacing=None, wrap_text=False)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    # test longer case which needs line breaks, with and without the break_long_words kwarg
    text = 'Boulder'
    with Image.open("./helpers/test_assets/Test_10.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=weather_stub_size,
                                             text=text, center_vertical=True, center_horizontal=False, align='left',
                                             fixed_spacing=None, wrap_text=True)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()

    custom_wrap_parameters_2 = (hlp.wrap_parameter_set(press_start_path, 16, 1, False, False, {}),
                                hlp.wrap_parameter_set(press_start_path, 9, 1, False, False,
                                                       {'break_long_words': False}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, False, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, True, {}))
    with Image.open("./helpers/test_assets/Test_11.png") as answer:
        test = hlp.draw_text_best_parameters(params_order=custom_wrap_parameters_2, bbox_size=weather_stub_size,
                                             text=text, center_vertical=True, center_horizontal=True, align='left',
                                             fixed_spacing=None, wrap_text=True)
        assert not ImageChops.difference(test.convert('RGBA'), answer.convert('RGBA')).getbbox()
