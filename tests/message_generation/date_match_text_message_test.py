from flip_sign.message_generation import DateMatchTextMessage
from tests.helpers.draw_text_test import image_equal
from PIL import Image


def test_date_match_message():
    # test a song lyric to confirm it prints like a date message
    with Image.open('./message_generation/test_assets/Test_DateMatch_01.png') as answer:
        out_path = './message_generation/test_output/Test_DateMatch_01.png'
        test_msg = DateMatchTextMessage(text="O mar tá bonito tá cheio de caminho", frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # print an actual date message and compare to test output from the DateMessage class
    with Image.open('./message_generation/test_assets/Test_03.png') as answer:
        out_path = './message_generation/test_output/Test_DateMatch_02.png'
        test_msg = DateMatchTextMessage(text="Trip to Uranus Now\nand Neptune", frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)
