from MessageClasses import *
from urllib.request import urlopen
import urllib.error
from bs4 import BeautifulSoup

class Message_Generator(object):
    """
    This class generates basic text messages using a web URL and a parsing method found in a local file.
    It has an init method and a create_messages method.
    TODO: Make the Google Calendar class a subclass of this one.
    """
    def __init__(self,url,file_path):
        """
        Initializes th class
        :param url: a URL that will be opened to generate the message
        :param file_path: a file containing a single python statement on each line that can be evaluated to generate 
        a desired message. this statement will assume that the URL has been parsed using BeautifulSoup4 into an 
        object called 'soup'.  Each line in the file at file_path will be evaluated into a different message.
        """
        self.url = url
        self.file_path = file_path


    def create_messages(self):
        opened = urlopen(self.url)
        content = opened.read()

        soup = BeautifulSoup(content, "lxml")

        f = open(self.file_path,'r')
        commands = f.readlines()
        f.close()

        messages = []
        for line in commands:
            messages.append(BasicTextMessage(eval(line)))

        return messages
