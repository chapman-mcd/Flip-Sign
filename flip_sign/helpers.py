import logging; logger_name = 'flip_sign.helpers'
from urllib.request import Request, urlopen
from urllib.parse import quote
from cachetools import cached, TLRUCache
import json, gzip



def accuweather_cache_ttu(_key, value, now):
    """
    Function which returns the expiry time for cached results from the accuweather API.  Location requests are cached
    for 30 days, 5-day forecast results are cached for 4 hours.  Unexpected events are written to the log.

    :param _key: in this case, the accuweather URL
    :param value: the API response.  provided by cachetools, but not relevant here.
    :param now: current value of timer
    :return: (float) expiration time for the cached request
    """

    # join the url into a single string
    key_str = ''.join(_key[0]) # function call is in a tuple (arg1, arg2, ..).  need to access first/only arg

    # use presence of '5day' to determine 5-day forecast
    if '5day' in key_str:
        increment = 4 * 60 * 60 # store 5-day forecasts for 4 hours
    # use present of 'geoposition' to detect location request
    elif 'geoposition' in key_str:
        increment = 30 * 24 * 60 * 60 # store location requests for 30 days
    else:
        # if a different URL is passed, write to the log and cache for 10 minutes only
        logging.getLogger(logger_name).warning("Unhandled URL type for AccuWeather Cache.  Url: " + key_str)
        increment = 10 * 60

    return now + increment

_accuweather_cache = TLRUCache(maxsize=10, ttu=accuweather_cache_ttu)
@cached(cache=_accuweather_cache)
def accuweather_api_request(url: object) -> object:
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