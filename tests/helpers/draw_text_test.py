import flip_sign.helpers as hlp
from PIL import Image
import hashlib
import pytest

press_start_path = r'../flip_sign/assets/fonts/PressStart2P.ttf'
dat_dot_path = r'../flip_sign/assets/fonts/DatDot_edited_v1.ttf'

default_wrap_parameters = (hlp.wrap_parameter_set(press_start_path, 16, 1, False, False, {}),
                           hlp.wrap_parameter_set(press_start_path, 9, 1, False, False, {}),
                           hlp.wrap_parameter_set(press_start_path, 8, 1, False, False, {}),
                           hlp.wrap_parameter_set(dat_dot_path, 8, -2, False, False, {}),
                           hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, False, {}),
                           hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, True, {}))


def image_equal(image_1, image_2):
    """
    Compares two images and returns a boolean indicating if they are the same image.

    :param image_1: (PIL.Image) left image
    :param image_2: (PIL.Image) right image
    :return: equal: (bool) whether the images are the same
    """

    return hashlib.sha512(image_1.tobytes()).hexdigest() == hashlib.sha512(image_2.tobytes()).hexdigest()


def test_draw_text_best_parameters(caplog):
    full_sign_size = (168, 21)
    # test a long message using wrap_text=False
    text = "\n".join(['You wrote a note with chalk on my door,',
                      "a message I'd known long before:",
                     "'On any given day you'll find me gone'"])
    with Image.open("./helpers/test_assets/Test_01.png") as answer:
        out_path = "./helpers/test_output/Test_01.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=None, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[3]
        assert test[2] == -1

    # test a standard calendar-type message
    text = ['Retorno às    5d ', 'Aulas Day     16h']
    with Image.open("./helpers/test_assets/Test_02.png") as answer:
        out_path = "./helpers/test_output/Test_02.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=1, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[1]
        assert test[2] == 1

    # test a calendar message with all lowercase (does not work properly unless fixed_spacing=1)
    text = ['all lowercase 8mo', 'mess          16d']
    with Image.open("./helpers/test_assets/Test_03.png") as answer:
        out_path = "./helpers/test_output/Test_03.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=1, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[1]
        assert test[2] == 1

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
        out_path = "./helpers/test_output/Test_04.png"
        test = hlp.draw_text_best_parameters(params_order=custom_wrap_parameters_1, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=None, wrap_text=True)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == custom_wrap_parameters_1[5]
        assert test[2] == -1

    # test a message that is too long with the default placeholder
    with Image.open("./helpers/test_assets/Test_05.png") as answer:
        out_path = "./helpers/test_output/Test_05.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=None, wrap_text=True)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[5]
        assert test[2] == -1

    # test a message that fits in a medium font
    text = "I call it a bargain: the best I ever had"
    with Image.open("./helpers/test_assets/Test_06.png") as answer:
        out_path = "./helpers/test_output/Test_06.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=None, wrap_text=True)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[2]
        assert test[2] == 3

    # test a message that fits in a large font
    text = "A doo-da-ee!!"
    with Image.open("./helpers/test_assets/Test_07.png") as answer:
        out_path = "./helpers/test_output/Test_07.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align='center', text_align='center',
                                             fixed_spacing=None, wrap_text=True)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[1]
        assert test[2] == 1

    # test a message that does not fit, with wrap_text=False (gets to end of params_order)
    # check message written matches and also that a message is written to the log
    text = "\n".join(["O mar ta bonito ta cheio de caminho pedala",
                      "pedala pedala pedalinho. me leva pra longe bem",
                      "devagarinho lorem ipsum lorem ipsum lorem ipsum"])
    log_text = "draw_text_best_parameters reached end of params_order without fitting, text: " + text
    with Image.open("./helpers/test_assets/Test_08.png") as answer:
        out_path = "./helpers/test_output/Test_08.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align='center', horizontal_align=0, text_align='left',
                                             fixed_spacing=None, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[5]
        assert test[2] == -1
    assert caplog.records[-1].getMessage() == log_text

    # test simple weather stub at large size
    weather_stub_size = (58, 21)
    text = "Rio"
    with Image.open("./helpers/test_assets/Test_09.png") as answer:
        out_path = "./helpers/test_output/Test_09.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=weather_stub_size,
                                             text=text, vertical_align='center', horizontal_align='center',
                                             text_align='left', fixed_spacing=None, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[0]
        assert test[2] == 1

    # test longer case which needs line breaks, with and without the break_long_words kwarg
    text = 'Boulder'
    with Image.open("./helpers/test_assets/Test_10.png") as answer:
        out_path = "./helpers/test_output/Test_10.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=weather_stub_size,
                                             text=text, vertical_align='center', horizontal_align=0,
                                             text_align='left', fixed_spacing=None, wrap_text=True)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == default_wrap_parameters[1]
        assert test[2] == 2

    custom_wrap_parameters_2 = (hlp.wrap_parameter_set(press_start_path, 16, 1, False, False, {}),
                                hlp.wrap_parameter_set(press_start_path, 9, 1, False, False,
                                                       {'break_long_words': False}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, False, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, False, {}),
                                hlp.wrap_parameter_set(dat_dot_path, 8, -2, True, True, {}))
    with Image.open("./helpers/test_assets/Test_11.png") as answer:
        out_path = "./helpers/test_output/Test_11.png"
        test = hlp.draw_text_best_parameters(params_order=custom_wrap_parameters_2, bbox_size=weather_stub_size,
                                             text=text, vertical_align='center', horizontal_align='center',
                                             text_align='left', fixed_spacing=None, wrap_text=True)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert test[1] == custom_wrap_parameters_2[2]
        assert test[2] == -2


def test_draw_text_parameters_log_error():
    # previously if a list was provided and the message did not fit, the log errored out
    date_message_wrap_params = hlp.wrap_parameter_set(font_path=press_start_path, font_size=9, min_spacing=1,
                                                      split_words=False, truncate=True, wrap_kwargs={})
    date_message_text_kws = {'params_order': [date_message_wrap_params],
                             'vertical_align': 'center', 'horizontal_align': 'center', 'text_align': 'center',
                             'fixed_spacing': 1, 'wrap_text': False}
    msg = ["123456789012345 2mo", "ABCDEFGHIJKLMNO 14d"]

    # next line originally returned error due to issue in log writing
    _, _, _ = hlp.draw_text_best_parameters(text=msg, bbox_size=(168, 21), **date_message_text_kws)


def test_vertical_horizontal_align(caplog):
    full_sign_size = (168, 21)
    # test a standard calendar-type message
    text = ['Retorno às    5d ', 'Aulas Day     16h']
    with Image.open("./helpers/test_assets/Test_Align_01.png") as answer:
        out_path = "./helpers/test_output/Test_Align_01.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align=0, horizontal_align=0, text_align='center',
                                             fixed_spacing=1, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    with Image.open("./helpers/test_assets/Test_Align_02.png") as answer:
        out_path = "./helpers/test_output/Test_Align_02.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align=1, horizontal_align=2, text_align='center',
                                             fixed_spacing=1, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    with Image.open("./helpers/test_assets/Test_Align_03.png") as answer:
        out_path = "./helpers/test_output/Test_Align_03.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align=2, horizontal_align=4, text_align='center',
                                             fixed_spacing=1, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    with Image.open("./helpers/test_assets/Test_Align_04.png") as answer:
        out_path = "./helpers/test_output/Test_Align_04.png"
        test = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                             vertical_align=10, horizontal_align=60, text_align='center',
                                             fixed_spacing=1, wrap_text=False)
        test[0].save(out_path)
        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
        assert caplog.records[-1].getMessage() == \
               "Horizontal align provided pushes drawn text off image.  Text:" + str(text)
        assert caplog.records[-2].getMessage() == \
               "Vertical align provided pushes drawn text off image.  Text:" + str(text)


def test_text_list_wrap_text_true():
    full_sign_size = (168, 21)
    # test a message that fits in a medium font
    text = ["I call it a bargain:", "the best I ever had"]

    error_text = "wrap_text must be False if text is passed as list."
    with pytest.raises(ValueError, match=error_text):
        _ = hlp.draw_text_best_parameters(params_order=default_wrap_parameters, bbox_size=full_sign_size, text=text,
                                          vertical_align='center', horizontal_align='center', text_align='center',
                                          fixed_spacing=None, wrap_text=True)
