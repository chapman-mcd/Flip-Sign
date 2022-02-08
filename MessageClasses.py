import textwrap
import datetime
import types
from urllib.request import urlopen
import urllib.error
from dateutil.easter import *
from dateutil.parser import *
from datetime import date
from bs4 import BeautifulSoup
import httplib2
import os
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
          'https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive.readonly']
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Sign Project'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Creds, the obtained credential.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


class GoogleCalendar(object):
    """
    This object represents a google calendar that can be harvested to provide events to show on the sign.
    To initialize, it takes a calendar ID (obtainable from google), and a set of OAuth2.0 credentials which
    provide access to that calendar ID.

    The create_messages method returns a tuple of lists.  First list is a list of OneTimeSpecificDateMessage objects
    which represent the first num_events events in the google calendar that are colored red (colorId = 11).
    Events not colored red are ignored -- this allows the user to select which events will show up on the sign.

    The second list is a list of locations for events that are within 8 days of now.  Those locations can then be used
    to generate weather messages.

    Additionally, the returned message objects will by default have their occasion set as the 'summary' attribute
    of the calendar event.  This can be overridden with any text inside the description of the calendar event
    that is wrapped in double asterisks.
    """
    def __init__(self,calID, credentials):
        self.credentials = credentials
        self.calID = calID

    def create_messages(self, num_events):
        # Authorize credentials and build google calendar object
        try:
            service = build('calendar', 'v3', credentials=self.credentials)
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
        result_weather = []
        # While there are still events in the calendar
        # if there are no more events to display, eventsRequest will be returned as none
        while eventsRequest is not None:
            # eventsResult is a dictionary
            # eventsResult['items'] is a list of dictionaries, each dictionary represents an event
            try:
                eventsResult = eventsRequest.execute()
                events = eventsResult.get('items', [])
            except httplib2.ServerNotFoundError:
                raise IOError("No internet connection")
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

                    daysuntil = (startdatetime.date() - datetime.datetime.now().date()).days
                    # Check if the event starts within ten days
                    if daysuntil < 8:
                        # add location to list of locations to send back, if there is a location
                        try:
                            result_weather.append((event['location'],daysuntil))
                        except KeyError:
                            pass

                    # Create OneTimeSpecificDateMessage object and add it to the list
                    result.append(OneTimeSpecificDateMessage(str(displayText),startdatetime))
                    # check to see if we have the right number of events yet
                    # if we do, send back the list
                    if len(result) == num_events:
                        return (result,result_weather)
            # get ready to request the next page of results from google calendar
            try:
                eventsRequest = service.events().list_next(eventsRequest,eventsResult)
            except httplib2.ServerNotFoundError:
                raise IOError("No Internet Connection")

        # If we've made it to this point, we've gotten to the end of the calendar before reaching num_events
        # In this case, just return the current list.
        return (result, result_weather)


class StringTooLongError(ValueError): pass

class DateMessageInPastError(ValueError): pass

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
        if remainingseconds // divisors[i][0] > 0:
            #if we only have one line left, check the next lower time span to see if it will fit (e.g. use '6wk' instead of '1mo')
            if num_lines-len(result) == 1:
                #if the next lower time span fits on one line, use that
                if len(str(remainingseconds // divisors[i+1][0])+divisors[i+1][1]) <= 3:
                    lengthcheck = str(remainingseconds // divisors[i+1][0])+divisors[i+1][1]
                #otherwise use the original time span
                else:
                    lengthcheck = str(remainingseconds // divisors[i][0]) + divisors[i][1]
            #if we have 2 lines left, just use this time span
            else:
                lengthcheck = str(remainingseconds // divisors[i][0])+divisors[i][1]

            #if the total is not 3 characters, add trailing spaces to keep everything the same length
            if len(lengthcheck) == 2: lengthcheck += " "
            result.append(lengthcheck)
            remainingseconds = remainingseconds % divisors[i][0]
        i += 1
    return result

def improvedtimedeltaformat(timedelta, num_lines = 2):
    """
    Takes in a time span and formats it for display on num_lines of 3 chars each. (e.g. ['9mo', '2d']
    This version is way better, because it better conforms to our idea of "months" - e.g. july 15th is 2 months and 3
    days after may 12th.  Previous version assumed all months had 30 days.

    Max input time delta is 9.999 years.  If this is exceeded, return error.
    :param timedelta: A timedelta formatted as per python datetime module
    :param num_lines: integer number of lines, max 2
    :return: a list 3-character strings of length num_lines representing the time span in text
    """
    # Confirm proper inputs
    assert type(num_lines) == int
    assert isinstance(timedelta,datetime.timedelta)
    assert timedelta.total_seconds() < 315360000
    result = ''
    # if we're in the base case (one line left) try to return the next time unit overloaded (e.g. 72 hours)
    if num_lines == 1:
        try:
            return [timedeltaformatoverload(timedelta)]
        # if the overload function returned error, then we just use the biggest delta we can find
        except ValueError:
            pass
    # calculate total number of months remaining
    months = 0
    # add months until we would pass the specified time delta by adding one more
    while addmonths(datetime.datetime.now(), months + 1) - datetime.datetime.now() < timedelta:
        months += 1
    # if the result is more than 12 months
    if months >= 12:
        # add the number of years, using integer division by 12
        result = str(months // 12) + 'y'
        # if there's extra space int he result, pad it with a space
        if len(result) == 2: result += ' '
        # subtract the even number of years from the remaining time (using the addmonths function and time subtraction)
        remainingtimedelta = timedelta - (addmonths(datetime.datetime.now(),(months // 12) * 12) - datetime.datetime.now())
    # or if we have more than a month but less than a year
    elif months > 0:
        # just add the number of months
        result = str(months)
        # pad with different strings depending on the length -- e.g. return '10M' or '9mo'
        if len(result) == 1:
            result += 'mo'
        else:
            result += 'M'
        # subtract the number of months we added from the remaining time delta to be parsed
        remainingtimedelta = timedelta - (addmonths(datetime.datetime.now(), months) - datetime.datetime.now())
    # if we have less than a month to go, this is easy peasy.  All these time formats are normal.  Use the formula from
    # before.
    elif timedelta.total_seconds() > 1:
        # initialize divisors
        divisors = [[604800, 'wk'], [86400, 'd'], [3600, 'h'], [60, 'm'], [1, 's']]
        for i in range(5):
            # check if this divisor fits
            if timedelta.total_seconds() // divisors[i][0] > 0:
                # if yes, put that in the result and pad if necessary
                result = str(int(timedelta.total_seconds()) // divisors[i][0]) + divisors[i][1]
                if len(result) == 2: result += ' '
                # update remaining time delta and break out of the loop
                remainingtimedelta = datetime.timedelta(seconds = timedelta.total_seconds() % divisors[i][0])
                break
    # if we've gotten this far, the time delta is less than one second.  just return blank
    else:
        result = '   '

    if num_lines == 1:
        return [result]
    else:
        return [result] + improvedtimedeltaformat(remainingtimedelta,num_lines - 1)

def timedeltaformatoverload(timedelta):
    """
    This function ignores the largest possible divisor, and tries to overload the next-largest possible divisor.

    Max input time delta is 9.999 years.  If this is exceeded, return error.
    :param timedelta: A timedelta formatted as per python datetime module
    :param num_lines: integer number of lines, max 2
    :return: a list 3-character strings of length num_lines representing the time span in text
    """


    # calculate total number of months remaining
    months = 0
    # add months until we would pass the specified time delta by adding one more
    while addmonths(datetime.datetime.now(), months + 1) - datetime.datetime.now() < timedelta:
        months += 1
    # if the result is more than 12 months
    if months >= 12:
        # just add the number of months
        result = str(months)
        # check if the result is longer than 2 characters - if so, raise ValueError
        if len(result) > 2:
            raise ValueError
        # if the number of months fits, return it
        else:
            result += 'M'
            return result
    # or if we have more than a month but less than a year
    elif months > 0:
        # initialize divisors
        divisors = [[604800, 'wk'], [86400, 'd'], [3600, 'h'], [60, 'm'], [1, 's']]
        for i in range(5):
            # check if this divisor fits
            if timedelta.total_seconds() // divisors[i][0] > 0:
                # if this divisor fits, create a result for it
                result = str(timedelta.total_seconds() // divisors[i][0]) + divisors[i][1]
                # if that result is too long, raise an error
                if len(result) > 3:
                    raise ValueError
                # if it fits, pad with spaces if necessary and return
                elif len(result) == 2:
                    result += ' '
                return result
    # otherwise we know the time delta is less than a month
    else:
        # initialize divisors and foundfirst variable
        divisors = [[604800, 'wk'], [86400, 'd'], [3600, 'h'], [60, 'm'], [1, 's']]
        foundfirst = False
        for i in range(5):
            # check if this divisor fits
            if timedelta.total_seconds() // divisors[i][0] > 0:
                # if we still haven't found the first divisor that fits, then we've now found it.  update foundfirst
                if not foundfirst:
                    foundfirst = True
                else:
                    # if we had already found a divisor that works
                    result = str(int(timedelta.total_seconds()) // divisors[i][0]) + divisors[i][1]
                    if len(result) > 3:
                        raise ValueError
                    elif len(result) == 2:
                        result += ' '
                    # update remaining time delta and break out of the loop
                    return result

    # if we've finished all the loops, then we have less than a second left over.  raise ValueError to send this through
    # the normal loop
    raise ValueError


def addmonths(indate,months):
    """
    This function takes in a datetime object and adds a number of months to that date, under the colloquial thinking
    that "X month later" refers to the same day of the month, X months from now.  This is obviously an inconsistent
    number of days, but that's how conversation usually runs.  Not all months have every day (e.g. no February 30th).
    For the purposes of this function, 1 month after January 30th returns the last day of February (same treatment
    applied to months with only 30 days)
    :param indate: datetime or date object the months should be added to
    :param months: number of months to be added
    :return: a datetime object representing the same date the specified number of months later
    """

    assert isinstance(indate,datetime.datetime) or isinstance(indate,datetime.date), "Input date must be from datetime"
    assert type(months) == int, "Months must be int."
    indate = datetime.datetime.combine(indate,datetime.time.min)
    year = indate.year + (indate.month + months - 1) // 12
    month = (indate.month + months) - ((indate.month + months - 1) // 12) * 12
    # need to account for the fact that not all months have a 29th,30th and 31st.
    day = indate.day
    i = 0
    result = ""
    # decrease result by one day until it first in the month
    while result == "":
        try:
            result = indate.replace(year=year, month=month, day = day - i)
        except ValueError:
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
    elif "Arriving" in timespanstring:
        return datetime.timedelta(seconds=30)
    else:
        return datetime.timedelta(minutes=int(timespanstring.replace(" min","")))


def parselines(occasion,num_lines=2,num_chars=13,padding=1):
    """
    Parses a string (occasion) into two lines of num_chars length.
    :param occasion: A string of less than num_lines x num_chars in length
    :param num_lines: An integer indicating the number of lines to parse the output into
    :param num_chars: An integer indicating the number of characters in each line
    :param padding: An integer indicating the number of trailing spaces to be added to each line
    :return: a list of strings, each numchars+padding in length, reflecting the parsed output
    """
    assert type(occasion) == str
    assert type(num_chars) == int
    assert type(num_lines) == int
    assert type(padding) == int
    # check length of occasion string and parse into two lines as best possible
    # if the overall string is too long, raise ValueError
    if len(occasion) > num_lines*num_chars:
        raise StringTooLongError('Occasion string too long for display')
    # Otherwise parse it into lines using the textwrap function
    output = textwrap.wrap(occasion, num_chars)
    # if the output is longer than the number of lines available, we've gotta break up some words
    if len(output) > num_lines:
        # re-initialize the output list
        output = [1]*num_lines
        # fill the first line, then the second, until we're out of characters in the input
        for i in range(num_lines):
            output[i] = occasion[i*num_chars:(i+1)*num_chars]
    # if there are lines we didn't use, add those to the list
    if len(output) < num_lines: output += ['']*(num_lines - len(output))
    # pad length of string so that all characters in sign are accounted for
    for i in range(num_lines):
        output[i] = output[i].ljust(num_chars+padding)
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
    def update(self,num_lines,num_chars):
        raise NotImplementedError


class BasicTextMessage(Message):
    """
    Simplest of message classes.  Has a single static message that it displays.
    Takes in a message - either a string or a list of strings
    """
    def __init__(self,message):
        Message.__init__(self)
        self.message = message

    def update(self, num_lines, num_chars):
        print(self.message)
        if type(self.message) == str:
            self.text = parselines(self.message,num_lines=num_lines,num_chars=num_chars,padding=0)
        elif type(self.message) == list:
            self.text = []
            if len(self.message) > num_lines:
                raise ValueError("List of strings too long for display.")
            for i in range(num_lines):
                assert type(self.message[i]) == str, "Items in list for message must be of type string."
                assert len(self.message[i]) < num_chars + 1, "Each string in message must be " +num_chars+ " chars or less."
                self.text.append(self.message[i].ljust(num_chars))


class DateMessage(Message):
    """
    A subclass of message which displays the amount of time until a specific date and time.
    This "level" of the class structure provides a common update() method which will be used
    by all different subclasses.  The different subclasses of DateMessage will initialize differently
    and will all have different ways of determining the latest date using the nextdate() method.
    """
    def __init__(self):
        # this class should not be initialized directly -- only subclasses should be initialized
        Message.__init__(self)

    def nextdate(self):
        """
        Subclasses must overwrite this method.  It must return a datetime object representing the time
        that the message is counting down to.
        :return: a datetime object
        """
        raise NotImplementedError

    def update(self,num_lines,num_chars):
        # get next date from nextdate function, calculate time delta and format time delta
        """
        Updates self.text with the remaining time and to the specifications of the display.
        Returns nothing.
        :param num_lines: integer indicating number of lines in the display
        :param num_chars: integer indicating number of characters in each line of the display
        """
        # this print statement is for monitoring purposes - it relies on all subclasses having an "occasion" attribute
        print(self.occasion)
        self.text = []
        nextdate = self.nextdate()
        timedelta = nextdate - datetime.datetime.now()
        formattedtimedelta = improvedtimedeltaformat(timedelta, min(num_lines, 2))

        # if there are more lines than the timedelta function allows, pad the returned list with blanks
        if num_lines > 2:
            formattedtimedelta += ['   ']*(num_lines - 2)
        formattedtext = parselines(self.occasion[:num_lines * num_chars], num_lines=num_lines,
                                   num_chars=num_chars-4, padding=1)
        for i in range(num_lines):
            self.text.append(formattedtext[i]+formattedtimedelta[i])


class SpecificDateMessage(DateMessage):
    """
    A SpecificDateMessage is a subclass of Message that occurs on the same date each year.
    (e.g. Valentine's Day, Tax Day)
    To initialize, it needs a string of no more than 26 characters describing the occasion and a date.
    The date can be of an arbitrary year, since the time span will be calculated based on the next occurrence.
    """
    def __init__(self, Occasion, Date):
        Message.__init__(self)
        # ensure initialization arguments are of the proper type
        assert type(Occasion) == str
        assert isinstance(Date,datetime.datetime) or isinstance(Date,datetime.date), "Date passed must be datetime object."
        if isinstance(Date,datetime.date): Date = datetime.datetime.combine(Date,datetime.time.min)
        self.date = Date
        self.occasion = Occasion

    def nextdate(self):
        #determine the date of this year's occasion
        thisyeardate = self.date.replace(year = datetime.datetime.now().year)
        # if the date hasn't passed yet this year, return this year date
        if thisyeardate - self.date.today() > datetime.timedelta():
            return thisyeardate
        # if the date has passed this year, return the date in the next year
        else:
            return self.date.replace(year = datetime.datetime.now().year + 1)


class OneTimeSpecificDateMessage(SpecificDateMessage):
    """
    This subclass of SpecificDateMessage does not reoccur every year -- it is a single event.
    As a result, it doesn't check the version of itself in the next year.
    Raises ValueError if the date/time has already passed and the update() method is called.
    """
    def __init__(self, Occasion, Date):
        SpecificDateMessage.__init__(self, Occasion, Date)

    def nextdate(self):
        # if the date hasn't passed, return the date
        if self.date - datetime.datetime.now() > datetime.timedelta():
            return self.date
        # if the date has passed, raise ValueError
        else:
            raise DateMessageInPastError("Specific Datemessage: " + self.occasion[0] + " has passed.")


class VaryingDateMessage(DateMessage):
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
        self.occasion = Occasion
        self.datefunction = datefunction

    def nextdate(self):
        #use date function to update the appropriate date for this year
        thisyeardate = datetime.datetime.combine(self.datefunction(), datetime.time.min)

        # if the date hasn't passed yet this year, calculate time delta to the date in this year
        if thisyeardate - datetime.datetime.now() > datetime.timedelta():
            return thisyeardate
        # if the date has passed this year, calculate time delta to the date in next year
        else:
            return thisyeardate.replace(year = datetime.datetime.now().year + 1)


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
        self.friendlyname = friendlyname
    def update(self, num_lines, num_chars):
        errors = "None"
        try:
            # Pull the http information, read it into memory, and parse using BeautifulSoup
            rtaurl = urlopen(self.url)
            content = rtaurl.read()
            soup = BeautifulSoup(content, "html.parser")

            # Parse arrival information from the next two buses/streetcars out of the soup

            bus = []
            time = []
            bus.append(soup.find(id="bus1").text.strip())
            time.append(soup.find(id="ts1").text.strip())
            bus.append(soup.find(id="bus2").text.strip())
            time.append(soup.find(id="ts2").text.strip())
            bus.append(soup.find(id="bus3").text.strip())
            time.append(soup.find(id="ts3").text.strip())
        except urllib.error.URLError:
            raise IOError("No Internet Connection.")


        # If no information is available, get cheeky about RTA's performance
        if bus[0] == "n/a":
            errors = "RTAData"

        if errors == "None":
        # If information is available, format the info for consumption
            for i in range(3):
                # for all of the 3 returns (RTA will only send back info about the first 3 buses)
                try:
                    timedelta = parseRTATimeDelta(time[i])
                    time[i] = improvedtimedeltaformat(timedelta,1)[0]
                except ValueError:
                # if we get a ValueError, that means we've tried to pass some text to the timedelta function
                # that means that there's no bus at this position, so fill with a dash
                    bus[i] = " - "
                    time[i] = " - "
                except IndexError:
                    print("Caught index error")

        # get the friendly name into the right length and number of lines
        friendlyname = parselines(self.friendlyname, num_lines=num_lines, num_chars=num_chars-8, padding=1)

        # determine what to put into the time and bus side of the message
        bustext = []
        if errors == "None":
            for i in range(num_lines):
                if i <= 3:
                    bustext.append(str(bus[i]) + " " + str(time[i]))
                else:
                    bustext.append('       ')
        else:
            bustext = ["No Data", "Lol RTA"]
            for i in range(num_lines - 2):
                bustext.append('       ')

        # Update self.text with all the info we've generated
        self.text = []
        for i in range(num_lines):
            self.text.append(friendlyname[i]+bustext[i])
