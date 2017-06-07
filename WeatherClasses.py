from urllib.request import urlopen
import urllib.error

keyfile = open('WeatherKey.txt','r')
key = keyfile.readline()
keyfile.close()

class WeatherLocation(object):
    """
    Weather locations are a specific type of message - they will have an 'update' method but no get_message method.
    Instead, they will have a get_image method, since the weather message will effectively be displayed as an image.
    
    Weather data will come from the weather underground API.
    """
    def __init__(self,location_string,key):
        """
        :param location_string: this location string will be fed to the weather underground API to determine the
        location.  it could be a zip code, etc.
        :param key: this is the API key to be used to access the weather underground API
        """

        self.location_string = location_string
        self.api_key = key
        self.url =

    def update(self):
        """
        Updates the weather information inside the object for later retrieval via the get_image method.
        :return: returns nothing
        """
