from PIL import Image, UnidentifiedImageError
from pathlib import Path
from typing import Union
import textwrap
import flip_sign.helpers as hlp
import random
import datetime
import logging

logger_name = 'flip_sign.message_generation'
message_gen_logger = logging.getLogger(logger_name)

press_start_path = r'./assets/fonts/PressStart2P.ttf'
dat_dot_path = r'./assets/fonts/DatDot_edited_v1.ttf'


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
    def __init__(self, image: Union[Path, Image.Image], frequency: Union[float, callable] = linear_decline_frequency_image_message):
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


def linear_decline_frequency_date_message(days):
    """
    This message is intended as the default frequency for date messages.  It maxes at 100% probability of display
    for messages occurring in less than 30 days, and hits a minimum of 10% probability at about a year out.

    :param days: (float): the number of days until event start
    :return: frequency (float): the probability that the message will display
    """

    return min(1.0, max(1 - (days-30)/335, 0.1))


date_message_wrap_params = hlp.wrap_parameter_set(font_path=press_start_path, font_size=9, min_spacing=1,
                                                  split_words=False, truncate=True, wrap_kwargs={})
date_message_text_kws = {'params_order': [date_message_wrap_params],
                         'vertical_align': 'center', 'horizontal_align': 3, 'text_align': 'left',
                         'fixed_spacing': 1, 'wrap_text': False}


class DateMessage(Message):
    """
    A base class for messages which display a countdown to a date.  The render function and part of the __init__
    function live at this level.
    """
    def __init__(self, frequency: Union[float, callable]):
        """
        Initializes the message.

        :param frequency: (callable or float):  If float, the probability the message will display.
                                                If callable, only argument is the number of days (float) to event start
        """

        self.final_message_wrapped = None

        if isinstance(frequency, float):
            super().__init__(frequency)
        elif callable(frequency):
            next_start, _, _ = self.next_occurrence()
            days = (next_start - datetime.datetime.now()).days
            super().__init__(frequency(days))
        else:
            self.display = False
            message_gen_logger.warning("Frequency must be float or callable.  Frequency:" + str(frequency))
            return

    def next_occurrence(self):
        """
        Must be implemented in subclasses.

        :return: (next_start, next_end, all_day): the start, end, and all-day status of the next occurrence
        """

        raise NotImplementedError

    def render(self):
        """
        Prepare the message for display.  Calculate actual time to event start, format and prepare the image.

        :return: None
        """

        next_start, next_end, all_day = self.next_occurrence()
        formatted_timedelta = hlp.countdown_format(target_start=next_start, target_end=next_end, all_day=all_day)
        description_wrapped = textwrap.wrap(text=self.description, width=14, placeholder=" {}", max_lines=2)
        final_message = ['{:<15}'.format(text) + time for text, time in zip(description_wrapped, formatted_timedelta)]
        image, _, _ = hlp.draw_text_best_parameters(bbox_size=(168, 21), text=final_message, **self.draw_text_kws)
        self.final_message_wrapped = final_message
        self.image = image


class EphemeralDateMessage(DateMessage):
    """
    A class for date messages which occur only once (such as calendar events).
    """
    def __init__(self, description: str, start: datetime.datetime, end: datetime.datetime, all_day: bool,
                 frequency: Union[float, callable] = linear_decline_frequency_date_message):
        """
        Initializes the message.

        :param description: (str): the text which describes the event.
        :param start: (datetime.datetime): when the event starts
        :param end: (datetime.datetime): when the event ends
        :param all_day: (bool): whether the event is an all-day event
        :param frequency: (callable or float):  if float, the chance the message will display.
                                                if callable, single argument is number of days until event start (float)
        """
        self.description = description
        self.start = start
        self.end = end
        self.all_day = all_day
        self.draw_text_kws = date_message_text_kws

        if all_day:
            self.end = self.end.replace(hour=23, minute=59, second=59)

        # if message is fully in the past
        if self.end < datetime.datetime.now():
            self.display = False
            message_gen_logger.warning("EphemeralDateMessage fully in the past.  Description:" + self.description)
            return

        super().__init__(frequency)

    def next_occurrence(self):
        """
        Since this event occurs only once, nothing to be done here.  Simply pass back the input dates.

        :return: next_start, next_end, all_day:
                next_start: (datetime.datetime): the start of the next occurrence
                next_end: (datetime.datetime): the end of the next occurrence
                all_day: (bool): whether the next occurrence is an all-day event
        """

        return self.start, self.end, self.all_day
