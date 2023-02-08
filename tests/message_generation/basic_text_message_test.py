from flip_sign.message_generation import BasicTextMessage, basic_text_default_wrap_params
from tests.helpers.draw_text_test import image_equal
from PIL import Image


# what is this even testing?
# this class is essentially just a wrapper on the text drawing function

# test 1-2 messages that use the entire draw stack
# make up messages that use each level of the stack?

def test_basic_text_message():
    # test giant message passed as string (gets largest font)
    with Image.open('./message_generation/test_assets/Test_Basic_01.png') as answer:
        out_path = './message_generation/test_output/Test_Basic_01.png'
        text = "You"
        test_msg = BasicTextMessage(text=text, frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)
        assert test_msg.applied_params == basic_text_default_wrap_params[0]

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # second largest font
    with Image.open('./message_generation/test_assets/Test_Basic_02.png') as answer:
        out_path = './message_generation/test_output/Test_Basic_02.png'
        text = "You wrote a"
        test_msg = BasicTextMessage(text=text, frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)
        assert test_msg.applied_params == basic_text_default_wrap_params[1]

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)


    # third largest font
    with Image.open('./message_generation/test_assets/Test_Basic_03.png') as answer:
        out_path = './message_generation/test_output/Test_Basic_03.png'
        text = "You wrote a note with chalk on my"
        test_msg = BasicTextMessage(text=text, frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)
        assert test_msg.applied_params == basic_text_default_wrap_params[2]

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)



    # fourth largest font (smallest with PressStart2P)
    with Image.open('./message_generation/test_assets/Test_Basic_04.png') as answer:
        out_path = './message_generation/test_output/Test_Basic_04.png'
        text = "You wrote a note with chalk on my door"
        test_msg = BasicTextMessage(text=text, frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)
        assert test_msg.applied_params == basic_text_default_wrap_params[3]

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test full song lyric with wrap_text = True
    text = "\n".join(['You wrote a note with chalk on my door,',
                      "a message I'd known long before:",
                      "'On any given day you'll find me gone'"])
    with Image.open('./message_generation/test_assets/Test_Basic_05.png') as answer:
        out_path = './message_generation/test_output/Test_Basic_05.png'

        test_msg = BasicTextMessage(text=text, frequency=1)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

    # test full song lyric with wrap_text = False
    # passed as string with newlines and as list
    with Image.open('./helpers/test_assets/Test_01.png') as answer:
        out_path = './message_generation/test_output/Test_Basic_06.png'
        text = "\n".join(['You wrote a note with chalk on my door,',
                          "a message I'd known long before:",
                         "'On any given day you'll find me gone'"])
        test_msg = BasicTextMessage(text=text, frequency=1, wrap_text=False)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)

        text = ['You wrote a note with chalk on my door,',
                "a message I'd known long before:",
                "'On any given day you'll find me gone'"]
        test_msg = BasicTextMessage(text=text, frequency=1, wrap_text=False)
        test_msg.render()
        test_msg.get_image().save(out_path)

        with Image.open(out_path) as test_result:
            assert image_equal(answer, test_result)


