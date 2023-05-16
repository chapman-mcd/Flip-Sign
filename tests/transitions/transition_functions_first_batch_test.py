from flip_sign.transitions import simple_transition, dissolve_changes_only, select_transition_function
from flip_sign.message_generation import DateMatchTextMessage
from PIL import ImageChops
from tests.helpers.draw_text_test import image_equal

first_message = DateMatchTextMessage(text="First test Message")
second_message = DateMatchTextMessage(text="Another test Message")

first_message.render()
second_message.render()


def test_simple_transition():
    states = simple_transition(first_message=first_message, second_message=second_message)

    assert states == [second_message.get_image()]


def test_dissolve_changes_only():
    states = dissolve_changes_only(first_message=first_message, second_message=second_message)

    assert image_equal(states[-1], second_message.get_image())  # must end with second image
    for i in range(len(states)-1):
        assert sum(list(ImageChops.difference(states[i], states[i+1]).getdata())) == 1  # only 1 pixel difference


def test_select_transition():
    assert select_transition_function(first_message=first_message, second_message=second_message) in \
           [simple_transition, dissolve_changes_only]
