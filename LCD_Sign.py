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
import copy
import random
import time

def GetGoogleSheetData(sheetID,credentials):
    # Create google sheets object
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
    SHEETS = discovery.build('sheets','v4',http=http,discoveryServiceUrl=discoveryUrl)
    result = SHEETS.spreadsheets().values().get(spreadsheetId=sheetID,range="Messages!A:C").execute()
    output = []
    for message in result['values']:
        if message[0] == "GCal":
            lstCalendars.append(GoogleCalendar(message[1],credentials))
        if message[0] == "SpecificDateMessage":
            lstTemporaryMessages.append(SpecificDateMessage(message[1],parse(message[2])))

Display = SerialLCDDisplay(num_lines=2,num_chars=16,device='/dev/cu.usbmodemFD131',frequency=9600,reactiontime=2)

while True:
    lstCalendars = []
    lstTemporaryMessages = []
    lstMessagestoDisplay = []
    lstTransitMessages = []
    lstTransitMessages.append(TransitMessageURL(
        "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=235&routecode=10123&direction=0","Street Car"))
    lstTransitMessages.append(TransitMessageURL(
        "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=145&routecode=10122&direction=0","Magazine Bus"))
    lstTransitMessages.append(TransitMessageURL(
        "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=58&routecode=10121&direction=0","Tchoup Bus"))
    GetGoogleSheetData("1cmbeXA6WeWJBWl9ge8S-LAuX0zvPBPBpIO1iRZngz8g",get_credentials())
    for cal in lstCalendars:
        temp = cal.create_messages(5)
        for message in temp:
            lstTemporaryMessages.append(message)
    if 6 < datetime.datetime.now().hour < 9:
        for i in range(3):
            lstMessagestoDisplay += copy.deepcopy(lstTransitMessages)
    lstMessagestoDisplay += copy.deepcopy(lstTransitMessages)
    lstMessagestoDisplay += lstTemporaryMessages
    random.shuffle(lstMessagestoDisplay)

    for message in lstMessagestoDisplay:
        Display.update(SimpleTransition,message)
        time.sleep(1)
