import flip_sign.message_generation as msg_gen
import random
from PIL import ImageChops, Image


def simple_transition(first_message: msg_gen.Message, second_message: msg_gen.Message):
    """
    Does the simplest possible transition - a direct flip over to the new message.

    :param first_message: (Message) the message currently displayed on the sign
    :param second_message: (Message) the new message to display on the sign
    :return: (list) the image states between the old and new message objects
    """

    return [second_message.get_image()]


def dissolve_changes_only(first_message: msg_gen.Message, second_message: msg_gen.Message):
    """
    Dissolves between the two messages, one pixel at a time.

    :param first_message: (Message) the message currently displayed on the sign
    :param second_message: (Message) the new message to display on the sign
    :return: (list) the image states between the old and new message objects
    """


    current_image = first_message.get_image().copy()
    desired_image = second_message.get_image()

    # generate a shuffled list of column, row addresses
    pixel_addresses = []
    for column in range(current_image.size[0]):
        for row in range(current_image.size[1]):
            pixel_addresses.append((column, row))
    random.shuffle(pixel_addresses)

    images_out = []

    for pixel in pixel_addresses:
        desired_pixel = desired_image.getpixel(pixel)
        if not current_image.getpixel(pixel) == desired_pixel:
            current_image.putpixel(pixel, desired_pixel)
            images_out.append(current_image.copy())

    return images_out


def select_transition_function(first_message: msg_gen.Message, second_message: msg_gen.Message):
    """
    Selects an appropriate transition function based on the message subtypes.  Currently just randomly chooses between
    two types.

    :param first_message: (Message) the message currently displayed on the sign
    :param second_message: (Message) the new message to display on the sign
    :return: (callable) a transition function that can be used on the two objects
    """

    return random.choice([simple_transition, dissolve_changes_only])