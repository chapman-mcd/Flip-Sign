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


def Generate_Layout_2():
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