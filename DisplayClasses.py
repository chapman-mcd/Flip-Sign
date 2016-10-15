from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import copy
import struct
import MessageClasses


class Display(object):
    """
    This class represents a display -- it has properties that specify its width and number of lines.
    It also has a property that represents its current state (e.g. what it is currently displaying).
    It has an update method which is fed a display object, a transition function and a delay.
    The transition function takes in a current display state and a desired display state, then returns
    a list of intermediate display states that need to be transitioned through.

    A display state is stored as a list of length num_lines that contains only strings of length num_chars.
    """
    def __init__(self, num_lines, num_chars):
        self.num_lines = num_lines
        self.num_chars = num_chars
        self.currentstate = [' '*num_chars]*num_lines

    def determine_transition(self, transitionfunction, messageobject):
        messageobject.update(num_lines=self.num_lines, num_chars=self.num_chars)
        return transitionfunction(self.currentstate, messageobject.get_message())

    def update(self, transitionfunction, messageobject):
        # this will be different for each display type, so must be overridden
        raise NotImplementedError


class SimpleDisplay(Display):
    """
    This class is the simplest display possible - it just prints the info to the console.
    """
    def __init__self(self, num_lines, num_chars):
        Display.__init__(self, num_lines, num_chars)

    def update(self, transitionfunction, messageobject):
        states = self.determine_transition(transitionfunction, messageobject)
        for i in range(len(states)):
            print(states[i])


class SerialLCDDisplay(Display):
    """
    This class is an LCD display controlled via serial -- it takes in a bytestring of length num_chars * num_lines and
    displays it.
    """
    def __init__(self, num_lines, num_chars, device, frequency, reactiontime):
        """
        :param num_lines: number of lines in the display
        :param num_chars: number of characters in each line of the display
        :param device: device location of the serial connection (e.g. '/dev/tty.usbserial')
        :param frequency: baud rate of the connection (e.g. 9600)
        :param reactiontime: delay between each update action, seconds
        """
        Display.__init__(self, num_lines, num_chars)
        self.device = device
        self.frequency = frequency
        self.reactiontime = reactiontime

    def update(self, transitionfunction, messageobject):
        import serial
        import time
        ser = serial.Serial(self.device, self.frequency)
        time.sleep(self.reactiontime)
        states = self.determine_transition(transitionfunction, messageobject)
        print("Attempting to display ", messageobject)
        for i in range(len(states)):
            output = ""
            for z in range(self.num_lines):
                output += states[i][z]
            ser.write(output.encode(encoding='us-ascii', errors='strict'))
            time.sleep(self.reactiontime)
        ser.close()


class FlipDotDisplay(Display):
    """
    This class represents a rectangular array of flip dot displays from AlfaZeta, arranged in an arbitrary layout.
    """
    def __init__(self, rows, columns, serial, layout):
        """
        Initializes the display.
        :param rows: Integer number of rows in the display
        :param columns: Integer number of columns in the display
        :param layout: A tuple of tuples of tuples, representing how to turn an array of size (rows,columns) into
        instructions for the display.  layout[rownum][colnum] should return a tuple (displayID,bytenum,powerof2)
        :param serial: A python serial module object, representing the serial interface of the actual display
        """
        # Make sure variables are of the right type.  For layout, only make sure it has the right dimensions
        assert type(rows) == int
        assert type(columns) == int
        assert isinstance(serial, serial.serial)
        assert len(layout) == rows
        for i in range(len(layout)):
            assert len(layout[i]) == columns
        self.rows = rows
        self.columns = columns
        self.layout = layout
        self.serial = serial
        self.invert = False

        # determine indices of displays and number of bytes
        # display is a dictionary of the displays, indexed by their identifier
        # each element of the dictionary is an integer (number of bytes)
        # this loop determines the largest bytenum for each display
        display = {}
        for row in layout:
            for column in row:
                if column[0] in display:
                    if column[1] > display[column[0]]:
                        display[column[0]] = column[1]
                else:
                    display[column[0]] = column[1]
        # turn the display dictionary into a dictionary of lists, each list the length of the bytes in the display
        # default empty state is 0 (all pixels in column black)
        for disp in display:
            temp = display[disp]
            display[disp] = [0]*temp
        self.emptystate = copy.deepcopy(display)

        # initialize current state to all black and then set the display to it
        self.currentstate = [[0]*self.columns for i in range(self.rows)]
        self.show(self.currentstate)

    def flip_invert(self):
        """
        Swaps display from inverted to not inverted or vice versa
        :return:
        """
        self.invert = not self.invert

    def get_invert(self):
        """
        Safe way to determine whether the display is inverted
        :return: boolean, indicating whether colors are inverted or not
        """
        return self.invert

    def show(self, desiredstate):
        """
        Writes the desired state to the display.
        :param desiredstate: a list of lists, of dimensions (rows,columns)
        :return: None
        """
        # to optimize time, only going to check if the first row has the proper number of columns
        assert len(desiredstate) == self.rows
        assert len(desiredstate[0]) == self.columns
        # start with generic command strings
        head = b'\x80'
        tail = b'x8F'
        cmd = b'x84'
        refresh = head + b'x82' + tail
        cmdstring = b''

        display = copy.deepcopy(self.emptystate)
        # first need to use self.layout to turn the desiredstate into the display IDs and byte values
        # iterate through all the rows and columns in the desired state
        for row in range(len(desiredstate)):
            for column in range(len(desiredstate(row))):
                # if display is inverted, turn 1 into 0 and vice versa, otherwise leave as is
                if self.invert:
                    pixel = 1 - desiredstate[row][column]
                else:
                    pixel = desiredstate[row][column]

                # display[displaynum from layout] [ bytenum from layout] incremented by the desiredstate value * power
                # of 2 from layout
                display[self.layout[row][column][0]][self.layout[row][column][1]] +=\
                    pixel * 2 ** self.layout[row][column][2]

        # iterate through the displays and turn them into the proper byte arrays
        for disp in display:
            # start off each command with a head and command string
            # add the display address
            # to generate bytes for the address, use struct.pack('=b',ADDRESS)
            # add the actual command string- use the bytearray function to turn the list of integers into the byte array
            cmdstring += head + cmd + struct.pack('=b', disp) + bytearray(display[disp]) + tail

        # once done, add the refresh command to the end of the command string
        cmdstring += refresh

        # write the command to the serial interface
        self.serial.write(cmdstring)

    def update(self, displayobject, transitionfunction, font='nofont'):
        # Ensure proper types
        assert isinstance(displayobject, Message) or isinstance(displayobject, Image.Image)
        if isinstance(displayobject, Message):
            assert isinstance(font, ImageFont.FreeTypeFont)
            assert callable(transitionfunction)

        # if an image
        if isinstance(displayobject, Image.Image):
            # either crop it to fit the display (keep top left) or pad to fill (center)
            # first check if either of the dimensions are too big
            if displayobject.size[0] > self.columns or displayobject.size[1] > self.rows:
                horizontalcrop = max(displayobject.size[0] - self.columns, 0)
                verticalcrop = max(displayobject.size[1] - self.rows, 0)
                displayobject = displayobject.crop((0 + horizontalcrop // 2, 0 + verticalcrop // 2,
                                                    displayobject.size[0] - horizontalcrop // 2 - horizontalcrop % 2,
                                                    displayobject.size[1] - verticalcrop // 2 - verticalcrop % 2))
            # now that any cropping has been done, need to check if the image needs to be padded
            if displayobject.size[0] < self.columns or displayobject.size[1] < self.rows:
                displayobject = PadImage(displayobject, self.rows, self.columns, fill=0)

        # if a message, we need to figure some things
        elif isinstance(displayobject,Message):
            # check the size of the phrase "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz " to see how wide
            # and tall the display is in terms of characters with the specified font
            checkwidth, checkheight = font.getsize("ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz ")
            checkwidth //= 54
            display_width_chars = self.columns // checkwidth
            display_height_chars = self.rows // checkheight
            if display_height_chars < 1 or display_width_chars < 1:
                raise ValueError("My font is too big!  My font is TOO BIG!")

            # while checkingmessagesize
                # tell the message to update with the estimated number of characters

                # turn the message into an image object with the font and font size

                # check against actual dimensions
                    # if smaller, pad the top and sides to center it

                    # if bigger re-estimate number of characters and loop

            # if the provided transition function is a messagetransition, apply it here.  otherwise, apply it later

            # convert all message states into display states

        # if the provided transition function is not a messagetransition, apply it to the desired state and display




def PadImage(Image,rows,columns,fill=0):
    """
    Takes in an image file, returns a padded image to fit the rectangle given by the rows and columns dimensions
    :param Image: A PIL image object
    :param rows: integer, number of rows of pixels
    :param columns: integer, number of columns of pixels
    :param fill: an integer 1 or 0, indicating which color to fill the padded area with (1= white, 0 = black)
    :return: A PIL image object of dimensions (rows,columns) with the provided image in the center
    """
    # create new image of the desired size, with the fill
    padded = Image.new('1',(columns,rows),fill)
    incolumns, inrows = Image.size
    if incolumns > columns or inrows > rows:
        raise ValueError("Input image must be less than or equal to the output size in all dimensions.")
    # paste provided image into created image, such that it is as centered as possible in the new area
    padded.paste(Image, ((columns - incolumns) // 2, (rows-inrows) // 2))
    return padded


def SimpleTransition(current_state,desired_state):
    """
    The simplest possible transition -- go to the desired state directly with no fancy stuff.
    :param current_state: the current display state -- ignored by this function but included for consistency with other
    transition functions.
    :param desired_state: the desired display state
    :return: in this case, just a single-element list containing the desired state
    """
    @messagetransition
    return [desired_state]

SimpleTransition.is_message_transition = True

def FlashStarsTransition(current_state,desired_state):
    """
    This transition function flashes all asterisks, then blanks, then asterisks, then the desired message.
    :param current_state: the current state of the display - again ignored by this function
    :param desired_state: the desired display state
    :return: a list containing the display states to be passed through
    """
    @messagetransition
    num_lines = len(current_state)
    num_chars = len(current_state[0])
    return [['*'*num_chars]*num_lines, [' '*num_chars]*num_lines, ['*'*num_chars]*num_lines, desired_state]

FlashStarsTransition.is_message_transition = True