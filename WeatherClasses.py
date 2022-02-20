import operator
from urllib.request import Request, urlopen
from urllib.parse import quote
import gzip
import json
import os
from math import acos, sin, cos
from PIL import Image
from PIL import ImageChops
from PIL import ImageFont
from MessageClasses import parselines
from MessageClasses import StringTooLongError
from DisplayClasses import message_to_image
from cachetools import cachedmethod, TTLCache
from datetime import datetime


class WeatherLocation(object):
    """
    Weather locations are a specific type of message - they will have an 'update' method but no get_message method.
    Instead, they will have a get_image method, since the weather message will effectively be displayed as an image.
    
    Weather data will come from the weather underground API.
    """
    def __init__(self, location_string, label, key, font, google_location_key=None, home_location=None):
        """
        
        :param location_string: a string to be passed to the weather underground API that identifies the location
        :param label: text to display labeling the weather
        :param key: an API key (text) for the weather underground API
        :param font: a relative path to a truetype or otf font
        """

        self.location_string = location_string
        self.api_key = key
        self.label = label
        self.dir = os.path.join(os.path.dirname(__file__), 'Weather_Images')
        self.font = font
        self.google_location_key = google_location_key
        self.home_location = home_location
        self.distance_to_home = 0
        self.locations_cache = TTLCache(maxsize=32, ttl=60*60*24) # cache location info for 1 day
        self.forecast_cache = TTLCache(maxsize=32, ttl=60*60*4) # cache weather forecasts for 4 hours

        self.forecast_url = None
        self.accuweather_location_code = None

        # stash base URLs for simpler code and easier updates
        geocode_base_url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
        weather_loc_base_url = 'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?'

        # Get lat-long of target
        response = self.location_api_request((geocode_base_url, quote(self.location_string),
                                              "&key=", self.google_location_key))
        self.location_lat_long = response['results'][0]['geometry']['location']

        # calculate distance to home
        if self.home_location is not None:
            # Get lat-long of home location
            response = self.location_api_request((geocode_base_url, quote(self.home_location),
                                                  "&key=", self.google_location_key))
            self.home_lat_long = response['results'][0]['geometry']['location']

            #Calculate great-circle distance
            radius_earth = 6371 #km
            self.distance_to_home = acos(sin(self.home_lat_long['lat'])*sin(self.location_lat_long['lat']) +
                                         cos(self.home_lat_long['lat'])*cos(self.location_lat_long['lat']) +
                                         cos(self.location_lat_long['lng']-self.home_lat_long['lng'])) * radius_earth

        if self.home_location is None or self.distance_to_home > 160:
            # Pull location code from API
            response = self.location_api_request((weather_loc_base_url, "apikey=", self.api_key, "&q=",
                                                  str(self.location_lat_long['lat']), ",",
                                                  str(self.location_lat_long['lng'])))
            self.accuweather_location_code = response['Key']
            # Build forecast request URL
            self.forecast_url = 'http://dataservice.accuweather.com/forecasts/v1/daily/5day/' + self.accuweather_location_code +\
                "?apikey=" + self.api_key + "&metric=true&details=true"

    @cachedmethod(cache=operator.attrgetter('locations_cache'))
    def location_api_request(self, url):
        """
        Cached class method for making api requests.  Tested only against the google geocoding API and
        the AccuWeather API.  No errors are handled in this function, all are passed along.

        :param url: string, tuple or list.  Will be packed together to make the API request.
        :return: the API response, processed into a python variable
        """
        url = ''.join(url)
        req = Request(url, headers={"Accept-Encoding": "gzip, deflate"})
        response = json.loads(gzip.decompress(urlopen(req).read()))

        return response

    @cachedmethod(cache=operator.attrgetter('forecast_cache'))
    def ten_day_forecast(self, rows, columns, daysfromnow):
        """
        Updates the weather information and returns an image object for display on the sign
        :return: an image object representing the weather forecast
        """
        assert rows == 21
        assert columns == 168

        if self.forecast_url is None:
            return None

        req = Request(self.forecast_url, headers={"Accept-Encoding": "gzip, deflate"})
        response = json.loads(gzip.decompress(urlopen(req).read()))
        forecast = response['DailyForecasts']

        weather_icon_lookup = {
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
            30: 'sunny', 31: 'snow', 32: 'cloudy'
        }

        weather_forecast_images = []

        # dictionary to turn ISO weekdays into short day-of-week strings
        dow_short = {1: 'MON', 2: 'TUE', 3: 'WED', 4: 'THU', 5: 'FRI', 6: 'SAT', 7: 'SUN'}

        # need to parse the list of stuff from the json into a list of image objects
        # run through the first five days of the forecast from the json
        for i in range(daysfromnow, 5):
            this_image = Image.new('1', (22, 21), 0)
            # paste the day of week in the bottom right
            dow_iso = datetime.fromisoformat(forecast[i]['Date']).isoweekday()
            dow_path = os.path.join(self.dir, dow_short[dow_iso].upper() + ".png")
            dow_image = Image.open(dow_path)
            this_image.paste(dow_image, (0, 6))

            # write the daily high in the top left
            high = int(round(forecast[i]['Temperature']['Maximum']['Value']))
            # determine whether the high is below zero
            if high >= 0:
                below_zero = False
            else:
                below_zero = True
            high = str(high)

            xposition = 0
            # if we have extra space before the high, we need to pad the top
            if len(high) < 3:
                for j in range(3-len(high)):
                    # get the path for the blank number image
                    blank_image_path = os.path.join(self.dir, "blank_number.png")
                    blank_image = Image.open(blank_image_path)
                    # if the high is below zero, we need to invert the blank image and add a row of on pixels
                    if below_zero:
                        ImageChops.invert(blank_image)
                        this_image.paste(1, (xposition + 3, 0, xposition + 4, 5))
                    # paste the blank image into the actual image and increment xposition
                    this_image.paste(blank_image, (xposition, 0))
                    xposition += 4

            # write the high temperature to the image
            for char in high:
                # replace the minus with a blank number, otherwise use the number itself
                if char == "-":
                    lookup_char = "blank_number"
                else:
                    lookup_char = char

                image_path = os.path.join(self.dir, lookup_char + ".png")
                number_image = Image.open(image_path)
                # if the high is below zero, we need to invert the number image and add a row of on pixels
                if below_zero:
                    number_image = ImageChops.invert(number_image)
                    this_image.paste(1, (xposition + 3, 0, xposition + 4, 5))
                this_image.paste(number_image, (xposition, 0))
                xposition += 4

            # write the percentage chance of precipitation to the image
            day_chance_rain = forecast[i]['Day']['PrecipitationProbability']
            night_chance_rain = forecast[i]['Night']['PrecipitationProbability']
            chance_of_rain_rounded = round(max(day_chance_rain, night_chance_rain) / 20)
            this_image.paste(1, (xposition, 5 - chance_of_rain_rounded, xposition + 1, 5))
            xposition += 2

            # write the daily low in the top right
            low = int(round(forecast[i]['Temperature']['Minimum']['Value']))
            # determine whether the low is below zero
            if low >= 0:
                below_zero = False
            else:
                below_zero = True
            low = str(low)

            # if we're below zero on the daily low, add a stripe of yellow pixels
            if below_zero:
                this_image.paste(1, (xposition-1, 0, xposition, 5))

            # if the low has three digits, we need to do some massaging on it
            if len(low) > 2:
                # if the low has three digits and is below zero, that's cool - just remove the minus
                if below_zero:
                    low = low[1:]
                # if the low has three digits and it's above zero, that means it's over 100.  That's hot.
                # just write ++ for the daily low
                else:
                    low = "++"

            # now it's time to write the numbers for the low
            for char in low:
                # replace any minus with a blank number, otherwise use the number itself
                if char == "-":
                    lookup_char = "blank_number"
                else:
                    lookup_char = char

                image_path = os.path.join(self.dir, lookup_char + ".png")
                number_image = Image.open(image_path)
                # if the high is below zero, we need to invert the number image and add a row of on pixels
                if below_zero:
                    number_image = ImageChops.invert(number_image)
                    this_image.paste(1, (xposition + 3, 0, xposition + 4, 5))
                this_image.paste(number_image, (xposition, 0))
                xposition += 4

            # run the icon through our lookup dictionary
            icon = weather_icon_lookup[forecast[i]['Day']['Icon']]

            # paste weather icon into the image
            icon_path = os.path.join(self.dir, icon +".png")
            icon_image = Image.open(icon_path)
            this_image.paste(icon_image, (6, 6))

            weather_forecast_images.append(this_image)

        output = Image.new('1', (columns, rows), 0)
        k = 21
        for thing in weather_forecast_images[::-1]:
            output.paste(thing, (columns - k, 0))
            k += 22
        # initialize label maker situation
        fontfound = False
        trysize = 20
        minsize = 8
        # iterate until we've found a font size and label length that works
        while not fontfound:
            tryfont = ImageFont.truetype(self.font, size=trysize)
            teststring = 'thequickbrownfoxjumpsoverthelazydogTHEQUICKBROWNFOXJUMPSOVERTHELAZYDOG'
            testsize = tryfont.getsize(teststring)
            num_chars = int((columns - 22*5) // (testsize[0]/len(teststring)))
            num_lines = rows // testsize[1]
            try:
                label_parsed = parselines(self.label, num_lines, num_chars, padding=0)
                fontfound = True
            except StringTooLongError:
                if trysize > minsize:
                    trysize -= 1
                else:
                    self.label = self.label[:-1]

        label_image = message_to_image(label_parsed, columns=columns - 22*5, rows=rows,max_width=columns - 22*5,
                                       total_height=testsize[1]*len(label_parsed) + 1, font=tryfont,
                                       display_height_chars=len(label_parsed))

        output.paste(label_image,(0,0))

        return output