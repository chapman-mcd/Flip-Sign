import logging
from urllib.request import Request, urlopen
import datetime as dt
from cachetools import cached, TLRUCache
import json
from PIL import ImageFont, ImageDraw, Image
import gzip
import re
import textwrap

logger_name = 'flip_sign.helpers'


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
        logging.getLogger(logger_name).warning("Unhandled URL type for AccuWeather Cache.  Url: " + key_str)
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
    current_time = dt.datetime.now()

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


def text_bbox_size(font: ImageFont, text: list or str, line_spacing: int, align: str):
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
                wrapped_text: the text, wrapped into lines
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
