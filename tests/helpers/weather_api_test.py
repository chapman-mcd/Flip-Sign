import flip_sign.helpers
import time
from unittest.mock import patch, MagicMock
from urllib.request import Request
from urllib.error import HTTPError

# Tests the time-to-use (TTU) function for the accuweather cache
def test_api_cache_ttu():
    # test result for 5-day forecast request
    five_day_url = ('http://dataservice.accuweather.com/forecasts/v1/daily/5day/', '431090', "?apikey=IFDAHGDjkdf",
                "&metric=true&details=true")
    time_now = time.monotonic()
    five_day_ttu = flip_sign.helpers.accuweather_cache_ttu(_key=five_day_url, value=None, now=time_now)
    assert five_day_ttu == time_now + 4 * 60 * 60  # cache 5-day forecast results for 4 hours

    # test result for location request
    location_url = ('http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?', 'apikey=rOIUgdaj',
        "&q=-23.43298432,24.543098543")
    location_ttu = flip_sign.helpers.accuweather_cache_ttu(_key=location_url, value=None, now=time_now)
    assert location_ttu == time_now + 30 * 24 * 60 * 60 # cache location lookup results for 30 days

# Tests the logging feature for the TTU function
def test_api_cache_ttu_logging(caplog):
    time_now = time.monotonic()
    other_ttu = flip_sign.helpers.accuweather_cache_ttu(_key=('http://www.yourmom.com',), value=None, now=time_now)
    assert caplog.records[-1].getMessage() == "Unhandled URL type for AccuWeather Cache.  Url: " +\
           'http://www.yourmom.com'
    assert other_ttu == time_now + 10 * 60

test_location = "36.252304,-85.710587" # Nameless, Tennessee
weather_loc_base_url = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?'
test_location_url_tuple = (weather_loc_base_url, "apikey=GRAIOUGRGH", "&q=", test_location)

# test Nameless, TN
f = open('./helpers/test_assets/nameless_tn_location_resp.txt', mode='rb')
urlopen_result = f.read()
f.close()
urlopen_mock = MagicMock()
req = Request(''.join(test_location_url_tuple), headers={"Accept-Encoding": "gzip, deflate"})
urlopen_mock(req).read = MagicMock(return_value = urlopen_result)

# Tests that the correct value is returned from caching
@patch('flip_sign.helpers.urlopen', urlopen_mock)
def test_api_requests_basic():
    resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    assert resp['Key'] == '335689' # Ensure returns correct result

    resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    urlopen_mock(req).read.assert_called_once() # mock is only called once due to caching

# Confirms that the method is called again after cache expires
@patch('flip_sign.helpers.urlopen', urlopen_mock)
def test_api_requests_cache_expiry():
    urlopen_mock(req).read.reset_mock()
    flip_sign.helpers._accuweather_cache.clear()
    resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    urlopen_mock(req).read.assert_called_once()  # mock is only called once due to caching

    flip_sign.helpers._accuweather_cache.expire(time=2e10) # simulate time expiry using the 'expire' method
    resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    assert len(urlopen_mock(req).read.mock_calls) == 2 # confirm mock is called again


# Confirm exceptions are not cached
@patch('flip_sign.helpers.urlopen', urlopen_mock)
def test_api_requests_cache_exceptions():
    err = HTTPError(url=''.join(test_location_url_tuple), code=403, msg='Got an error', hdrs=None, fp=None)
    urlopen_mock(req).read.configure_mock(side_effect=err)
    flip_sign.helpers._accuweather_cache.clear()
    try:
        resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    except HTTPError:
        pass

    # make another request to confirm the exception was not cached
    urlopen_mock(req).read.configure_mock(side_effect=None)
    resp = flip_sign.helpers.accuweather_api_request(test_location_url_tuple)
    assert resp['Key'] == '335689'  # Ensure returns correct result

# HTTP Errors:
# 400 Bad Request
# 403 Forbidden
