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
import serial
from TransitionFunctions import *
from Generate_Layout import *


z = SimpleTransition('', 'z')

fontsize = 9
minfontsize = 3


def GetGoogleSheetData(sheetID, credentials, lstCalendars, lstTemporaryMessages):
    # Create google sheets object
    http = credentials.authorize(httplib2.Http())
    discoveryurl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    result = {}
    try:
        SHEETS = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryurl)
    except httplib2.ServerNotFoundError:
        raise IOError("No Internet Connection")
    try_again = True
    num_times = 1
    # Service may be unavailable, so try at least 3 times, backing off during
    while try_again:
        try:
            # if successful, then update TryAgain to get out of the loop
            result = SHEETS.spreadsheets().values().get(spreadsheetId=sheetID, range="Messages!A:C").execute()
            try_again = False
        except googleapiclient.errors.HttpError:
            num_times += 1
            if num_times == 4:
                # if we've done this 4 times, raise an ValueError to be caught by the calling function
                raise ValueError
            # wait before trying again
            time.sleep(int(random.random() * (2 ^ num_times - 1)))
        except httplib2.ServerNotFoundError:
            raise IOError("No Internet Connection")

    for processmessage in result['values']:
        if processmessage[0] == "GCal":
            lstCalendars.append(GoogleCalendar(processmessage[1], credentials))
        elif processmessage[0] == "SpecificDateMessage":
            lstTemporaryMessages.append(SpecificDateMessage(processmessage[1], parse(processmessage[2])))
        elif processmessage[0] == "BasicTextMessage":
            lstTemporaryMessages.append(BasicTextMessage(processmessage[1]))
        elif processmessage[0] == "MessageGenerator":
            lstGeneratedMessages = Message_Generator(processmessage[1],processmessage[2]).create_messages()
            for Generated_Message in lstGeneratedMessages:
                lstTemporaryMessages.append(Generated_Message)

port = '/dev/ttyS0'

serialinterface = serial.Serial(port=port, baudrate=57600, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS,
                                timeout=1, stopbits=serial.STOPBITS_ONE)

Display = FlipDotDisplay(columns=168, rows=21, serialinterface=serialinterface, layout=Generate_Layout_2())

transition_functions = [SimpleTransition, dissolve_changes_only]

# set up list of transit messages - since this is static, it is done outside the loop
lstTransitMessages = []
# lstTransitMessages.append(TransitMessageURL(
#     "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=235&routecode=10123&direction=0", "Street Car"))
# lstTransitMessages.append(TransitMessageURL(
#     "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=145&routecode=10122&direction=0", "Magazine Bus"))
# lstTransitMessages.append(TransitMessageURL(
#     "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=58&routecode=10121&direction=0", "Tchoup Bus"))


q = datetime.datetime(1990,1,1,1,1)

start_time = datetime.time(6,45)
end_time = datetime.time(23,00)

while True:
    if start_time < q.now().time() < end_time:
        # Reset list of calendars and messages to display
        lstCalendars = []
        lstMessagestoDisplay = []
        lstTemporaryMessages = []
        try:
            # attempt to get new temporary messages and calendars from the google spreadsheet
            # the "check" list is used so that the temporary messages list is only replaced if the internet is up
            check = []
            GetGoogleSheetData("1cmbeXA6WeWJBWl9ge8S-LAuX0zvPBPBpIO1iRZngz8g", get_credentials(), lstCalendars, check)
            lstTemporaryMessages = check
            print("Pulled google sheet data")
        except IOError:
            # if the internet is down, do nothing
            print("Found no internet connection when pulling google sheet data.")
            pass
        except ValueError:
            print("No google service when opening google sheet.")
            lstTemporaryMessages.append(BasicTextMessage("No Google Service"))

        # for each calendar in the list of google calendars we want to display
        # if the internet connection check earlier was unsuccessful, then this will be an empty list and the whole block
        # will be skipped
        for cal in lstCalendars:
            # create a temporary list of messages from the google calendar routine
            temp = []
            try:
                temp = cal.create_messages(5)
                print("Created messages from google calendar.")
            except IOError:
                pass
                print("No internet connection when pulling from google calendar.")
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
                Display.update(random.choice(transition_functions), message,
                               font=ImageFont.truetype('/home/pi/Documents/flip-sign/PressStart2P.ttf', size=9))
                time.sleep(300)
            # if we've got an internet connection problem, tell the user about it
            except IOError:
                Display.update(SimpleTransition, BasicTextMessage("Check Internet"),
                               font=ImageFont.truetype('/home/pi/Documents/flip-sign/PressStart2P.ttf', size=9))
            except DateMessageInPastError:
                # if it's a one time specific date message, then valueerror means the date is passed
                # if it's not a one-time specific date message, then this is a real error
                if isinstance(message, OneTimeSpecificDateMessage):
                    print("Had a case where a one-time specific date message was in the past.")
                    pass
            except StringTooLongError:
                trysize = fontsize
                while trysize >= minfontsize:
                    try:
                        Display.update(SimpleTransition, message,
                                       font=ImageFont.truetype('/Users/cmcd/PycharmProjects/Sign/PressStart2P.ttf',
                                                               size=trysize))
                        break
                    except StringTooLongError:
                        trysize += -1



        serialinterface.write(reset_command())
        time.sleep(1)
        serialinterface.write(all_black_command())
