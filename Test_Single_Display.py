from MessageClasses import *
from DisplayClasses import *
import serial

def Generate_Layout_1():
    """
    Generates a layout dictionary for a single 28x14 display, according to the layout specifications.
    :return:
    """
    output = {}
    #first display
    for i in range(28):
        for j in range(7):
            output[(j, i)] = (1, i, j)

    #second display
    for i in range(28):
        for j in range(7):
            output[(j+7, i)] = (2, i, j)
    return output

z = Generate_Layout_1()

port = '/dev/ttyS0'

serialinterface = serial.Serial(port=port, baudrate=57600, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS,
                                timeout=1, stopbits=serial.STOPBITS_ONE)

Display = FlipDotDisplay(14, 28, serialinterface=serialinterface, layout=Generate_Layout_1())

while True:
    test = []
    test.append(BasicTextMessage('TEST test'))
    test.append(BasicTextMessage('HELLO WORLD'))
    test.append(BasicTextMessage('FLIP DOTS'))

    for msg in test:
        Display.update(SimpleTransition, msg,
                       font=ImageFont.truetype('/Users/cmcd/PycharmProjects/Sign/PressStart2P.ttf', size=7))