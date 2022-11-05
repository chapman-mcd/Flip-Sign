import flip_sign.helpers
from PIL import ImageFont

press_start_path = r'../flip_sign/assets/fonts/PressStart2P.ttf'
dat_dot_path = r'../flip_sign/assets/fonts/DatDot_edited_v1.ttf'


def test_bbox_text_no_truncation():
    # test a message that fits in a standard font size (full sign resolution)
    full_sign_size = (168, 21)
    font_1 = ImageFont.truetype(press_start_path, size=8)
    text = "Does this two-line text fit to start?"
    answer = (True, ['Does this two-line', 'text fit to start?'])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_1, align='left') == answer

    # test a message that doesn't fit, in a standard font size (full sign resolution)
    text = "I think this text is just a little bit too long to fit."
    answer = (False, [])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_1, align='left') == answer

    # test a message that fits in a large font size (full sign resolution)
    text = 'A doo-da-ee!'
    answer = (True, ['A doo-da-ee!'])
    font_2 = ImageFont.truetype(press_start_path, size=14)
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_2, align='left') == answer

    # test a message that doesn't fit in a large font size (full sign resolution)
    text = 'My font is too big.'
    answer = (False, [])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_2, align='left') == answer

    # test a message that fits in a large font size (weather stub resolution) - e.g. "Rio"
    weather_stub_size = (58, 21)
    text = 'Rio'
    font_3 = ImageFont.truetype(press_start_path, size=16)
    answer = (True, ['Rio'])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_3, align='left') == answer

    # test a message that doesn't fit in a large font size (weather stub resolution) - e.g. "Boulder"
    text = 'Boulder'
    answer = (False, [])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_3, align='left') == answer

    # test a message that fits in a small font size (weather stub resolution) - e.g. "Boulder"
    font_4 = ImageFont.truetype(dat_dot_path, size=7)
    answer = (True, ['Boulder'])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_4, align='left') == answer

    # test a message that does not fit with split_words=False but does fit with split_words=True
    text = "Split_words is essential with long words"
    answer = (False, [])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_1, align='left') == answer

    answer = (True, ['Split_words is essent', 'ial with long words'])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                     split_words=True, font=font_1, align='left') == answer

    # test the use of break_long_words=False and True
    font_5 = ImageFont.truetype(press_start_path, size=9)
    answer = (True, ['Boulde', 'r'])
    text = 'Boulder'
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_5, align='left') == answer

    answer = (False, [])
    assert flip_sign.helpers.bbox_text_no_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                     split_words=False, font=font_5, align='left',
                                                     break_long_words=False) == answer


def test_bbox_text_truncation():
    # same testa as without truncation, just the answers are different.
    # test a message that fits in a standard font size (full sign resolution)
    full_sign_size = (168, 21)
    font_1 = ImageFont.truetype(press_start_path, size=8)
    text = "Does this two-line text fit to start?"
    answer = (True, ['Does this two-line', 'text fit to start?'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_1, align='left') == answer

    # test a message that doesn't fit, in a standard font size (full sign resolution)
    text = "I think this text is just a little bit too long to fit."
    answer = (True, ['I think this text is', 'just a little bit [...]'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_1, align='left') == answer

    # test a message that fits in a large font size (full sign resolution)
    text = 'A doo-da-ee!'
    answer = (True, ['A doo-da-ee!'])
    font_2 = ImageFont.truetype(press_start_path, size=14)
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_2, align='left') == answer

    # test a message that doesn't fit in a large font size (full sign resolution)
    text = 'My font is too big.'
    answer = (True, ['My font [...]'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_2, align='left') == answer

    # test a message that fits in a large font size (weather stub resolution) - e.g. "Rio"
    weather_stub_size = (58, 21)
    text = 'Rio'
    font_3 = ImageFont.truetype(press_start_path, size=16)
    answer = (True, ['Rio'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_3, align='left',
                                                  placeholder='..') == answer

    # test a message that doesn't fit in a large font size (weather stub resolution) - e.g. "Boulder"
    # in this case still doesn't fit because default placeholder is too big
    text = 'Boulder'
    answer = (False, [])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_3, align='left') == answer

    # add another case with a shorter placeholder that fits now
    text = 'Boulder'
    answer = (True, ['..'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_3, align='left',
                                                  placeholder='..') == answer

    # test a message that fits in a small font size (weather stub resolution) - e.g. "Boulder"
    font_4 = ImageFont.truetype(dat_dot_path, size=7)
    answer = (True, ['Boulder'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_4, align='left') == answer

    # test a message that does not fit with split_words=False but does fit with split_words=True
    text = "Split_words is essential with long words"
    answer = (True, ['Split_words is', 'essential with [...]'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_1, align='left') == answer

    answer = (True, ['Split_words is essent', 'ial with long words'])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                  split_words=True, font=font_1, align='left') == answer

    # test the use of break_long_words=False and True
    font_5 = ImageFont.truetype(press_start_path, size=9)
    answer = (True, ['Boulde', 'r'])
    text = 'Boulder'
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_5, align='left') == answer

    answer = (False, [])
    assert flip_sign.helpers.bbox_text_truncation(bbox_size=weather_stub_size, line_spacing=1, text=text,
                                                  split_words=False, font=font_5, align='left',
                                                  break_long_words=False) == answer


def test_check_bbox_no_wrap():
    # test a message that barely fits
    full_sign_size = (168, 21)
    text = "\n".join(['You wrote a note with chalk on my door,',
                      "a message I'd known long before:",
                     "'On any given day you'll find me gone'"])
    answer = (True, text)
    font_1 = ImageFont.truetype(dat_dot_path, size=8)
    assert flip_sign.helpers.check_bbox_no_wrap(bbox_size=full_sign_size, line_spacing=-2, text=text,
                                                font=font_1, align='center') == answer

    # test a message that does not fit
    font_2 = ImageFont.truetype(press_start_path, size=8)
    text = "My text is too big.  My text is TOO BIG."
    answer = (False, [])
    assert flip_sign.helpers.check_bbox_no_wrap(bbox_size=full_sign_size, line_spacing=1, text=text,
                                                font=font_2, align='center') == answer
