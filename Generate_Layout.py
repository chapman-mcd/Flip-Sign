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
                    output[(j+7*z, i+28*x)] = (z+3*x, 27-i, j)
    return output
