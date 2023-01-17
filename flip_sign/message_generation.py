from PIL import Image, UnidentifiedImageError
from pathlib import Path
import random
import datetime
import logging

logger_name = 'flip_sign.message_generation'
message_gen_logger = logging.getLogger(logger_name)


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


def linear_decline_frequency_image_message(image_argument):
    """
    For pathlib.path images, this function provides a linearly declining probability starting at 100% for the first
    month and declining to 25% after just ovr 1 year.  For PIL.Image arguments, provides 50% for all.

    :param image_argument: (pathlib.Path or PIL.Image) the image provided to the ImageMessage constructor
    :return: frequency: (float) the probability that the message will display
    """
    if isinstance(image_argument, Image.Image):
        return 0.5
    elif isinstance(image_argument, Path):
        image_modified_time = datetime.datetime.fromtimestamp(image_argument.stat().st_mtime)
        days = (datetime.datetime.now() - image_modified_time).days
        return min(1.0, max(1 - (days-30)/365, 0.25))
    else:
        raise ValueError("Image must be a pathlib path or Pillow Image object.")


class ImageMessage(Message):
    """
    A message composed of a single static image, the same size as the sign (168 x 21).
    """
    def __init__(self, image: Path or Image, frequency: float or callable = linear_decline_frequency_image_message):
        """
        Initializes the message.

        :param image: (pathlib.Path or PIL.Image) the image to display
        :param frequency: (callable or float)  a float probability to display or callable to generate said probability
                           if callable, must accept the companion image parameter as a single argument
        """

        if callable(frequency):
            try:
                super().__init__(frequency(image))
            except FileNotFoundError as e:
                self.display = False
                message_gen_logger.warning("Error calculating frequency. Image:" + str(image))
                message_gen_logger.info("Error Details:" + str(e))
                return
        elif isinstance(frequency, float):
            super().__init__(frequency)
        else:
            self.display = False  # do not display because of error
            message_gen_logger.warning("Invalid frequency passed, must be callable or float. Passed:" + str(frequency))
            return

        if isinstance(image, Path):
            try:
                Image.open(image).verify()
                self.image = Image.open(image)
            except (FileNotFoundError, UnidentifiedImageError) as e:
                self.display = False
                message_gen_logger.warning("Error opening image. Image:" + str(image))
                message_gen_logger.info("Error Details:" + str(e))
                return
        elif isinstance(image, Image.Image):
            self.image = image
        else:
            # Frequency function will probably find this error first, but frequency could also be a float
            self.display = False  # do not display
            message_gen_logger.warning("Invalid image passed, must be Image or Path. Passed:" + str(image))
            return

        # if image is the wrong size
        if self.image.width != 168 or self.image.height != 21:
            self.display = False  # do not display this image
            message_gen_logger.warning("Image is the wrong size.  Image:" + str(image))  # log it
            return

        # convert image to black-and-white
        if self.image.mode != '1':
            self.image = self.image.convert(mode='1')

    def render(self):
        """
        Nothing needed here, since the image is already saved.  Does nothing, returns None.

        :return: None
        """
        pass
