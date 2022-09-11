import logging
from urllib.request import Request, urlopen
import datetime as dt
from cachetools import cached, TLRUCache
import json
import gzip

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
    # confirm start time is in the future
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
