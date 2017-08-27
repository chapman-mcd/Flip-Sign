from urllib.request import urlopen
import json
import os
from PIL import Image
from PIL import ImageChops
from PIL import ImageFont
from MessageClasses import parselines
from MessageClasses import StringTooLongError
from DisplayClasses import message_to_image


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
        self.use_google = self.google_location_key is not None and self.home_location is not None

        self.url = None
        #  Determine proper URL to use for this location
        # if using the google method then feed everything through the google APIs
        if self.use_google:
            # determine if the location can be parsed using google's geocoding API
            geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json?address=' + \
                          self.location_string.replace(' ','+') + '&key=' + self.google_location_key
            geocode_json = json.loads(urlopen(geocode_url).read().decode('utf-8'))
            if geocode_json['status'] == 'OK':
                #now we know it can be parsed using the geocoding API, find out if it is more than 100 miles from home
                directions_url = 'https://maps.googleapis.com/maps/api/directions/json?' + 'origin=place_id:' + \
                    geocode_json['results'][0]['place_id'] + '&destination=' + self.home_location + '&key=' + \
                                 self.google_location_key
                directions_json = json.loads(urlopen(directions_url).read().decode('utf-8'))
                # if the directions API returns zero results that means there's no way to drive (it must be far away)
                # or if the distance is more than 160934 meters
                if directions_json['status'] == 'ZERO_RESULTS' or \
                    directions_json['routes'][0]['legs'][0]['distance']['value'] > 160934:
                    self.url = 'http://api.wunderground.com/api/' + self.api_key + '/forecast10day/q/' + \
                               str(geocode_json['results'][0]['geometry']['location']['lat']) + ',' + \
                               str(geocode_json['results'][0]['geometry']['location']['lng']) + '.json'
                # if we get here then our location is within 100 miles of home_location
                else:
                    pass

            else:
                pass

        # if not using google, then just generate the URL directly
        else:
            self.url = 'http://api.wunderground.com/api/' + self.api_key + '/forecast10day/q/' + location_string + '.json'

    def ten_day_forecast(self, rows, columns, daysfromnow):
        """
        Updates the weather information and returns an image object for display on the sign
        :return: an image object representing the weather forecast
        """
        assert rows == 21
        assert columns == 168

        if self.url == None:
            return None

        url_opened = urlopen(self.url)
        url_decoded = url_opened.read().decode('utf-8')
        json_out = json.loads(url_decoded)
        forecast = json_out['forecast']['simpleforecast']['forecastday']

        weather_icon_lookup = {
            'clear': 'sunny',
            'unknown': 'tstorms',
            'mostlysunny': 'partlycloudy',
            'partlysunny': 'mostlycloudy',
            'hazy': 'fog',
            'flurries': 'snow',
        }

        weather_forecast_images = []

        # need to parse the list of stuff from the json into a list of image objects
        # run through the first five days of the forecast from the json
        for i in range(daysfromnow, min(10, daysfromnow + 5)):
            this_image = Image.new('1', (22, 21), 0)
            # paste the day of week in the bottom right
            dow_path = os.path.join(self.dir, forecast[i]['date']['weekday_short'].upper() + ".png")
            dow_image = Image.open(dow_path)
            this_image.paste(dow_image, (0, 6))

            # write the daily high in the top left
            high = forecast[i]['high']['fahrenheit']
            # determine whether the high is below zero
            if high.find("-") == -1:
                below_zero = False
            else:
                below_zero = True

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
            chance_of_rain_rounded = round(forecast[i]['pop']/20)
            this_image.paste(1, (xposition, 5 - chance_of_rain_rounded, xposition + 1, 5))
            xposition += 2

            # write the daily low in the top right
            low = forecast[i]['low']['fahrenheit']
            # determine whether the low is below zero
            if low.find("-") == -1:
                below_zero = False
            else:
                below_zero = True

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


            # now it's time to write the weather icon
            # determine whether there is a "chance" of the weather
            chance_of = not forecast[i]['icon'].find('chance') == -1
            # so you're telling me there's a chance...

            icon = forecast[i]['icon'].replace('chance','')

            # run thr icon through our lookup dictionary to sanitize it down into stuff we have icons for
            # if it's not in there, we have an icon for it
            if icon in weather_icon_lookup:
                icon = weather_icon_lookup[icon]

            # paste weather icon into the image
            icon_path = os.path.join(self.dir, icon +".png")
            icon_image = Image.open(icon_path)
            # if it's a chance, then invert the colors on the image
            if chance_of:
                icon_image = ImageChops.invert(icon_image)
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