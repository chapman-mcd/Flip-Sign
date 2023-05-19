import logging
import pathlib
from urllib.request import Request, urlopen
from urllib.parse import quote
import datetime as dt
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload
from cachetools import cached, TLRUCache, TTLCache
from typing import Union, Literal
import json
from PIL import ImageFont, ImageDraw, ImageChops, Image
from tzlocal import get_localzone_name
from pytz import timezone
from math import acos, sin, cos, radians
from hashlib import sha256
import gzip
import re
import os
import io
import textwrap
from collections import namedtuple
from flip_sign.assets import root_dir, keys
import math
from google.auth.transport.requests import Request as google_Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger_name = 'flip_sign.helpers'
helper_logger = logging.getLogger(logger_name)

LOCAL_TIMEZONE = timezone(get_localzone_name())


def accuweather_cache_ttu(_key, value, now):
    """
    Function which returns the expiry time for cached results from the accuweather API.  Location requests are cached
    for 30 days, 5-day forecast results are cached for 4 hours.  Unexpected events are written to the log.

    :param _key: in this case, the accuweather URL
    :param value: the API response. provided by cachetools, but not relevant here.
    :param now: current value of timer
    :return: (float) expiration time for the cached request
    """

    # join the url into a single string
    key_str = ''.join(_key[0])  # function call is in a tuple (arg1, arg2, ..).  need to access first/only arg

    # use presence of '5day' to determine 5-day forecast
    if '5day' in key_str:
        increment = 4 * 60 * 60  # store 5-day forecasts for 4 hours
    # use present of 'geoposition' to detect location request
    elif 'geoposition' in key_str:
        increment = 30 * 24 * 60 * 60  # store location requests for 30 days
    else:
        # if a different URL is passed, write to the log and cache for 10 minutes only
        helper_logger.warning("Unhandled URL type for AccuWeather Cache.  Url: " + key_str)
        increment = 10 * 60

    return now + increment


_accuweather_cache = TLRUCache(maxsize=10, ttu=accuweather_cache_ttu)
@cached(cache=_accuweather_cache)
def accuweather_api_request(url):
    """
    Requests the provided URL from the accuweather API and returns.  No errors are handled in this function,
    all are passed along.  Results cached as per ttu function.

    :param url: (tuple) - ordered pieces of the url to request
    :return: (dict) the json response from accuweather, parsed to dict
    """
    url_string = ''.join(url)
    req = Request(url_string, headers={"Accept-Encoding": "gzip, deflate"})
    response = json.loads(gzip.decompress(urlopen(req).read()))

    return response


_google_geocoding_cache = TTLCache(maxsize=50, ttl=60*60*24*30)  # cache geocoding results for 30 days
@cached(cache=_google_geocoding_cache)
def geocode_to_lat_long(location_string: str):
    """
    Uses google's geocoding API to turn strings provided into lat/long coordinates.  Always chooses the most likely /
    first option returned by the API.  Raises ValueError if location not found by google.  Does not handle any
    HTTP exceptions - all are passed on.

    :param location_string: (str) - the location to be geocoded.
    :return: (dict): a dictionary containing {'lat': **latitude_value**, 'lng': **longitude_value**}
    """

    geocode_base_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
    url_string = ''.join([geocode_base_url, quote(location_string), "&key=", keys['GoogleLocationAPI']])
    req = Request(url_string)
    response = json.loads(urlopen(req).read())

    if response['status'] == 'ZERO_RESULTS':
        raise ValueError("Location not found by Google API.")
    else:
        return response['results'][0]['geometry']['location']


def countdown_format(target_start, target_end, all_day):
    """
    This function calculates the amount of time until the passed date and returns it as a 2-list of 3-character
    strings.  The calculation of the number of months is done in a way that feels natural - e.g. july 15th is
    2 months and 3 days after May 12th.

    Longest time to target_date is 9.999 years.  Returns error if exceeded.
    :param target_start: (datetime.datetime) the start time of the event
    :param target_end: (datetime.datetime) the end time of the event
    :param all_day: (boolean) whether the target event is an all-day event
    :return: tuple of two 3-character strings showing the time remaining (e.g. ('3mo', '10d))
    """

    # initialize current time
    current_time = dt.datetime.now().replace(tzinfo=LOCAL_TIMEZONE)

    # confirm time delta within limits
    if (target_start - current_time).days > 3651:
        raise ValueError("Time delta out of range.  Max 9.99 years.")
    # confirm end time after start time
    if target_end < target_start:
        raise ValueError("End time before start time.")
    # confirm end time is in the future
    if target_end < current_time:
        raise ValueError("Target event not in the future.")

    # if all-day event
    if all_day:
        # replace the time part of start and current time with 12:00 AM
        current_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        target_start = target_start.replace(hour=0, minute=0, second=0, microsecond=0)
        # replace time part of the end time with 23:59:59
        target_end = target_end.replace(hour=23, minute=59, second=59)

    # if current time is between start and end (inclusive) return now
    if (current_time <= target_end) and (current_time >= target_start):
        return 'Now', '   '

    # initialize return value
    date_strings = []
    # iterate through the list of divisors
    for divisor in ['years', 'months', 'weeks', 'days', 'hours', 'minutes']:
        difference, current_time_divisor_added, next_divisors = calc_diff(current_time, target_start, divisor)
        # if current divisor fits
        if difference > 0:
            # add it to the list
            difference_str = format_3char_time_string(difference, divisor)
            date_strings.append(difference_str)
            # add largest divisor to the date (to check remainder)
            current_time = current_time_divisor_added
            break

    # iterate list of second-level divisors
    for divisor in next_divisors:
        difference, _, _ = calc_diff(current_time, target_start, divisor)
        # if current divisor fits
        if difference > 0:
            # add it to the list
            difference_str = format_3char_time_string(difference, divisor)
            date_strings.append(difference_str)

    # if no second-level divisor has fit
    if len(date_strings) == 1:
        # add 3 blank spaces
        date_strings.append('   ')

    # return the string
    return tuple(date_strings)


def format_3char_time_string(difference, divisor):
    """
    Formats a time difference as a 3-character string.  Handles years, months, weeks, days, hours, minutes.

    :param difference: (int) the difference
    :param divisor: (string) the units of measure (e.g. years, months)
    :return: (string) a 3-character string representing the time difference
    """
    abbreviations = {'years': 'yr', 'weeks': 'wk', 'days': 'd', 'hours': 'h', 'minutes': 'm'}

    # make months fit as either 'mo' or 'M' depending on number
    if divisor == 'months':
        if difference < 10:
            out_str = str(difference) + 'mo'
        else:
            out_str = str(difference) + 'M'
    # other divisors fit all the same way, no need for complications
    else:
        out_str = str(difference) + abbreviations[divisor]

    # if we only have 2 characters pad a trailing space
    if len(out_str) == 2:
        out_str += ' '

    return out_str


def calc_diff(current_time, target_start, divisor):
    """
    This function calculates the time delta between two dt.datetime objects, based on a provided divisor.  In that way,
    it has similar functionality to datetime's timedelta objects, only this function also handles months and years.
    The datetime module avoids these because they have varying durations and different people may want them differently.

    Function returns the number of intervals, a new datetime object with the intervals added (to calculate the
    remainder) and a list of divisors that could be used to split the remainder.

    :param current_time: (dt.datetime) the current date and time
    :param target_start: (dt.datetime) the target date and time
    :param divisor: (string) the divisor to be used (e.g. 'years', 'months')
    :return: (difference, new_dt, new_divisors)
            difference: (int) the number of divisors between current_time and target_start
            new_dt: (dt.datetime) the current time with {difference} {divisor}s added to it. for calculating remainder
            new_divisors: (list) list of strings indicating which divisors can be applied to the remainder
    """

    # look up new divisors
    new_divisors_dict = {'years': ['months', 'weeks', 'days'],
                         'months': ['days'],
                         'weeks': ['days'],
                         'days': ['hours'],
                         'hours': ['minutes'],
                         'minutes': []}
    new_divisors = new_divisors_dict[divisor]

    # first case is the easier divisors to handle (since they are fully defined)
    if divisor in ['weeks', 'days', 'hours', 'minutes']:
        # determine number of seconds in the divisor
        num_seconds = dt.timedelta(**{divisor: 1}).total_seconds()
        # determine difference and corresponding new_dt using integer division
        diff = int((target_start - current_time).total_seconds() // num_seconds)
        new_dt = current_time + dt.timedelta(**{divisor: diff})

    elif divisor == 'years':
        # iterate through the max number of years
        for i in range(10):
            if add_years(current_time, i+1) > target_start:
                diff = i
                new_dt = add_years(current_time, i)
                break

    elif divisor == 'months':
        # iterate through the max number of months
        for i in range(12):
            if add_months(current_time, i+1) > target_start:
                diff = i
                new_dt = add_months(current_time, i)
                break

    return diff, new_dt, new_divisors


def add_years(date, num_years):
    """
    Adds num_years to a provided date.  Handles leap years by returning February 28th in the future year.

    :param date: (dt.datetime) starting date
    :param num_years: (int) the number of years to add
    :return: new_date (dt.datetime) the starting date with num_years added.
    """

    current_year = date.year
    try:
        new_date = date.replace(year=current_year + num_years)
    except ValueError:  # it is February 29th and the new year is not a leap year
        new_date = date.replace(year=current_year + num_years, day=28)

    return new_date


def add_months(date, num_months):
    """
    Adds num_months to a provided date.  Handles 28, 29 and 30-day months by giving the latest date in the ending month.

    Examples:
     - January {29th/30th/31st} + 1 month (leap year) = February 29th
     - January {28th/29th/30th/31st} + 1 month (non leap year) = February 28th
     - August 31st + 3 months = November 30th

    :param date: (dt.datetime) the starting date
    :param num_months: (int) number of months to add
    :return: new_date (dt.datetime) the starting date
    """

    current_month = date.month
    current_year = date.year
    new_year = current_year

    new_month = current_month + num_months
    if new_month > 12:
        new_month -= 12
        new_year = current_year + 1

    try:
        new_date = date.replace(year=new_year, month=new_month)
    except ValueError:  # new month does not have enough days
        new_month += 1
        if new_month > 12:
            new_month -= 12
            new_year += 1
        new_date = date.replace(year=new_year, month=new_month, day=1)
        new_date += dt.timedelta(days=-1)

    return new_date


def text_bbox_size(font: ImageFont, text: Union[list, str], line_spacing: int, align: str):
    """
    Calculates the size of a message, in pixels.  Takes in a message (split into lines) and font parameters.
    Returns the size of the written message in pixels, and the appropriate target such that the first pixel of the
    message is drawn at the origin: (0,0).

    :param font: (PIL.ImageFont) the font to be used
    :param text: (list or string) the message to be sized
    :param line_spacing: (int) the spacing between lines, as per PIL.ImageDraw.multiline_text
    :param align: (str) 'center' or 'left' or 'right'
    :return: size (tuple), target (tuple)
              size:  the size of the message, in pixels (rows, columns)
              target: the location to be fed to multiline_text to put the first pixel at the origin (x, y)
    """

    # handle case of being passed a list - turn it into a string with newlines
    if isinstance(text, list):
        text = '\n'.join(text)

    canvas_size = 1024
    finished_bbox = False

    # iterate to allow for increasing canvas size if it is too small
    while not finished_bbox:
        # create new image filled with black
        image = Image.new('1', (canvas_size, canvas_size), 0)
        # draw the message on the canvas in the font at position 10,10 and get bbox
        draw = ImageDraw.Draw(image)
        draw.multiline_text(xy=(10, 10), text=text, font=font, anchor='la', spacing=line_spacing, align=align, fill=1)
        bbox = image.getbbox()

        # check if text hit the edge.  since truncations can happen in strange ways, test with 70% of box as the cutoff
        if bbox[2] < canvas_size * 0.7 and bbox[3] < canvas_size * 0.7:
            # if text did not hit the edge, exit the loop
            finished_bbox = True
        else:
            # if text did hit the edge, double the canvas size (subject to max)
            if canvas_size == 8192:
                raise ValueError("Font too large.")
            canvas_size *= 2

    # calculate results from final bbox
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    target_x = 10 - bbox[0]
    target_y = 10 - bbox[1]

    return (width, height), (target_x, target_y)


def wrap_text_split_words(text: str, width: int, replace_whitespace: bool = True, drop_whitespace: bool = True,
                          max_lines: int = None, placeholder: str = '[...]', already_wrapped: list = []):
    """
    Wraps the string given in text so that every line is at most width characters long.  Pays no regard to word
    boundaries, breaking words to fit maximum text into the space.  Very similar in practice to simple string-slicing,
    but also handles line-leading whitespace and offers additional options similar to textwrap.wrap, allowing for it
    to be a drop-in replacement.

    Returns a list containing each line of the original text.

    :param text: (str) the text to be wrapped
    :param width: (int) the maximum number of characters per line
    :param replace_whitespace: (boolean) whether to replace whitespace characters (\t, \n)
    :param drop_whitespace: (boolean) whether to replace line-leading whitespace
    :param max_lines: (int) the maximum number of lines
    :param placeholder: (str) the string to add at the end in case of truncation.
    :param already_wrapped: (list) used internally for recursion
    :return: wrapped_text: (list) the text, wrapped into lines
    """

    if width < len(placeholder):
        raise ValueError("placeholder too large for max width")

    # handle initial replace whitespace, only if first call (already_wrapped is an empty list)
    if already_wrapped == [] and replace_whitespace:
        text = re.sub(r"[\n\t\v\f\r ]+", " ", text)
        
    # create new list to pass on
    next_wrapped = already_wrapped.copy()
    
    # end recursion condition: max lines hit.  check and handle
    if len(next_wrapped) == max_lines:
        next_wrapped[-1] = next_wrapped[-1][:-len(placeholder)] + placeholder
        return next_wrapped
    
    # drop line-leading whitespace if required
    if drop_whitespace:
        text = re.sub(r"^\s+", "", text)
        
    # end recursion condition: remaining text fits in this line
    if len(text) < width:
        next_wrapped.append(text)
        return next_wrapped
    
    else:  # continue recursion: add to wrapped list and recur
        next_wrapped.append(text[:width])
        return wrap_text_split_words(text[width:], width=width, replace_whitespace=replace_whitespace, 
                                     drop_whitespace=drop_whitespace, max_lines=max_lines, placeholder=placeholder,
                                     already_wrapped=next_wrapped)


def bbox_text_no_truncation(bbox_size: tuple, line_spacing: int, text: str, split_words: bool, font: ImageFont,
                            align: str, **kwargs):
    """
    Attempts to iteratively wrap text to fit inside bbox_size without truncating at the end.  Does not change font or
    size, and so allows for the possibility that the text cannot fit.  Follows method from the wand package
    documentation.  Uses either textwrap.wrap or wrap_text_split_words internally, depending on the split_words
    arguemnt.  **kwargs are all passed to textwrap.wrap or wrap_text_split_words.

    Returns a boolean indicating if the text can fit, and a list containing the text post-wrapping.

    :param bbox_size: (tuple) the bounding box the text must fit in
    :param line_spacing: (int) the line spacing, passed to PIL.ImageDraw.Draw.multiline_text
    :param text: (str) the text to be fit into the box
    :param split_words: (Boolean) whether to split words while text wrapping
    :param font: (PIL.ImageFont) the font to be used
    :param align: ('left', 'center', 'right') the text alignment
    :param kwargs: (dict) passed to textwrap.wrap or wrap_text_split_words as appropriate
    :return: (fits, wrapped_text):
                fits: (Boolean) whether the message fits
                wrapped_text: (list) the text, wrapped into lines
    """

    # initialize loop
    columns = len(text)

    while columns > 0:
        # wrap text with current number of columns
        if split_words:
            test_text = wrap_text_split_words(text, width=columns, **kwargs)
        else:
            test_text = textwrap.wrap(text, width=columns, **kwargs)

        # check size with current number of columns
        check_size, _ = text_bbox_size(font=font, text=test_text, line_spacing=line_spacing, align=align)

        # if too tall, message does not fit
        if check_size[1] > bbox_size[1]:
            return False, []
        # if the message fits horizontally as well as vertically, return the current setup
        elif check_size[0] < bbox_size[0]:
            return True, test_text
        # if the message doesn't fit, continue looping
        # reduce number of columns and repeat
        else:
            columns += -1

    # if the loop has completed (can get here in various cases, such as break_long_words=False)
    # then the text does not fit
    if columns == 0:
        return False, []


def bbox_text_truncation(bbox_size: tuple, line_spacing: int, text: str, split_words: bool, font: ImageFont,
                         align: str, **kwargs):
    """
    Attempts to iteratively wrap text to fit in bbox_size, truncating if necessary.  Given truncation, the text
    will always fit unless a single line of text is too tall for bbox_size or the truncation placeholder is too large.
    **kwargs are passed to textwrap.wrap or text_wrap_split_words, as appropriate.

    Returns a boolean indicating if the text can fit, and a list containing the text post-wrap.

    :param bbox_size: (tuple) the bounding box the text must fit in
    :param line_spacing: (int) the line spacing, passed to PIL.ImageDraw.Draw.multiline_text
    :param text: (str) the text to be fit into the box
    :param split_words: (Boolean) whether to split words while text wrapping
    :param font: (PIL.ImageFont) the font to be used
    :param align: ('left', 'center', 'right') the text alignment
    :param kwargs: (dict) passed to textwrap.wrap or wrap_text_split_words as appropriate
    :return: (fits, wrapped_text):
                fits: (Boolean) whether the message fits
                wrapped_text: (list) the text, wrapped into lines
    """

    # initialize
    columns = len(text)
    if split_words:
        wrap_func = wrap_text_split_words
    else:
        wrap_func = textwrap.wrap

    # check for the possibility that a single line is too tall
    check_size, _ = text_bbox_size(font=font, text=text, line_spacing=line_spacing, align=align)
    if check_size[1] > bbox_size[1]:
        return False, []

    # determine number of columns
    while columns > 0:
        # wrap text using current number of columns
        test_text = wrap_func(text=text, width=columns, **kwargs)

        # calculate size - if fits horizontally, break out.  if not, reduce number of columns
        check_size, _ = text_bbox_size(font=font, text=test_text, line_spacing=line_spacing, align=align)
        if check_size[0] < bbox_size[0]:
            break
        else:
            columns += -1

    # if loop completed with columns == 0 (can happen if break_long_words=False)
    # then the combination does not work
    if columns == 0:
        return False, []

    # determine number of lines
    lines = len(test_text)
    while lines > 0:
        # need to wrap in try-except to handle case where placeholder is too large for the columns
        try:
            test_text = wrap_func(text=text, width=columns, max_lines=lines, **kwargs)
        except ValueError as e:
            if e.args[0] == "placeholder too large for max width":
                return False, []
            else:
                raise

        # calculate size - if it fits vertically, return the answer.  if not, reduce the number of lines.
        check_size, _ = text_bbox_size(font=font, text=test_text, line_spacing=line_spacing, align=align)
        if check_size[1] < bbox_size[1]:
            return True, test_text
        else:
            lines += -1


def check_bbox_no_wrap(bbox_size: tuple, line_spacing: int, text: str, font: ImageFont, align: str, **kwargs):
    """
    This function replaces bbox_text_truncation and bbox_text_no_truncation when wrap_text=False.  The wrap_text=False
    option is intended to allow custom line breaks / phrasing in the text.  In this scenario, newline characters are
    expected in text, as necessary to make the message fit.  Since no word wrapping is performed, this function simply
    checks if the message fits and returns that answer, along with the message unchanged.

    :param bbox_size: (tuple) the bounding box the text must fit in
    :param line_spacing: (int) the line spacing, passed to PIL.ImageDraw.Draw.multiline_text
    :param text: (str or list) the text to be fit into the box
    :param font: (PIL.ImageFont) the font to be used
    :param align: ('left', 'center', 'right') the text alignment
    :param kwargs: (dict) not used, added in arguments to allow for drop-in replacement with other functions
    :return: (fits, wrapped_text):
            fits: (Boolean) whether the message fits
            wrapped_text: (str or list) in this case, the original message unchanged
    """

    # call text_bbox_size to check the size
    check_size, _ = text_bbox_size(font=font, text=text, line_spacing=line_spacing, align=align)

    # check if the text fits and set appropriate text return
    fits = check_size[0] < bbox_size[0] and check_size[1] < bbox_size[1]
    if fits:
        text_return = text
    else:
        text_return = []

    return fits, text_return


# define namedtuple to hold text wrap parameters
wrap_parameter_set = namedtuple('wrap_parameter_set',
                                ['font_path', 'font_size', 'min_spacing', 'split_words', 'truncate', 'wrap_kwargs'],
                                defaults=[None, None, False, None, False, {}])


def draw_text_best_parameters(params_order: tuple, bbox_size: tuple, text: Union[str, list],
                              vertical_align: Union[Literal['center'], int] = 'center',
                              horizontal_align: Union[Literal['center'], int] = 'center',
                              text_align: Literal['left', 'center', 'right'] = 'center', fixed_spacing: int = None,
                              wrap_text: bool = True):
    """
    Draws text in a box of bbox_size, iterating through text parameters in params_order until one works.  If none work,
    text is drawn using the last set of parameters, as much as can fit, and an event is written to the log.

    :param params_order: (tuple) a sequence of text_parameter_set namedtuples, in order of preference
    :param bbox_size: (tuple) the bounding box the text must fit in
    :param text: (str or list) the text to be fit into the box
    :param vertical_align: (int or 'center') number of pixels to offset the image down, or 'center' to center
    :param horizontal_align: (int or 'center') number of pixels to offset the image right, or 'center' to center
    :param text_align: ('left', 'center', 'right') the text alignment
    :param fixed_spacing: (int, default None) an optional fixed line spacing to use for consistency between draws
    :param wrap_text: (Boolean, default True) whether to wrap the text before attempting to draw it in the bounding box
    :return: image, params, spacing (tuple):
                image: (PIL.Image): the text, drawn in the bounding box with the highest-preference parameters possible
                params: (text_parameter_set namedtuple): the text parameters used to draw the image
                spacing: (int): the line spacing used with ImageDraw.Draw.multiline_text
    """

    for wrap_parameters in params_order:
        # select appropriate bbox function
        if not wrap_text:
            bbox_func = check_bbox_no_wrap
        elif wrap_parameters.truncate:
            bbox_func = bbox_text_truncation
        else:
            bbox_func = bbox_text_no_truncation

        # apply fixed spacing if specified
        if fixed_spacing is not None:
            line_spacing = fixed_spacing
        else:
            line_spacing = wrap_parameters.min_spacing

        font = ImageFont.truetype(wrap_parameters.font_path, size=wrap_parameters.font_size)
        fits, wrapped = bbox_func(bbox_size=bbox_size, line_spacing=line_spacing, text=text,
                                  split_words=wrap_parameters.split_words, font=font, align=text_align,
                                  **wrap_parameters.wrap_kwargs)

        if fits:
            break

    if not fits:
        log_msg = "draw_text_best_parameters reached end of params_order without fitting, text: " + str(text)
        helper_logger.warning(log_msg)
        # if does not fit, draw message with last parameters in list
        if isinstance(text, list):
            wrapped = "\n".join(text)
        else:
            wrapped = text

    # at this point 'wrapped' could either be type str or list.  make sure it is type str from here on
    if isinstance(wrapped, list):
        wrapped = "\n".join(wrapped)

    min_text_size, min_draw_target = text_bbox_size(font=font, text=wrapped, line_spacing=line_spacing, align=text_align)

    # now expand text to fit the sign space in a visually pleasing way
    # calculate initial parameters for spacing out the text (and defaults to be used if no solution found)
    num_whitespace_breaks = wrapped.count("\n") + 2
    extra_lines = bbox_size[1] - min_text_size[1]
    spacing_to_add = 0

    # this section allocates the whitespace within multiline text
    # only runs if there are more than 2 breaks (e.g. more than one line) and we are not using fixed_spacing
    if num_whitespace_breaks > 2 and fixed_spacing is None:
        # determine if there is enough whitespace for all breaks to get one more line.  only execute if so.
        whitespace_per_break = extra_lines / num_whitespace_breaks
        if whitespace_per_break >= 1:
            # calculate how much more whitespace we want within the text.  round it up to space out slightly more
            new_whitespace_within = math.ceil(whitespace_per_break * (num_whitespace_breaks - 2))

            # iterate, adding to line_spacing until we have added the desired whitespace
            for i in range(extra_lines):
                text_size, draw_target = text_bbox_size(font=font, text=wrapped, line_spacing=line_spacing + i,
                                                        align=text_align)
                # check if we have added the desired amount of whitespace
                if text_size[1] - min_text_size[1] >= new_whitespace_within:
                    # act appropriately - set parameters if the message still fits, otherwise reset
                    if text_size[1] <= bbox_size[1]:
                        spacing_to_add = i
                    else:
                        text_size = min_text_size
                        draw_target = min_draw_target
                    break
        # if there is not enough whitespace to add, just set text_size and draw_target to min values
        else:
            text_size = min_text_size
            draw_target = min_draw_target
    # if we are using fixed spacing or there is only one line, just set text_size and draw_target to min values
    else:
        text_size = min_text_size
        draw_target = min_draw_target

    if fixed_spacing is not None:
        final_line_spacing = fixed_spacing
    else:
        final_line_spacing = line_spacing + spacing_to_add

    extra_lines = bbox_size[1] - text_size[1]
    extra_cols = bbox_size[0] - text_size[0]
    draw_target = list(draw_target)  # draw target provided as tuple from function, now needs to be mutable

    if vertical_align == 'center':
        draw_target[1] += extra_lines // 2
    elif isinstance(vertical_align, int):
        draw_target[1] += vertical_align
        if vertical_align > extra_lines > 0:
            helper_logger.warning("Vertical align provided pushes drawn text off image.  Text:" + str(text))
    else:
        helper_logger.error("Vertical align must be 'center' or int.  Text:" + str(text))
        raise ValueError("Vertical_align must be 'center' or int.")

    if horizontal_align == 'center':
        draw_target[0] += extra_cols // 2
    elif isinstance(horizontal_align, int):
        draw_target[0] += horizontal_align
        if horizontal_align > extra_cols > 0:
            helper_logger.warning("Horizontal align provided pushes drawn text off image.  Text:" + str(text))
    else:
        helper_logger.error("Horizontal align must be 'center' or int.  Text:" + str(text))
        raise ValueError("Horizontal_align must be 'center' or int.")

    # draw the image using the final parameters
    image = Image.new(mode='1', size=bbox_size, color=0)
    ImageDraw.Draw(image).multiline_text(draw_target, text=wrapped, spacing=final_line_spacing, font=font, fill=1,
                                         anchor='la', align=text_align)

    return image, wrap_parameters, final_line_spacing


def render_day(high: Union[float, int], low: Union[float, int], chance_precipitation: float,
               iso_weekday: int, icon_name: str, language: Literal['english', 'portugues'] = "english"):
    """
    Creates a sub-image with the forecast for a specific day.

    :param high: (float or int): the daily high, in degrees C
    :param low: (float or int): the daily high, in degrees C
    :param chance_precipitation: (float): the chance of precipitation, as a probability (0-1)
    :param iso_weekday: (int): the day of the week according to the ISO system (week starts on Monday)
    :param icon_name: (str): the weather icon to be displayed
    :param language: (str): the language for weekdays to be written in, currently only 'english' and 'portugues'.
    :return: (PIL.Image.Image): an image summarizing the weather for the appropriate day
    """

    day_rendered = Image.new(mode="1", size=(22, 21), color=0)

    # paste day-of-week image
    weekday_img_path = "/".join([root_dir, "assets/weather_images/days_of_week", language,
                                "ISOWEEKDAY_" + str(iso_weekday) + ".png"])
    weekday_img = Image.open(fp=weekday_img_path, mode="r")
    day_rendered.paste(im=weekday_img, box=(0, 6))

    # paste weather icon
    icon_img = Image.open(fp=root_dir + "/assets/weather_images/conditions_icons/" + icon_name + ".png")
    day_rendered.paste(im=icon_img, box=(6, 6))

    # paste the high and the low
    high_below_zero = high < 0
    low_below_zero = low < 0
    high_rounded = "{:>2}".format(round(abs(high)))
    low_rounded = "{:>2}".format(round(abs(low)))

    if high_below_zero:
        day_rendered.paste(im=1, box=(0, 0, 9, 5))

    x_position = 1
    for char in high_rounded:
        number_image = Image.open(fp=root_dir + "/assets/weather_images/numbers/" + char + ".png")
        if high_below_zero:
            number_image = ImageChops.invert(number_image)
        day_rendered.paste(im=number_image, box=(x_position, 0))
        x_position += 4

    if low_below_zero:
        day_rendered.paste(im=1, box=(12, 0, 21, 5))

    x_position = 13
    for char in low_rounded:
        number_image = Image.open(fp=root_dir + "/assets/weather_images/numbers/" + char + ".png")
        if low_below_zero:
            number_image = ImageChops.invert(number_image)
        day_rendered.paste(im=number_image, box=(x_position, 0))
        x_position += 4

    # paste the chance of precipitation
    chance_precipitation_rounded = min(math.floor(chance_precipitation * 6), 5)  # range 0-5
    day_rendered.paste(im=1, box=(10, 5-chance_precipitation_rounded, 11, 5))

    return day_rendered


SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.readonly']


def get_credentials():
    """
    Provided as part of the google api python client libraries.  Copied here for use as a helper function.
    Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns:
        Creds, the obtained credential.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(keys['GOOGLE_TOKEN_PATH']):
        creds = Credentials.from_authorized_user_file(keys['GOOGLE_TOKEN_PATH'], SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google_Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                keys['GOOGLE_CLIENT_SECRET_FILE'], SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(keys['GOOGLE_TOKEN_PATH'], 'w') as token:
            token.write(creds.to_json())

    return creds


def great_circle_distance(lat_1: float, lng_1: float, lat_2: float, lng_2: float):
    """
    Calculates the great-circle distance between two lat-long pairs.  Result returned as float km.
    Assumes spherical earth with radius = 6371 km

    :param lat_1: (float) the latitude of the first location
    :param lng_1: (float) the longitude of the first location
    :param lat_2: (float) the latitude of the second location
    :param lng_2: (float) the longitude of the second location
    :return: distance: (float) the great-circle distance between the two locations, in km
    """

    radius_earth = 6371

    distance = acos(sin(radians(lat_1)) * sin(radians(lat_2)) +
                    cos(radians(lat_1)) * cos(radians(lat_2)) *
                    cos(radians(lng_2) - radians(lng_1))) * radius_earth

    return distance


def sha256_with_default(file_path: pathlib.Path):
    """
    Computes the sha256 hash of an image file in the cache, if it exists.  If the file does not exist,
    returns a dummy string.  Primary purpose is determining if an image file has changed from a server version.
    As such, the dummy string will never match the server hash and avoids file-existence exceptions.

    :param file_path: (Path) the path to the object
    :return: (str) the sha256 hash, or a dummy string if the file does not exist
    """

    if file_path.exists():
        with open(file_path, 'rb') as f:
            file_hash = sha256(f.read()).hexdigest()
    else:
        file_hash = "file does not exist lol"

    return file_hash


def download_file_google_drive(file_id: str, out_path: Union[str, pathlib.Path],
                               drive_service: Resource):
    """
    Downloads the file specified by file_id from the provided Google API Resource drive_service and saves it
    at location out_path.

    :param file_id: (str) the file_id to download
    :param out_path: (str or Path) where to save the file
    :param drive_service: (google api resource) the google API object to use
    :return: None
    """

    if isinstance(out_path, pathlib.Path):
        out_path = out_path.as_posix()

    file_request = drive_service.files().get_media(fileId=file_id)
    file_handler = io.FileIO(out_path, mode='wb')
    downloader = MediaIoBaseDownload(fd=file_handler, request=file_request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        helper_logger.info("Downloading file " + out_path + "progress: " + str(status.progress()))


def is_timezone_naive(d: dt.datetime):
    """
    Determines whether a given datetime object is time-zone naive or not.  Per the datetime docs at:
    https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive

    :param d: (datetime.datetime) the object in question
    :return: (bool) whether the object is timezone-naive or not.
    """

    try:
        utcoffset = d.tzinfo.utcoffset(d) is None
    except AttributeError:
        utcoffset = False

    return d.tzinfo is None and not utcoffset
