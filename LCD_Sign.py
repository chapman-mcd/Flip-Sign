"""
Since this is basically firmware, it should be able to handle a lot of hard coding.  Some of the elements,
especially the events to add, will be difficult to allow the user to send.

1.  ???
2.  List of message objects
3.  Pop random element off list of message objects
4.  When list reaches X entries, start the ??? process in a new thread to update the list of message objects
5.  Repeat with new list of message objects
"""


from MessageClasses import *
from DisplayClasses import *
import googleapiclient.errors
import copy
import random
import time

def GetGoogleSheetData(sheetID,credentials,lstCalendars,lstTemporaryMessages):
    # Create google sheets object
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    try:
        SHEETS = discovery.build('sheets','v4',http=http,discoveryServiceUrl=discoveryUrl)
    except httplib2.ServerNotFoundError:
        raise IOError("No Internet Connection")
    TryAgain = True
    numtimes = 1
    # Service may be unavailable, so try at least 3 times, backing off during
    while TryAgain:
        try:
            # if successful, then update TryAgain to get out of the loop
            result = SHEETS.spreadsheets().values().get(spreadsheetId=sheetID,range="Messages!A:C").execute()
            TryAgain = False
        except googleapiclient.errors.HttpError:
            numtimes += 1
            if numtimes == 4:
                # if we've done this 4 times, raise an IOError to be caught by the calling function
                raise ValueError
            # wait before trying again
            time.sleep(int(random.random()*(2^numtimes - 1)))

    output = []
    for message in result['values']:
        if message[0] == "GCal":
            lstCalendars.append(GoogleCalendar(message[1],credentials))
        elif message[0] == "SpecificDateMessage":
            lstTemporaryMessages.append(SpecificDateMessage(message[1],parse(message[2])))
        elif message[0] == "BasicTextMessage":
            lstTemporaryMessages.append(BasicTextMessage(message[1]))

Display = SerialLCDDisplay(num_lines=2,num_chars=16,device='/dev/cu.usbmodemFD131',frequency=9600,reactiontime=2)

# set up list of transit messages - since this is static, it is done outside the loop
lstTransitMessages = []
lstTransitMessages.append(TransitMessageURL(
    "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=235&routecode=10123&direction=0", "Street Car"))
lstTransitMessages.append(TransitMessageURL(
    "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=145&routecode=10122&direction=0", "Magazine Bus"))
lstTransitMessages.append(TransitMessageURL(
    "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=58&routecode=10121&direction=0", "Tchoup Bus"))

while True:
    # Reset list of calendars and messages to display
    lstCalendars = []
    lstMessagestoDisplay = []
    try:
        # attempt to get new temporary messages and calendars from the google spreadsheet
        # the "check" list is used so that the temporary messages list is only replaced if the internet is up
        check = []
        GetGoogleSheetData("1cmbeXA6WeWJBWl9ge8S-LAuX0zvPBPBpIO1iRZngz8g",get_credentials(),lstCalendars,check)
        lstTemporaryMessages = check
    except IOError:
        # if the internet is down, do nothing
        pass
    except ValueError:
        lstTemporaryMessages.append(BasicTextMessage("No Google Service"))

    # for each calendar in the list of google calendars we want to display
    # if the internet connection check earlier was unsuccessful, then this will be an empty list and the whole block
    # will be skipped
    for cal in lstCalendars:
        # create a temporary list of messages from the google calendar routine
        temp = []
        try:
            temp = cal.create_messages(5)
        except IOError:
            pass
        # for each message we got back from GCal, add that to the list of temporary messages
        for message in temp:
            lstTemporaryMessages.append(message)
    # if it's between 6 and 9 AM, we care a lot more about transit than anything else, add a lot more of those
    if 6 < datetime.datetime.now().hour < 9:
        for i in range(3):
            lstMessagestoDisplay += copy.deepcopy(lstTransitMessages)
    # build the list of messages to display
    lstMessagestoDisplay += copy.deepcopy(lstTransitMessages)
    lstMessagestoDisplay += lstTemporaryMessages
    random.shuffle(lstMessagestoDisplay)

    # for each messages in our list to display, make the display show it then wait for 1 second before sending next
    for message in lstMessagestoDisplay:
        try:
            Display.update(SimpleTransition,message)
        # if we've got an internet connection problem, tell the user about it
        except IOError:
            Display.update(BasicTextMessage("Check Internet"))
        except ValueError:
            # if it's a one time specific date message, then valueerror means the date is passed
            # if it's not a one-time specific date message, then this is a real error
            if isinstance(message,OneTimeSpecificDateMessage):
                pass
            else:
                raise ValueError

        time.sleep(1)
