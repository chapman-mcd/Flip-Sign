from PIL import Image, UnidentifiedImageError
from pathlib import Path
from typing import Union, Literal, Optional
from itertools import zip_longest
from flip_sign.assets import keys, fonts
from tzlocal import get_localzone_name
from pytz import timezone
import textwrap
import flip_sign.helpers as hlp
import random
import datetime
import logging

logger_name = 'flip_sign.message_generation'
message_gen_logger = logging.getLogger(logger_name)

press_start_path = fonts['PressStart2P']
dat_dot_path = fonts['DatDot']

LOCAL_TIMEZONE = timezone(get_localzone_name())

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


def linear_decline_frequency_image_message(image_argument: Union[Path, Image.Image]):
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
    def __init__(self, image: Union[Path, Image.Image],
                 frequency: Union[float, callable] = linear_decline_frequency_image_message):
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


def linear_decline_frequency_date_message(days: float):
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
                         'vertical_align': 1, 'horizontal_align': 3, 'text_align': 'left',
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
            days = (next_start - datetime.datetime.now().replace(tzinfo=LOCAL_TIMEZONE)).days
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
        time_strs = hlp.countdown_format(target_start=next_start, target_end=next_end, all_day=all_day)
        desc_strs = textwrap.wrap(text=self.description, width=14, placeholder=" {}", max_lines=2)
        final_message = ['{:<15}'.format(text) + time for text, time in zip_longest(desc_strs, time_strs, fillvalue='')]
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
        if self.end < datetime.datetime.now().replace(tzinfo=LOCAL_TIMEZONE):
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


class RecurringFixedDateMessage(DateMessage):
    """
    A class for date messages which recur on the same calendar date every year (e.g. New Year's Day on January 1st)
    """
    def __init__(self, description: str, base_date_start: datetime.datetime, base_date_end: datetime.datetime,
                 all_day: bool, frequency: Union[float, callable] = linear_decline_frequency_date_message):
        """
        Initializes the message.

        :param description: (str): the text which describes the event.
        :param base_date_start: (datetime.datetime): when the event starts, in an arbitrary year.
        :param base_date_end: (datetime.datetime): when the event ends, in the same year as base_date_start
        :param all_day: (bool): whether the event is an all-day event
        :param frequency: (callable or float):  if float, the chance the message will display.
                                        if callable, single argument is number of days until event start (float)
        """
        self.description = description
        self.base_start = base_date_start
        self.base_end = base_date_end
        self.all_day = all_day
        self.draw_text_kws = date_message_text_kws

        if all_day:
            self.base_end = self.base_end.replace(hour=23, minute=59, second=59)

        super().__init__(frequency)

    def next_occurrence(self):
        """
        Returns the next occurrence of the event.

        :return: next_start, next_end, all_day:
                next_start: (datetime.datetime): the start of the next occurrence
                next_end: (datetime.datetime): the end of the next occurrence
                all_day: (bool): whether the next occurrence is an all-day event
        """
        now = datetime.datetime.now().replace(tzinfo=LOCAL_TIMEZONE)

        # if the event has already passed this year, use next year
        if now > self.base_end.replace(year=now.year):
            next_start = self.base_start.replace(year=now.year + 1)
            next_end = self.base_end.replace(year=now.year + 1)
        # if the event has not already passed this year, use this year
        else:
            next_start = self.base_start.replace(year=now.year)
            next_end = self.base_end.replace(year=now.year)

        return next_start, next_end, self.all_day


class RecurringVariableDateMessage(DateMessage):
    """
    A class for events which recur on different dates depending on the year (e.g. Easter, Ramadan)
    """
    def __init__(self, description: str, next_dates_func: callable, all_day: bool,
                 frequency: Union[float, callable] = linear_decline_frequency_date_message):
        """
        Initializes the message.

        :param description: (str): the text which describes the event.
        :param next_dates_func: (callable): function which returns a tuple (start, end) of the next occurrence
        :param all_day: (bool): whether the event is an all-day event
        :param frequency: (callable or float):  if float, the chance the message will display.
                                            if callable, single argument is number of days until event start (float)
        """

        self.description = description
        self.next_dates_func = next_dates_func
        self.all_day = all_day
        self.draw_text_kws = date_message_text_kws

        super().__init__(frequency)

    def next_occurrence(self):
        """
        Returns the next occurrence of the event.

        :return: next_start, next_end, all_day:
                next_start: (datetime.datetime): the start of the next occurrence
                next_end: (datetime.datetime): the end of the next occurrence
                all_day: (bool): whether the next occurrence is an all-day event
        """

        return *self.next_dates_func(), self.all_day


basic_text_default_wrap_params = (
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=16, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=12, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=9, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=8, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=True, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=True, truncate=True,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=True, truncate=True,
                           wrap_kwargs={'placeholder': "."}),
)


class BasicTextMessage(Message):
    """
    A class for messages which are simple text.
    """
    def __init__(self, text: Union[str, list], font_parameters: Union[tuple, list] = basic_text_default_wrap_params,
                 frequency: float = 0.9, **kwargs):
        """
        Initializes the message.

        :param text: (str or list): the text to be displayed in the message
        :param font_parameters: (tuple or list): a list or tuple of hlp.wrap_parameter_set objects, in preference order
        :param frequency: (float): the probability that the message will display
        :param kwargs: (captured as dict): passed to draw_text_best_parameters
        """

        self.text = text
        self.font_parameters = font_parameters
        self.draw_text_kwargs = kwargs
        self.applied_spacing = None
        self.applied_params = None

        super().__init__(frequency=frequency)

    def render(self):
        """
        Prepare the message for display.  Determine best parameters and save the image and resulting params.

        :return: None
        """

        image, params, spacing = hlp.draw_text_best_parameters(params_order=self.font_parameters,
                                                               bbox_size=(168, 21), text=self.text,
                                                               **self.draw_text_kwargs)
        self.image = image
        self.applied_params = params
        self.applied_spacing = spacing


date_match_wrap_params = hlp.wrap_parameter_set(font_path=press_start_path, font_size=9, min_spacing=1,
                                                split_words=False, truncate=True, wrap_kwargs={'placeholder': '{}'})


class DateMatchTextMessage(BasicTextMessage):
    """
    A convenience class for creating text-only messages that 'match' with output from the DateMessage class
    """
    def __init__(self, text: str, frequency: float = 0.9):
        """
        Initializes the message.

        :param text: (str or list): the text to be displayed in the message
        :param frequency: (float): the probability that the message will display
        """
        super().__init__(text=text, font_parameters=[date_message_wrap_params], frequency=frequency, vertical_align=1,
                         horizontal_align=3, text_align='left', fixed_spacing=1, wrap_text=True)


class AccuweatherDescription(BasicTextMessage):
    """
    A class to display the text description of the weather from the AccuWeather API
    """
    def __init__(self, location: dict, description: Optional[str] = None, headline: bool = True,
                 date: Union[datetime.datetime, datetime.date] = None, day_or_night: Literal['day', 'night'] = 'day',
                 font_parameters: Union[tuple, list] = basic_text_default_wrap_params,
                 frequency: float = 1.0, **kwargs):
        """
        Initializes the message.

        :param location: (dict): a location response from the accuweather API
        :param description: (str): Location description printed in the message.  Optional.
        :param headline: (bool): whether to be a headline or date description.  if true, date and day/night are ignored
        :param date: (datetime.datetime or datetime.date) the date for the description to be displayed
        :param day_or_night: ('day' or 'night'): whether the description should be for day or night weather
        :param font_parameters: (tuple or list): a list or tuple of hlp.wrap_parameter_set objects, in preference order
        :param frequency: (float): the probability that the message will display
        :param kwargs: kwargs: (captured as dict): passed to draw_text_best_parameters
        """

        self.location = location.copy()
        self.headline = headline
        # standardize type to datetime.date
        # use attribute of hour to determine if date was passed as datetime
        if hasattr(date, 'hour'):
            date = date.date()
        self.date = date
        self.day_or_night = day_or_night.capitalize()
        if description is not None:
            self.description = description
        else:
            self.description = self.location['LocalizedName']

        # initialize with blank text which will be replaced in the render method
        super().__init__(text='', font_parameters=font_parameters, frequency=frequency, **kwargs)

        if not self.headline and self.date is None:
            self.display = False
            message_gen_logger.warning("Improper WeatherDescription construction.  Location:" + str(location))

    def render(self):
        """
        Prepares the message for display.  Makes API requests to get the proper weather text, then displays it
        using the same render method as a basic text message.

        :return: None
        """
        api_request = ('http://dataservice.accuweather.com/forecasts/v1/daily/5day/',
                       self.location['Key'],
                       '?apikey=',
                       keys['AccuweatherAPI'],
                       '&details=true',
                       '&metric=true')
        response = hlp.accuweather_api_request(api_request)  # no try/except here since errors should be handled above

        if self.headline:
            self.text = self.description + ":" + response['Headline']['Text']
        else:
            # humanize the date into today/tomorrow/ISO8601
            if self.date == datetime.date.today():
                date_text = self.description + ":Today(" + self.day_or_night[0] + "): "
            elif self.date == datetime.date.today() + datetime.timedelta(days=1):
                date_text = self.description + ":Tomorrow(" + self.day_or_night[0] + "): "
            else:
                date_text = self.description + ":" + self.date.isoformat() + "(" + self.day_or_night[0] + "): "

            for forecast_day in response['DailyForecasts']:
                if datetime.datetime.fromisoformat(forecast_day['Date']).date() == self.date:
                    self.text = date_text + forecast_day[self.day_or_night]['LongPhrase']

            # if we got here, the date was not in the API forecast response
            if self.text == '':
                raise ValueError("Weather Description Obj: Provided date not found in API response.")

        super().render()


weather_stub_default_wrap_params = (
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=16, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=12, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=9, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=8, min_spacing=1, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=False, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=press_start_path, font_size=8, min_spacing=1, split_words=True, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=True, truncate=False,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=True, truncate=True,
                           wrap_kwargs={}),
    hlp.wrap_parameter_set(font_path=dat_dot_path, font_size=8, min_spacing=-2, split_words=True, truncate=True,
                           wrap_kwargs={'placeholder': "."}),
)


class AccuweatherDashboard(Message):
    """
    A class to display weather forecast information in a visual layout.  Data source is accuweather API.
    """
    def __init__(self, location: dict, description: Optional[str] = None,
                 start_date: Union[datetime.datetime, datetime.date] = None,
                 language: Literal["english", "portugues"] = "english", frequency: float = 1.0):
        """
        Initializes the message.

        :param location: (dict): a location response from the accuweather API
        :param description: (str): Location description printed in the message.  Optional.
        :param start_date: (datetime.datetime or datetime.date) the first day to display forecast.  default today
        :param language: (str) the language for weekday display, currently only "english" and "portugues"
        :param frequency: (float): the probability that the message will display
        """

        self.location = location.copy()
        self.language = language
        # standardize type to datetime.date
        if hasattr(start_date, 'hour'):  # use attribute of hour to determine if date was passed as datetime
            start_date = start_date.date()
        elif start_date is None:  # if omitted, start with today
            start_date = datetime.date.today()
        self.start_date = start_date

        if description is not None:
            self.description = description
        else:
            self.description = self.location['LocalizedName']

        self.weather_icon_lookup = {
                                    1: 'sunny', 2: 'sunny',
                                    3: 'partlycloudy', 4: 'partlycloudy',
                                    5: 'mostlycloudy', 6: 'mostlycloudy',
                                    7: 'cloudy', 8: 'cloudy',
                                    11: 'fog',
                                    12: 'rain', 13: 'rain', 14: 'rain',
                                    15: 'tstorms', 16: 'tstorms', 17: 'tstorms',
                                    18: 'rain',
                                    19: 'snow', 20: 'snow', 21: 'snow', 22: 'snow', 23: 'snow',
                                    24: 'sleet', 25: 'sleet', 26: 'sleet', 29: 'sleet',
                                    30: 'hot', 31: 'cold', 32: 'wind'
        }

        super().__init__(frequency=frequency)

    def render(self):
        """
        Prepare the message for display.  Make the required API calls, prepare the image and save in self.image.

        :return: None.
        """

        # initialize output
        dashboard_rendered = Image.new(mode="1", size=(168, 21), color=0)

        # make API call
        api_request = ('http://dataservice.accuweather.com/forecasts/v1/daily/5day/',
                       self.location['Key'],
                       '?apikey=',
                       keys['AccuweatherAPI'],
                       '&details=true',
                       '&metric=true')

        response = hlp.accuweather_api_request(api_request)  # no try/except here since errors should be handled above

        # wrap description text and add to output
        weather_stub_size = (58, 21)
        description_drawn, _, _ = hlp.draw_text_best_parameters(params_order=weather_stub_default_wrap_params,
                                                                bbox_size=weather_stub_size, text=self.description)
        dashboard_rendered.paste(im=description_drawn, box=(0, 0))

        # add forecast days to image
        x_position = 59
        for forecast_day in response['DailyForecasts']:
            forecast_date = datetime.datetime.fromisoformat(forecast_day['Date'])
            if forecast_date.date() >= self.start_date:  # only add if after start date
                # extract info from API response
                high = forecast_day['RealFeelTemperature']['Maximum']['Value']
                low = forecast_day['RealFeelTemperature']['Minimum']['Value']
                chance_precipitation = forecast_day['Day']['PrecipitationProbability'] / 100.0
                iso_weekday = forecast_date.isoweekday()
                icon = self.weather_icon_lookup[forecast_day['Day']['Icon']]

                # call render_day to create the image for the day
                forecast_dashboard_part = hlp.render_day(high=high, low=low, chance_precipitation=chance_precipitation,
                                                         iso_weekday=iso_weekday, icon_name=icon,
                                                         language=self.language)
                dashboard_rendered.paste(im=forecast_dashboard_part, box=(x_position, 0))
                x_position += 22

        # save in self.image
        self.image = dashboard_rendered
