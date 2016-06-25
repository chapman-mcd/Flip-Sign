import textwrap
import datetime
import types
import urllib2
from dateutil.easter import *
from dateutil.parser import *
from datetime import date
from bs4 import BeautifulSoup

# Begin setup for Google Calendar object
import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

class GoogleCalendar(object):
    """
    This object represents a google calendar that can be harvested to provide events to show on the sign.
    To initialize, it takes a calendar ID (obtainable from google), and a set of OAuth2.0 credentials which
    provide access to that calendar ID.

    The create_messages method returns a list of OneTimeSpecificDateMessage objects which represent the first
    num_events events in the google calendar that are colored red (colorId = 11).  Events not colored red are
    ignored -- this allows the user to select which events will show up on the sign.

    Additionally, the returned message objects will by default have their occasion set as the 'summary' attribute
    of the calendar event.  This can be overridden with any text inside the description of the calendar event
    that is wrapped in double asterisks.
    """
    def __init__(self,calID,credentials):
        self.credentials = credentials
        self.calID = calID
    def create_messages(self,num_events):
        # Authorize credentials and build google calendar object
        http = self.credentials.authorize(httplib2.Http())
        try:
            service = discovery.build('calendar','v3',http=http)
        except httplib2.ServerNotFoundError:
            raise IOError("No internet connection")

        # determine current time and put into correct format
        # determine end time as 213 days from now and put that into correct format
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        endtime = datetime.datetime.utcnow() + datetime.timedelta(days=213)
        endtime = endtime.isoformat() + 'Z'

        # creates an events request object that describes what to get from google

        eventsRequest = service.events().list(
            calendarId=self.calID, timeMin=now, timeMax=endtime, singleEvents=True,
            orderBy='startTime')

        result = []
        # While there are still events in the calendar
        # if there are no more events to display, eventsRequest will be returned as none
        while eventsRequest is not None:
            # eventsResult is a dictionary
            # eventsResult['items'] is a list of dictionaries, each dictionary represents an event
            eventsResult = eventsRequest.execute()
            events = eventsResult.get('items', [])
            # check events on this page of results
            for event in events:
                # if the event has been colored red, then we want to create an event for it
                try:
                    blnColor = int(event['colorId']) == 11
                except KeyError:
                    blnColor = False
                if blnColor:
                    # Determine start time to calculate from
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    startdatetime = parse(start,ignoretz=True)
                    # Check if we have a name override in the text of the event
                    try:
                        blnOverride = event['description'].count('**') == 2
                    except KeyError:
                        blnOverride = False
                    # If we do, new event name will be the text wrapped in stars
                    if blnOverride:
                        displayText = event['description'].split('**')[1]
                    # If not, use the summary attribute as the name
                    else:
                        displayText = event['summary']
                    # Create OneTimeSpecificDateMessage object and add it to the list
                    result.append(OneTimeSpecificDateMessage(str(displayText),startdatetime))
                    # check to see if we have the right number of events yet
                    # if we do, send back the list
                    if len(result) == num_events:
                        return result
            # get ready to request the next page of results from google calendar
            eventsRequest = service.events().list_next(eventsRequest,eventsResult)

        # If we've made it to this point, we've gotten to the end of the calendar before reaching num_events
        # In this case, just return the current list.
        return result







def MardiGrasDate():
    """
    A function to return the date of Mardi Gras in the current year.
    :return: a date formatted as per the python datetime module, representing Mardi Gras of the current year
    """
    thiseaster = easter(date.today().year)
    MardiGras = thiseaster - datetime.timedelta(days=47)
    return MardiGras

def timedeltaformat(timedelta, num_lines = 2):
    """
    Takes in a time span and formats it for display on num_lines of 3 chars each. (e.g. ['9mo', '2d']
    :param timedelta: A timedelta formatted as per python datetime module
    :param num_lines: integer number of lines, max 2
    :return: a list 3-character strings of length num_lines representing the time span in text
    """
    # Confirm proper inputs
    assert 0 <num_lines < 3
    assert type(num_lines) == int
    assert isinstance(timedelta,datetime.timedelta)
    #Initialize loop variables
    result = []
    remainingseconds = int(timedelta.total_seconds())
    divisors = [[31536000,'y'],[2592000,'mo'],[604800,'wk'],[86400,'d'],[3600,'h'],[60,'m'],[1,'s']]
    i = 0
    #loop while we still have lines to fill
    while len(result) < num_lines:
        #stop looping if we don't have any more time spans to check
        if i > 5:
            break
        #if there is a nonzero number of this time span
        if remainingseconds / divisors[i][0] > 0:
            #if we only have one line left, check the next lower time span to see if it will fit (e.g. use '6wk' instead of '1mo')
            if num_lines-len(result) == 1:
                #if the next lower time span fits on one line, use that
                if len(str(remainingseconds/divisors[i+1][0])+divisors[i+1][1]) <= 3:
                    lengthcheck = str(remainingseconds/divisors[i+1][0])+divisors[i+1][1]
                #otherwise use the original time span
                else:
                    lengthcheck = str(remainingseconds / divisors[i][0]) + divisors[i][1]
            #if we have 2 lines left, just use this time span
            else:
                lengthcheck = str(remainingseconds/divisors[i][0])+divisors[i][1]

            #if the total is not 3 characters, add trailing spaces to keep everything the same length
            if len(lengthcheck) == 2: lengthcheck += " "
            result.append(lengthcheck)
            remainingseconds = remainingseconds % divisors[i][0]
        i += 1
    return result

def parseRTATimeDelta(timespanstring):
    """
    Takes in a string time span formatted along the New Orleans RTA Website.
    Returns a proper datetime timedelta that represents the same amount of time.
    :param timespanstring: A string representing a time span, from the New Orleans RTA real-time data website
    :return: a datetime timedelta, representing the same time span
    """
    if "hr" in timespanstring:
        lstSpanString = timespanstring.split()
        return datetime.timedelta(hours=int(lstSpanString[0]),minutes=int(lstSpanString[2]))
    else:
        return datetime.timedelta(minutes=int(timespanstring.replace(" min","")))



def parselines(occasion,num_chars=13,padding=1):
    """
    Parses a string (occasion) into two lines of num_chars length.
    :param occasion: A string of less than 2x num_chars in length
    :param num_chars: An integer indicating the number of characters in each line
    :param padding: An integer indicating the number of trailing spaces to be added to each line
    :return: a list of strings, each numchars+padding in length, reflecting the parsed output
    """
    assert type(occasion) == str
    assert type(num_chars) == int
    assert type(padding) == int
    # check length of occasion string and parse into two lines as best possible
    if len(occasion) > 2*num_chars:
        raise ValueError('Occasion string too long for display')
    output = textwrap.wrap(occasion, num_chars)
    if len(output) > 2:
        output = [1, 1]
        output[0] = occasion[0:num_chars]
        output[1] = occasion[num_chars:]
    if len(output) == 1: output.append("")
    # pad length of string so that all characters in sign are accounted for
    output[0] = output[0].ljust(num_chars+padding)
    output[1] = output[1].ljust(num_chars+padding)
    return output


class Message(object):
    """
    Catch-all class.  Only method is get_message, which returns the message.
    The message is a list of strings, where each string represents one line of the message.
    Subclasses will define the update method, which will vary by subclass.
    """


    def __init__(self):
        self.text = []
    def get_message(self):
        return self.text
    def __str__(self):
        return str(self.text)
    def update(self):
        raise NotImplementedError

class BasicTextMessage(Message):
    """
    Simplest of message classes.  Has a single static message that it displays.
    Takes in a message - either a string or a list of strings of length 2
    """
    def __init__(self,message):
        Message.__init__(self)
        if type(message) == str:
            self.text = parselines(message,17,0)
        elif type(message) == list:
            self.text = []
            if len(message) > 2:
                raise ValueError("List of strings too long for display.")
            for i in range(2):
                assert type(message[i]) == str, "Items in list for message must be of type string."
                assert len(message[i]) < 18, "Each string in message must be 17 chars or less."
            self.text.append(message[0].ljust(17))
            self.text.append(message[1].ljust(17))


class SpecificDateMessage(Message):
    """
    A SpecificDateMessage is a subclass of Message that occurs on the same date each year.
    (e.g. Valentine's Day, Tax Day)
    To initialize, it needs a string of no more than 26 characters describing the occasion and a date.
    The date can be of an arbitrary year, since the time span will be calculated based on the next occurrence.
    """
    def __init__(self,Occasion,Date):
        Message.__init__(self)
        # ensure initialization arguments are of the proper type
        assert isinstance(Date,datetime.date), "Date passed must be datetime object."
        self.date = Date
        self.occasion = parselines(Occasion)

    def update(self):
        #determine the date of this year's occasion
        thisyeardate = self.date.replace(year = self.date.today().year)
        # if the date hasn't passed yet this year, calculate time delta to the date in this year
        if thisyeardate - self.date.today() > datetime.timedelta():
            timedelta = thisyeardate - self.date.today()
        # if the date has passed this year, calculate time delta to the date in next year
        else:
            timedelta = self.date.replace(year = self.date.today().year + 1) - self.date.today()
        # update self.text with the occasion string, and the time delta, formatted using timedeltaformat function
        self.text = []
        self.text.append(self.occasion[0] + timedeltaformat(timedelta)[0])
        self.text.append(self.occasion[1] + timedeltaformat(timedelta)[1])

class OneTimeSpecificDateMessage(SpecificDateMessage):
    """
    This subclass of SpecificDateMessage does not reoccur every year -- it is a single event.
    As a result, it doesn't check the version of itself in the next year.
    Raises ValueError if the date/time has already passed and the update() method is called.
    """
    def __init__(self,Occasion,Date):
        SpecificDateMessage.__init__(self,Occasion,Date)
    def update(self):
        # if the date hasn't passed, calculate time delta
        if self.date - datetime.datetime.now() > datetime.timedelta():
            timedelta = self.date - datetime.datetime.now()
        # if the date has passed, raise ValueError
        else:
            raise ValueError("Specific Datemessage: " + self.occasion[0] + " has passed.")
        # update self.text with the occasion string, and the time delta, formatted using timedeltaformat function
        self.text = []
        self.text.append(self.occasion[0] + timedeltaformat(timedelta)[0])
        self.text.append(self.occasion[1] + timedeltaformat(timedelta)[1])

class VaryingDateMessage(Message):
    """
    A VaryingDateMessage is a subclass of Message that does not occur on the same date each year.
    (e.g. Mardi Gras, Chinese New Year, Super Bowl Sunday)
    To initialize, it needs a string of no more than 26 characters describing the occasion, and a function
    requiring no arguments which returns the current-year occurrence of the date when called.
    """
    def __init__(self,Occasion,datefunction):
        Message.__init__(self)
        assert type(Occasion) == str, "Occasion must be string."
        assert isinstance(datefunction,(types.FunctionType, types.BuiltinFunctionType)), "DateFunction must be a function."
        self.occasion = parselines(Occasion)
        self.datefunction = datefunction

    def update(self):
        #use date function to update the appropriate date for this year
        thisyeardate = self.datefunction()

        #remainder of this is the same as the specificdatemessage function

        # if the date hasn't passed yet this year, calculate time delta to the date in this year
        if thisyeardate - thisyeardate.today() > datetime.timedelta():
            timedelta = thisyeardate - thisyeardate.today()
        # if the date has passed this year, calculate time delta to the date in next year
        else:
            timedelta = thisyeardate.replace(year = thisyeardate.today().year + 1) - thisyeardate.today()
        # update self.text with the occasion string, and the time delta, formatted using timedeltaformat function
        self.text = []
        self.text.append(self.occasion[0] + timedeltaformat(timedelta)[0])
        self.text.append(self.occasion[1] + timedeltaformat(timedelta)[1])

class TransitMessageURL(Message):
    """
    A TransitMessage is a subclass of message that shows arrival information from the New Orleans RTA.
    In contrast with other possible transit messages, it accesses this data by scraping the RTA website.
    In order to initialize, it needs a URL(string) from which to access the arrival information and a friendly
    name (also string) to refer to the route by.
    """
    def __init__(self,url,friendlyname):
        # Initialize according to overall message class
        Message.__init__(self)
        # Confirm adherence to input rules
        assert type(url) == str, "Url must be passed in as string."
        # Assign self variables and parse friendly name into two lines
        self.url = url
        self.friendlyname = parselines(friendlyname,9,1)
    def update(self):
        errors = "None"
        try:
            # Pull the http information, read it into memory, and parse using BeautifulSoup
            rtaurl = urllib2.urlopen(self.url)
            content = rtaurl.read()
            soup = BeautifulSoup(content, "html.parser")

            # Parse arrival information from the next two buses/streetcars out of the soup

            bus1 = soup.find(id="bus1").string.strip()
            time1 = soup.find(id="ts1").string.strip()
            bus2 = soup.find(id="bus2").string.strip()
            time2 = soup.find(id="ts2").string.strip()
        except urllib2.URLError:
            raise IOError("No Internet Connection.")


        # If no information is available, get cheeky about RTA's performance
        if bus1 == "n/a":
            errors = "RTAData"

        if errors == "None":
        # If information is available, format the info for consumption
        # If we've gotten this far, there must be at least one set of time info
        # Parse the first set of info without checking, then use try/except on second set
            timedelta1 = parseRTATimeDelta(time1)
            time1 = timedeltaformat(timedelta1, 1)[0]
            try:
                timedelta2 = parseRTATimeDelta(time2)
                time2 = timedeltaformat(timedelta2,1)[0]
            except ValueError:
                bus2 = " - "
                time2 = " - "
        # Update self.text with all the info we've generated
        self.text = []
        if errors == "None":
            self.text.append(self.friendlyname[0] + str(bus1) + " " + str(time1))
            self.text.append(self.friendlyname[1] + str(bus2) + " " + str(time2))
        elif errors == "Interwebs":
            self.text.append(self.friendlyname[0] + "No Net ")
            self.text.append(self.friendlyname[1] + "Connect")
        else:
            self.text.append(self.friendlyname[0] + "No Data")
            self.text.append(self.friendlyname[1] + "Lol RTA")


#TODO:
# - make objects display-independent -- give the update method num_lines and width parameters

# Testing google calendar onetimemessage creator

Gcal = GoogleCalendar("ugqtbs0n8j2781647ammtahcag@group.calendar.google.com",get_credentials())
messages = Gcal.create_messages(2)
messages[0].update()
messages[1].update()
print messages[0], messages[1]

# Testing basic text message class
joke = BasicTextMessage("Napoleon Work Lol Finish       Nvr")
print joke

joke2 = BasicTextMessage(["Napoleon Work Lol", "Finish      Never"])
print joke2

# testing Transit Message URL Class

StCharles = TransitMessageURL("http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=235&routecode=10123&direction=0","Streetcar")
StCharles.update()
print StCharles.get_message()

MagBus = TransitMessageURL("http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=145&routecode=10122&direction=0","Magazine Bus")
MagBus.update()
print MagBus

TchoupBus = TransitMessageURL("http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=58&routecode=10121&direction=0","Tchoup Bus")
TchoupBus.update()
print TchoupBus



# testing specific date message class

# newdate = datetime.date(2010,10,1)
# print type(newdate)
# print newdate
# newdelta = newdate.today() - newdate
# print newdelta
# print newdelta > datetime.timedelta()

# testing text wrap handling

# specdate = SpecificDateMessage("test testtest test",datetime.date(2016,1,1))
# print specdate.occasion
# specdate.update()
# print specdate.get_message()
# specdate = SpecificDateMessage("Janet Birthday",datetime.date(2011,3,24))
# print specdate.occasion
# specdate.update()
# print specdate.get_message()
# specdate = SpecificDateMessage("Napolean Construct Finish",newdate)
# print specdate.occasion
# specdate.update()
# print specdate.get_message()

# testing varying date message class

yoyo = VaryingDateMessage('Mardi Gras Woo Woo',MardiGrasDate)
yoyo.update()
print yoyo

# testing timedeltaformat function
#
# bigtimedelta = datetime.timedelta(weeks=65,days=50,hours=1)
# print timedeltaformat(bigtimedelta)
# print timedeltaformat(bigtimedelta,1)
#
# mediumtimedelta = datetime.timedelta(weeks=10,days=5,hours=1,minutes=15)
# print timedeltaformat(mediumtimedelta)
# print timedeltaformat(mediumtimedelta,1)
