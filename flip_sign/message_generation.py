import random


class Message(object):
    """
    A base message class for branching into subclasses.  Only the display randomization elements and get_image method
    will live at this level.
    """
    def __init__(self, frequency: float):
        """
        Selects whether to display the image or not, based on provided frequency.

        :param frequency: (float) a float between 0 and 1 indicating the probability this message will display
        """
        self.display = random.random() < frequency
        self.image = None

    def __bool__(self):
        """
        Message display will be tested using this built-in method.  "if Message:"

        :return: (boolean) whether the message displays.
        """
        return self.display

    def render(self):
        """
        The render method must be overridden in subclasses.

        :return: None
        """
        raise NotImplementedError

    def get_image(self):
        """
        Standard method (called after the render method) for getting the image to display.

        :return: (PIL.Image) the message rendered into an image
        """
        return self.image

