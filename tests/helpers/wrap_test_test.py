import flip_sign.helpers
from PIL import ImageFont
import pytest

press_start_path = r'../flip_sign/assets/fonts/PressStart2P.ttf'
dat_dot_path = r'../flip_sign/assets/fonts/DatDot_edited_v1.ttf'


def test_size_function():
    # test basic image sizing / targeting
    font_1 = ImageFont.truetype(press_start_path, size=8)
    test_text_1 = 'The quick brown fox\njumps over the lazy dog'
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_1, line_spacing=1, align='left')
    assert size == (182, 17) and draw_target == (-1, 0)

    # test different alignment (should have same result)
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_1, line_spacing=1, align='right')
    assert size == (182, 17) and draw_target == (-1, 0)

    # test different line spacing
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_1, line_spacing=5, align='left')
    assert size == (182, 21) and draw_target == (-1, 0)

    # test providing same input as list
    test_text_2 = ['The quick brown fox', 'jumps over the lazy dog']
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_2, line_spacing=1, align='left')
    assert size == (182, 17) and draw_target == (-1, 0)

    # test all on one line
    test_text_3 = 'The quick brown fox jumps over the lazy dog'
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_3, line_spacing=1, align='left')
    assert size == (342, 8) and draw_target == (-1, 0)

    # test a large number of lines
    test_text_4 = test_text_3.replace(" ", '\n')
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_4, line_spacing=1, align='left')
    assert size == (39, 80) and draw_target == (0, 0)

    # test different size
    font_2 = ImageFont.truetype(press_start_path, size=18)
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_2, text=test_text_1, line_spacing=1, align='left')
    assert size == (410, 38) and draw_target == (-2, 1)

    # test a different font
    font_3 = ImageFont.truetype(dat_dot_path, size=8)
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_3, text=test_text_1, line_spacing=1, align='left')
    assert size == (91, 14) and draw_target == (-1, -3)

    # test a text which contains all characters in brazilian portuguese
    test_text_5 = 'À noite, vovô Kowalsky vê o ímã cair\nno pé do pinguim queixoso e vovó\n'\
                  'põe açúcar no chá de\ntâmaras do jabuti feliz.'
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_1, text=test_text_5, line_spacing=1, align='left')
    assert size == (287, 35) and draw_target == (0, 0)

    # test a font too large for the base canvas size
    font_4 = ImageFont.truetype(press_start_path, size=90)
    size, draw_target = flip_sign.helpers.text_bbox_size(font=font_4, text=test_text_5, line_spacing=1, align='left')
    assert size == (3229, 364) and draw_target == (0, 1)

    # test a font too large overall
    font_5 = ImageFont.truetype(dat_dot_path, size=500)
    with pytest.raises(ValueError) as _:
        flip_sign.helpers.text_bbox_size(font=font_5, text=test_text_5, line_spacing=1, align='left')


def test_wrap_text_split_words():
    # test with default parameters
    text = "No man ever steps in the same river twice, for \tit is not the\t\nsame river and he is not the same man."
    answer = ['No man ever steps in',
              'the same river twice',
              ', for it is not the ',
              'same river and he is',
              'not the same man.']
    assert flip_sign.helpers.wrap_text_split_words(text=text, width=20, replace_whitespace=True,
                                                   drop_whitespace=True) == answer

    # test default with different number of columns
    answer = ['No man ever steps in the',
              'same river twice, for it',
              'is not the same river an',
              'd he is not the same man',
              '.']
    assert flip_sign.helpers.wrap_text_split_words(text=text, width=24, replace_whitespace=True,
                                                   drop_whitespace=True) == answer

    # test with replace_whitespace=False
    answer = ['No man ever steps in the',
              'same river twice, for \ti',
              't is not the\t\nsame river',
              'and he is not the same m',
              'an.']
    assert flip_sign.helpers.wrap_text_split_words(text=text, width=24, replace_whitespace=False,
                                                   drop_whitespace=True) == answer

    # test with drop_whitespace=False
    answer = ['No man ever steps in',
              ' the same river twic',
              'e, for it is not the',
              ' same river and he i',
              's not the same man.']
    assert flip_sign.helpers.wrap_text_split_words(text=text, width=20, replace_whitespace=True,
                                                   drop_whitespace=False) == answer

    # test with max_lines and default placeholder
    answer = ['No man ever steps in', 'the same river [...]']
    assert flip_sign.helpers.wrap_text_split_words(text=text, width=20, replace_whitespace=True,
                                                   drop_whitespace=True, max_lines=2) == answer

    # test with max_lines and other placeholder
    answer = ['No man ever steps in', 'the same riv[Blurgh]']
    assert flip_sign.helpers.wrap_text_split_words(text=text, width=20, replace_whitespace=True,
                                                   drop_whitespace=True, max_lines=2, placeholder='[Blurgh]') == answer

    # test with a placeholder too large to fit
    with pytest.raises(ValueError) as _:
        flip_sign.helpers.wrap_text_split_words(text=text, width=3, placeholder='[Blurgh]')
