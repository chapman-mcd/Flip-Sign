from flip_sign.helpers import render_day
from flip_sign.assets import root_dir
from PIL import Image
from tests.helpers.draw_text_test import image_equal


def test_render_day():
    # random stuff
    with Image.open(root_dir + "/../tests/helpers/test_assets/Test_Render_Day_01.png") as answer:
        out_path = root_dir + "/../tests/helpers/test_output/Test_Render_Day_01.png"
        render_day(40, 10, 0.2, 1, "cloudy").save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # provide floats for temps
    with Image.open(root_dir + "/../tests/helpers/test_assets/Test_Render_Day_02.png") as answer:
        out_path = root_dir + "/../tests/helpers/test_output/Test_Render_Day_02.png"
        render_day(39.8, 9.9, 0.0, 2, "sunny").save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # negative temps
    with Image.open(root_dir + "/../tests/helpers/test_assets/Test_Render_Day_03.png") as answer:
        out_path = root_dir + "/../tests/helpers/test_output/Test_Render_Day_03.png"
        render_day(-5, -7, 0.5, 3, "snow").save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # high precipitation
    with Image.open(root_dir + "/../tests/helpers/test_assets/Test_Render_Day_04.png") as answer:
        out_path = root_dir + "/../tests/helpers/test_output/Test_Render_Day_04.png"
        render_day(25, 10, 0.9, 4, "rain").save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
