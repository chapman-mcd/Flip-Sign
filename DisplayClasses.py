from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from TransitionFunctions import *
import copy
import struct
import serial
from MessageClasses import *



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
    def __init__(self, rows, columns, serialinterface, layout):
        """
        Initializes the display.
        :param rows: Integer number of rows in the display
        :param columns: Integer number of columns in the display
        :param layout: A dictionary, with keys being (row,column) tuples.  layout[(row,column)]
                        should return a tuple (displayID,bytenum,powerof2)
        :param serialinterface: A python serial module object, representing the serial interface of the actual display
        """
        # Make sure variables are of the right type.  For layout, only make sure it has the right dimensions
        assert type(rows) == int
        assert type(columns) == int
        assert isinstance(serialinterface, serial.Serial)

        self.rows = rows
        self.columns = columns
        self.layout = copy.deepcopy(layout)
        self.serial = serialinterface
        self.invert = False

        # determine indices of displays and number of bytes
        # display is a dictionary of the displays, indexed by their identifier
        # each element of the dictionary is an integer (number of bytes)
        # this loop determines the largest bytenum for each display
        display = {}
        for pixel in layout:
            if layout[pixel][0] in display:
                if layout[pixel][1] > display[layout[pixel][0]]:
                    display[layout[pixel][0]] = layout[pixel][1]
            else:
                display[layout[pixel][0]] = layout[pixel][1]
        # turn the display dictionary into a dictionary of lists, each list the length of the bytes in the display
        # default empty state is 0 (all pixels in column black)
        for disp in display:
            temp = display[disp]
            display[disp] = [0]*(temp + 1)
        self.emptystate = copy.deepcopy(display)

        # initialize current state to all black and then set the display to it
        self.currentstate = Image.new('1',(self.columns,self.rows),0)
        self.show(self.currentstate)
        self.currentmessage = None

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
        :param desiredstate: a PIL image object, of dimensions (rows,columns)
        :return: None
        """
        # to optimize time, only going to check if the first row has the proper number of columns
        assert (self.columns, self.rows) == desiredstate.size

        # turn desiredstate into a list of lists, with desiredstate[row][column] returning the pixel direction
        pixel = list(desiredstate.getdata())
        pixels = [pixel[i * self.columns : (i + 1) * self.columns] for i in range(self.rows)]
        # start with generic command strings
        head = b'\x80'
        tail = b'\x8F'
        cmd = b'\x84'
        refresh = head + b'\x82' + tail
        cmdstring = b''

        display = copy.deepcopy(self.emptystate)
        # first need to use self.layout to turn the pixels array into the display IDs and byte values
        # iterate through all the rows and columns in the desired state
        for row in range(len(pixels)):
            for column in range(len(pixels[row])):
                # if display is inverted, turn 1 into 0 and vice versa, otherwise leave as is
                if self.invert:
                    pixel = 1 - pixels[row][column]
                else:
                    pixel = pixels[row][column]

                # display[displaynum from layout] [ bytenum from layout] incremented by the pixels value * power
                # of 2 from layout
                display[self.layout[(row, column)][0]][self.layout[(row, column)][1]] +=\
                    pixel * 2 ** self.layout[(row, column)][2]

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

    def update(self, transitionfunction, displayobject, font=ImageFont.truetype('/Users/cmcd/PycharmProjects/Sign/PressStart2P.ttf', size=9)):
        # Ensure proper types
        assert isinstance(displayobject, Message) or isinstance(displayobject, Image.Image)
        if isinstance(displayobject, Message):
            assert isinstance(font, ImageFont.FreeTypeFont)
        assert callable(transitionfunction)
        assert transitionfunction.is_message_transition or transitionfunction.is_display_transition

        displaystates = []

        # if an image
        if isinstance(displayobject, Image.Image):
            # either crop it to fit the display (keep top left) or pad to fill (center)
            # first check if either of the dimensions are too big
            if displayobject.size[0] > self.columns or displayobject.size[1] > self.rows:
                horizontalcrop = max(displayobject.size[0] - self.columns, 0)
                verticalcrop = max(displayobject.size[1] - self.rows, 0)
                image_for_transition = displayobject.crop((0 + horizontalcrop // 2, 0 + verticalcrop // 2,
                                                    displayobject.size[0] - horizontalcrop // 2 - horizontalcrop % 2,
                                                    displayobject.size[1] - verticalcrop // 2 - verticalcrop % 2))
            # now that any cropping has been done, need to check if the image needs to be padded
            if image_for_transition.size[0] < self.columns or displayobject.size[1] < self.rows:
                image_for_transition = pad_image(displayobject, self.rows, self.columns, fill=0)

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

            # set foundissue to true to ensure we check at least once
            foundissue = True
            # purpose of this loop is to check ensure we get a message that fits in the display
            # the initial estimate of the number of characters is a guess - because some fonts do not have the same
            # width for each character, the actual size taken up can depend on the message
            # so, we check if the message fits.  if it doesn't, we honor the font size provided and reduce the amount
            # of space available for the message
            while foundissue:
                # tell the message to update with the estimated number of characters
                displayobject.update(num_lines=display_height_chars, num_chars=display_width_chars)
                totalheight = 0
                maxwidth = 0
                foundissue = False
                # determine max dimensions of the image
                for line in displayobject.get_message():
                    width, height = font.getsize(line)
                    totalheight += height
                    maxwidth = max(maxwidth, width)
                # check against maximum display dimensions and update the "message size" if necessary
                if maxwidth > self.columns:
                    foundissue = True
                    display_width_chars = int(display_width_chars * self.columns / maxwidth)
                if totalheight > self.rows:
                    foundissue = True
                    display_height_chars = int(display_height_chars * self.rows / totalheight)
            # at the end of the loop, totalheight and maxwidth should contain the actual values for the message

            # if the provided transition function is messagetransition, apply it here to generate a message states list
            # then turn those message states into display states
            # otherwise, create a single-item list that is just the eventual message
            if transitionfunction.is_message_transition:
                # try to use transition function - if we get an assertion error, that means the current display state
                # is an image, so a message transition is not possible
                try:
                    messagestates = transitionfunction(self.currentmessage,displayobject.get_message())
                except AssertionError:
                    messagestates = [displayobject.get_message()]
                # since our function is a message function, we create the displaystates list here
                for messagestate in messagestates:
                    image = message_to_image(messagestate, self.columns, self.rows, maxwidth, totalheight,
                                             font, display_height_chars)
                    displaystates.append(image)
            # since our function is not a message function, we just make the message into an image for transition
            else:
                image_for_transition = message_to_image(displayobject.get_message(), self.columns, self.rows, maxwidth,
                                                        totalheight, font, display_height_chars)
            # write the message output to the self.currentmessage container, so future message transitions can work
            self.currentmessage = displayobject.get_message()

        else: # it's not a message or an image - technically this should not be possible because of the asserts
            raise AssertionError("Assertion not working")

        # if the provided transition function is a displaytransition, then use the transition function to generate
        # desired display states
        if transitionfunction.is_display_transition:
            displaystates = transitionfunction(self.currentstate, image_for_transition)

        # if we get this far and displaystates is still an empty list, then
        # we got an image to display, but combined with a message transition.  just use simpletransition
        if displaystates == []:
            displaystates = SimpleTransition(self.currentstate, image_for_transition)


        # show the desired states on the display
        for state in displaystates:
            self.show(state)

        self.currentstate = displaystates[-1]

class FakeFlipDotDisplay(FlipDotDisplay):
    def __init__(self, rows, columns, serialinterface, layout):
        self.file_number = 1
        FlipDotDisplay.__init__(self, rows, columns, serialinterface, layout)

    def show(self, desiredstate):
        desiredstate.format = 'PNG'
        statepath = '/Users/cmcd/PycharmProjects/SignStorage/'
        desiredstate.save(statepath + str(self.file_number) + '.PNG',format='PNG')
        self.file_number += 1

def pad_image(Image,rows,columns,fill=0):
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


def initialize_row_spacing_lookup():
    """
    Could not determine an algorithm for how to space the lines, so going to use a lookup table.
    lookuptable[num_lines][extra_spaces] will contain a tuple (top,per_line) which indicates how many spaces go
    at the top and how many go between each line.
    :return: a lookup table, which is a list of lists of tuples.
    """
    output = [[None]*7 for i in range(5)]
    output[3][0] = (0, 0)
    output[3][1] = (0, 0)
    output[3][2] = (0, 1)
    output[3][3] = (0, 1)
    output[3][4] = (1, 1)
    output[3][5] = (1, 1)
    output[2][0] = (0, 0)
    output[2][1] = (0, 1)
    output[2][2] = (0, 1)
    output[2][3] = (1, 1)
    output[2][4] = (1, 2)
    output[2][5] = (1, 2)
    return output

def message_to_image(message,columns,rows,max_width,total_height, font, display_height_chars):
    image = Image.new('1', (columns, rows), 0)
    # calculate x position to write the lines to - this is easy since it's just centering the stuff
    xposition = (columns - max_width) // 2
    # calculate y position and spacing - more difficult since there are multiple lines and spacing between
    total_y_space = rows - total_height
    yposition, per_line = initialize_row_spacing_lookup()[display_height_chars][total_y_space]
    line_height = font.getsize('A')[1]
    # iterate through the lines in the message, writing each line at the right position and then
    # incrementing the position
    for i in range(len(message)):
        ImageDraw.Draw(image).text((xposition, yposition), message[i], fill=1, font=font)
        yposition += line_height + per_line
    return image