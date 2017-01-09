from PIL import Image
from PIL import ImageDraw
from PIL import ImageChops
import random

def message_transition(func):
    func.is_message_transition = True
    func.is_display_transition = False

def display_transition(func):
    func.is_message_transition = False
    func.is_display_transition = True

def FlashStarsTransition(current_state,desired_state):
    """
    This transition function flashes all asterisks, then blanks, then asterisks, then the desired message.
    :param current_state: the current state of the display - again ignored by this function
    :param desired_state: the desired display state
    :return: a list containing the display states to be passed through
    """
    assert type(current_state) == list
    num_lines = len(current_state)
    num_chars = len(current_state[0])
    return [['*'*num_chars]*num_lines, [' '*num_chars]*num_lines, ['*'*num_chars]*num_lines, desired_state]

message_transition(FlashStarsTransition)

def SimpleTransition(current_state,desired_state):
    """
    The simplest possible transition -- go to the desired state directly with no fancy stuff.
    :param current_state: the current display state -- ignored by this function but included for consistency with other
    transition functions.
    :param desired_state: the desired display state
    :return: in this case, just a single-element list containing the desired state
    """

    return [desired_state]

display_transition(SimpleTransition)

def center_wipe(currentstate, desiredstate):
    """
    Transition function that wipes from currentstate to desiredstate out from the center in both directions.
    :param currentstate: a PIL image object representing the current display state
    :param desiredstate: a PIL image object representing the eventual desired display state
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(currentstate, Image.Image)
    assert isinstance(desiredstate, Image.Image)
    assert currentstate.size == desiredstate.size

    # initialize list for transition
    output = []

    # set initial columns for wipe (possibly same if odd number of pixels)

    if desiredstate.size[0] % 2 == 0: # if the number of columns of pixels is even
        # set the right and left columns as the middle ones - assuming the indices start at 0
        left_column = desiredstate.size[0] / 2 - 1
        right_column = desiredstate.size[0] / 2
    else: # if the number of columns of pixels is odd
        left_column = desiredstate.size[0] / 2 - 0.5
        right_column = left_column

    # iterate until the wipe has passed the edge
    while left_column >= -1:
        # create a mask with the right amount of interior area transparent
        # note - Image.composite(image1, image2, mask) yields image1 where mask is 1 and image2 where mask is 0
        image_mask = Image.new('1',desiredstate.size,1)
        ImageDraw.Draw(image_mask).rectangle([left_column, 0, right_column, desiredstate.size[1]-1], fill=0)
        # composite the initial image with the desired state using the layer mask
        composite = Image.composite(currentstate, desiredstate, image_mask)
        # draw vertical lines of all white to create the line doing the wiping
        draw = ImageDraw.Draw(composite)
        draw.line(xy=[left_column, 0, left_column, desiredstate.size[1]-1], fill=1, width=1)
        draw.line(xy=[right_column, 0, right_column, desiredstate.size[1]-1], fill=1, width=1)
        # append this new image to the list of images
        output.append(composite)
        left_column -= 1
        right_column += 1

    # return the list of images for transition
    return output

display_transition(center_wipe)


def dissolve_changes_only(currentstate, desiredstate):
    """
    A transition function that changes pixels one by one at random between currentstate and desiredstate.  Pixels that
    are the same in both images are skipped (no time taken)
    :param currentstate: a PIL image object representing the current display state
    :param desiredstate: a PIL image object representing the eventual desired display state
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(currentstate, Image.Image)
    assert isinstance(desiredstate, Image.Image)
    assert currentstate.size == desiredstate.size
    # generate a list of all pixel addresses in the image and shuffle it
    pixel_addresses = []
    for column in range(currentstate.size[0]):
        for row in range(currentstate.size[1]):
            pixel_addresses.append((column, row))
    random.shuffle(pixel_addresses)

    output = []

    next_image = currentstate.copy()
    # for each pixel in the image
    for pixel in pixel_addresses:
        # if the pixel is different between the input image and the desired one
        if currentstate.getpixel(pixel) != desiredstate.getpixel(pixel):
            # take the previous image in the output list and change that pixel (currentstate if list is empty)
            ImageDraw.Draw(next_image).point(pixel, fill=desiredstate.getpixel(pixel))
            # append that image to the output list
            output.append(next_image.copy())

    return output


display_transition(dissolve_changes_only)


def push_up(current_state, desired_state):
    """
    A transition function that raises the desired state up from the bottom of the screen, "pushing" the current state
    off the top.  One blank line is inserted between.
    :param current_state: a PIL image object representing the current display state
    :param desired_state: a PIL image object representing the eventual desired display state
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(current_state, Image.Image)
    assert isinstance(desired_state, Image.Image)
    assert current_state.size == desired_state.size

    output = []

    current_state_y_val = -1
    desired_state_y_val = current_state.size[1]

    # while the desired image has not reached the top
    while desired_state_y_val >= 0:
        # initialize next image
        next = Image.new("1", current_state.size, color=0)
        # paste current state at its y valute
        next.paste(current_state, (0, current_state_y_val))
        # paste desired state at its y value
        next.paste(desired_state, (0, desired_state_y_val))
        # increment y vales
        current_state_y_val -= 1
        desired_state_y_val -= 1
        # append output
        output.append(next)

    output.append(desired_state)
    # return the output
    return output

display_transition(push_up)


def push_down(current_state, desired_state):
    """
    A transition function that raises the desired state down from the top of the screen, "pushing" the current state
    off the bottom.  One blank line is inserted between.
    :param current_state: a PIL image object representing the current display state
    :param desired_state: a PIL image object representing the eventual desired display state
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(current_state, Image.Image)
    assert isinstance(desired_state, Image.Image)
    assert current_state.size == desired_state.size

    output = []

    current_state_y_val = 1
    desired_state_y_val = 0 - current_state.size[1]

    # while the desired image has not reached the top
    while desired_state_y_val <= 0:
        # initialize next image
        next = Image.new("1", current_state.size, color=0)
        # paste current state at its y valute
        next.paste(current_state, (0, current_state_y_val))
        # paste desired state at its y value
        next.paste(desired_state, (0, desired_state_y_val))
        # increment y vales
        current_state_y_val += 1
        desired_state_y_val += 1
        # append output
        output.append(next)

    # return the output
    return output

display_transition(push_down)


def push_right(current_state, desired_state):
    """
    A transition function that raises the desired state right from the left of the screen, "pushing" the current state
    off the right.  One blank line is inserted between.
    :param current_state: a PIL image object representing the current display state
    :param desired_state: a PIL image object representing the eventual desired display state
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(current_state, Image.Image)
    assert isinstance(desired_state, Image.Image)
    assert current_state.size == desired_state.size

    output = []

    current_state_x_val = 1
    desired_state_x_val = 0 - current_state.size[0]

    # while the desired image has not reached the top
    while desired_state_x_val <= 0:
        # initialize next image
        next = Image.new("1", current_state.size, color=0)
        # paste current state at its y valute
        next.paste(current_state, (current_state_x_val,0))
        # paste desired state at its y value
        next.paste(desired_state, (desired_state_x_val,0))
        # increment y vales
        current_state_x_val += 1
        desired_state_x_val += 1
        # append output
        output.append(next)

    # return the output
    return output

display_transition(push_right)


def push_left(current_state, desired_state):
    """
    A transition function that raises the desired state right from the left of the screen, "pushing" the current state
    off the right.  One blank line is inserted between.
    :param current_state: a PIL image object representing the current display state
    :param desired_state: a PIL image object representing the eventual desired display state
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(current_state, Image.Image)
    assert isinstance(desired_state, Image.Image)
    assert current_state.size == desired_state.size

    output = []

    current_state_x_val = -1
    desired_state_x_val = current_state.size[0]

    # while the desired image has not reached the top
    while desired_state_x_val >= 0:
        # initialize next image
        next = Image.new("1", current_state.size, color=0)
        # paste current state at its y valute
        next.paste(current_state, (current_state_x_val,0))
        # paste desired state at its y value
        next.paste(desired_state, (desired_state_x_val,0))
        # increment y vales
        current_state_x_val -= 1
        desired_state_x_val -= 1
        # append output
        output.append(next)

    # return the output
    return output

display_transition(push_left)

def ellipse_wipe(current_state, desired_state):
    """
    A transition function that draws an ellipse which gradually grows, revealing the desired state inside the ellipse.
    :param current_state: a PIL image object representing the current display state.  Must be larger than 4x4.
    :param desired_state: a PIL image object representing the eventual desired display state.  Must be larger than 4x4.
    :return: a list of PIL image objects representing a transition of display states to get from current to desired
    """
    assert isinstance(current_state, Image.Image)
    assert isinstance(desired_state, Image.Image)
    assert current_state.size == desired_state.size
    assert current_state.size[0] > 4 and current_state.size[1] > 4 #needs to be larger to make the loop work properly

    # initialize list for transition
    output = []

    # generate starting values for top, bottom, left and right
    if desired_state.size[0] % 2 == 0: # if the number of columns of pixels is even
        # set the right and left columns as the middle ones - assuming the indices start at 0
        left_column = desired_state.size[0] / 2 - 1
        right_column = desired_state.size[0] / 2
    else: # if the number of columns of pixels is odd
        left_column = desired_state.size[0] / 2 - 0.5
        right_column = left_column

    if desired_state.size[1] % 2 == 0: # if the number of rows of pixels is even
        # set the top and bottom rows as the middle ones - assuming the indices start at 0
        top_row = desired_state.size[1] / 2 - 1
        bottom_row = desired_state.size[1] / 2
    else: # if the number of rows of pixels is odd
        top_row = desired_state.size[1] / 2 - 0.5
        bottom_row = top_row

    # Start off the while loop operator as True to get into looping
    keep_going = True

    # while we haven't reached the left edge yet
    while keep_going:
        # create a mask with the right amount of interior area transparent
        image_mask = Image.new('1',desired_state.size,1)
        ImageDraw.Draw(image_mask).ellipse([left_column, top_row, right_column, bottom_row], fill=0, outline=0)
        # create a composite image of the desired and current states using the mask
        composite = Image.composite(current_state, desired_state, image_mask)
        # draw the ellipse
        draw = ImageDraw.Draw(composite)
        draw.ellipse([left_column, top_row, right_column, bottom_row], fill=None, outline=1)
        # add the image the output list
        output.append(composite)
        # increment the ellipse size
        if current_state.size[0] > current_state.size[1]: # if there are more columns than rows
            left_column -= 1
            right_column += 1
            top_row = min(top_row, int(left_column / current_state.size[0] * current_state.size[1]))
            bottom_row = max(bottom_row, int(right_column / current_state.size[0] * current_state.size[1]))
        else: # there must be more rows than columns, or there are an equal number in which case either algo is fine
            top_row -= 1
            bottom_row += 1
            left_column = min(left_column, int(top_row / current_state.size[1] * current_state.size[0]))
            right_column = max(left_column, int(bottom_row / current_state.size[1] * current_state.size[0]))

        # determine whether we are done
        try:
            # this is a quick way to see if the two images are the same
            # if the two images are the same, the difference image will be all zeros and the bounding box will be None
            keep_going = ImageChops.difference(output[-2], output[-1]).getbbox() is not None
        except IndexError: # indexerror means we don't have 2 images in the outputs list yet
            keep_going = True

    # return the output list, except the last one which we know is the same as the one before
    return output[:-1]

display_transition(ellipse_wipe)