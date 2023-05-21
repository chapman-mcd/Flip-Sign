from serial import Serial
from flip_sign.message_generation import ImageMessage
import flip_sign.transitions as transitions
from urllib.error import URLError
from PIL import Image
import copy
import struct
import logging
import time

logger_name = 'flip_sign.displays'
displays_logger = logging.getLogger(logger_name)


def generate_layout():
    """
    Generates a layout dictionary for the main sign project, according to the layout spec.
    :return: Dictionary, indicating the pixel layout of the sign
    """
    output = {}
    for x in range(6):
        for z in range(3):
            for i in range(28):
                for j in range(7):
                    output[(j+7*z, i+28*x)] = (z+3*x, 27-i, 6-j)
    return output


def generate_addresses():
    """
    Generates a list of all display addresses
    :return: a list of display addresses in the flip dot display
    """
    addr = [b'']*18
    addr[0] = b'\x00'
    addr[1] = b'\x01'
    addr[2] = b'\x02'
    addr[3] = b'\x03'
    addr[4] = b'\x04'
    addr[5] = b'\x05'
    addr[6] = b'\x06'
    addr[7] = b'\x07'
    addr[8] = b'\x08'
    addr[9] = b'\x09'
    addr[10] = b'\x0A'
    addr[11] = b'\x0B'
    addr[12] = b'\x0C'
    addr[13] = b'\x0D'
    addr[14] = b'\x0E'
    addr[15] = b'\x0F'
    addr[16] = b'\x10'
    addr[17] = b'\x11'

    return addr


def reset_command():
    """
    Returns a command that can be sent to the display to turn all dots white
    :return: a binary string command that sets all dots white
    """

    head = b'\x80'
    cmd = b'\x84'
    tail = b'\x8F'
    refreshcmd = b'\x82'

    result = b''

    for address in generate_addresses():
        result += head + cmd + address + b'\x7F'*28 + tail

    result += head + refreshcmd + tail

    return result


def all_black_command():
    """
    Returns a command that can be sent to the display to turn all dots black
    :return: a binary string command that sets all dots black
    """

    head = b'\x80'
    cmd = b'\x84'
    tail = b'\x8F'
    refreshcmd = b'\x82'

    result = b''

    for address in generate_addresses():
        result += head + cmd + address + b'\x00'*28 + tail

    result += head + refreshcmd + tail

    return result


class FlipDotDisplay(object):
    """
    A FlipDotDisplay is a rectangular array of flip-dot displays from AlfaZeta, arranged in an arbitrary layout.
    """
    def __init__(self, serial_interface: Serial):
        """
        Initializes the display.
        :param serial_interface: (serial.Serial) the serial interface to be written to for display updates
        """
        self.serial_interface = serial_interface

        self.rows = 21
        self.columns = 168
        self.layout = generate_layout()
        self.serial_interface = serial_interface
        self.invert = False

        # determine indices of displays and number of bytes
        # display is a dictionary of the displays, indexed by their identifier
        # each element of the dictionary is an integer (number of bytes)
        # this loop determines the largest bytenum for each display
        display = {}
        for pixel in self.layout:
            if self.layout[pixel][0] in display:
                if self.layout[pixel][1] > display[self.layout[pixel][0]]:
                    display[self.layout[pixel][0]] = self.layout[pixel][1]
            else:
                display[self.layout[pixel][0]] = self.layout[pixel][1]
        # turn the display dictionary into a dictionary of lists, each list the length of the bytes in the display
        # default empty state is 0 (all pixels in column black)
        for disp in display:
            temp = display[disp]
            display[disp] = [0] * (temp + 1)
        self.empty_state = copy.deepcopy(display)

        # initialize current state to all black and then set the display to it
        self.current_message = ImageMessage(image=Image.new('1', (self.columns, self.rows), 0))
        self.current_state = self.current_message.get_image()
        self.show(self.current_state)

    def show(self, image: Image.Image):
        """
        Updates the display to show the provided image.

        :param image: (PIL.Image.Image) the image to display
        :return: None
        """

        # turn new image into a list of lists, with desiredstate[row][column] returning the pixel direction
        image_data = list(image.getdata())
        pixels = [image_data[i * self.columns: (i + 1) * self.columns] for i in range(self.rows)]
        # start with generic command strings
        head = b'\x80'
        tail = b'\x8F'
        cmd = b'\x84'
        refresh = head + b'\x82' + tail
        cmd_string = b''

        display = copy.deepcopy(self.empty_state)
        # first need to use self.layout to turn the pixels array into the display IDs and byte values
        # iterate through all the rows and columns in the desired state
        for row in range(len(pixels)):
            for column in range(len(pixels[row])):
                # sometimes white will be 255, sometimes it will be 1
                # this code needs white to be 1 for calculation purposes
                # sanitize 255 into 1, or just use as is
                if pixels[row][column] == 255:
                    pixel = 1
                else:
                    pixel = pixels[row][column]

                # if display is inverted, turn 1 into 0 and vice versa, otherwise leave as is
                if self.invert:
                    pixel = 1 - pixel

                # display[displaynum from layout] [ bytenum from layout] incremented by the pixels value * power
                # of 2 from layout
                display[self.layout[(row, column)][0]][self.layout[(row, column)][1]] += \
                    pixel * 2 ** self.layout[(row, column)][2]

        # iterate through the displays and turn them into the proper byte arrays
        for disp in display:
            # start off each command with a head and command string
            # add the display address
            # to generate bytes for the address, use struct.pack('=b',ADDRESS)
            # add the actual command string- use the bytearray function to turn the list of integers into the byte array
            cmd_string += head + cmd + struct.pack('=b', disp) + bytearray(display[disp]) + tail

        # once done, add the refresh command to the end of the command string
        cmd_string += refresh

        # write the command to the serial interface
        self.serial_interface.write(cmd_string)

    def update(self, next_message):
        """
        Updates the display with the desired next_message.

        :param next_message: (Message) the message to display on the sign
        :return: (bool) whether the update was successful
        """

        try:
            next_message.render()
        except (ValueError, URLError) as e:
            displays_logger.warning("Error rendering message.")
            displays_logger.warning("Full error: " + str(e))
            return False

        transition_function = transitions.select_transition_function(self.current_message, next_message)

        for state in transition_function(self.current_message, next_message):
            self.show(image=state)

        self.current_message = next_message
        self.current_state = next_message.get_image()

        return True

    def cycle_dots(self):
        """
        Display all black, then all yellow, then all black again.  Used at end of cycle to make sure
        all pixels get some exercise.

        :return: None
        """

        self.show(image=Image.new('1', (168, 21), 0))
        time.sleep(0.5)
        self.show(image=Image.new('1', (168, 21), 1))
        time.sleep(0.5)
        self.show(image=Image.new('1', (168, 21), 0))
        time.sleep(0.5)
        self.current_message = ImageMessage(image=Image.new('1', (self.columns, self.rows), 0))
        self.current_state = self.current_message.get_image()
