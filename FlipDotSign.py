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
from MessageGenerator import *
from WeatherClasses import *
import os
import io
from datetime import time as dt_time
from googleapiclient.http import MediaIoBaseDownload

z = SimpleTransition('', 'z')

fontsize = 9
minfontsize = 3
wait_time = 300

base_directory = os.path.dirname(__file__)
weather_API_key = open(os.path.join(base_directory, 'WeatherKey.txt')).readline()
default_font_path = os.path.join(base_directory, 'PressStart2P.ttf')
google_sheet_id = open(os.path.join(base_directory, 'GoogleSheet.txt')).readline()
google_location_key = open(os.path.join(base_directory, 'Google_Location_Key.txt')).readline()
home_location = input('Please enter zip code for home location: ')

def GetGoogleSheetData(sheetID, credentials, lstCalendars, lstTemporaryMessages):
    # Create google sheets object
    result = {}
    try:
        SHEETS = build('sheets', 'v4', credentials=credentials)
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
        elif processmessage[0] == "WeatherLocation":
            try:
                location = WeatherLocation(processmessage[1], processmessage[2], weather_API_key,
                                           default_font_path, google_location_key=google_location_key)
                lstTemporaryMessages.append(location.ten_day_forecast(rows=21, columns=168, daysfromnow=0))
            except urllib.error.HTTPError:
                print("Problem with Weather API")

# get google drive folder name
with open('Google_Drive_Folder.txt') as f:
    google_drive_folder = f.readline()

# If system is running on mac (development)
if os.uname().sysname == "Darwin":
    Display = FakeFlipDotDisplay(columns=168, rows=21, serialinterface=None, layout=None)
    transition_functions = [SimpleTransition]
    # override wait_time for faster running / debugging
    wait_time = 5
# if system is running on raspberry linux (production)
elif os.uname().sysname == "Linux":
    port = '/dev/ttyS0'
    serialinterface = serial.Serial(port=port, baudrate=57600, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS,
                                    timeout=1, stopbits=serial.STOPBITS_ONE)
    Display = FlipDotDisplay(columns=168, rows=21, serialinterface=serialinterface, layout=Generate_Layout_2())
    transition_functions = [SimpleTransition, dissolve_changes_only]
else:
    raise ValueError("Unsupported platform - must be MacOS or Linux")

# set up list of transit messages - since this is static, it is done outside the loop
lstTransitMessages = []
# lstTransitMessages.append(TransitMessageURL(
#     "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=235&routecode=10123&direction=0", "Street Car"))
# lstTransitMessages.append(TransitMessageURL(
#     "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=145&routecode=10122&direction=0", "Magazine Bus"))
# lstTransitMessages.append(TransitMessageURL(
#     "http://www.norta.com/Mobile/whers-my-busdetail.aspx?stopcode=58&routecode=10121&direction=0", "Tchoup Bus"))


q = datetime(1990, 1, 1, 1, 1)

start_time = dt_time(6,45)
end_time = dt_time(23,00)

while True:
    q = datetime(1990, 1, 1, 1, 1)
    now_time_fix = q.now().time()
    if start_time < now_time_fix < end_time:
        # Reset list of calendars and messages to display
        lstCalendars = []
        lstMessagestoDisplay = []
        lstTemporaryMessages = []
        try:
            # attempt to get new temporary messages and calendars from the google spreadsheet
            # the "check" list is used so that the temporary messages list is only replaced if the internet is up
            check = []
            GetGoogleSheetData(google_sheet_id, get_credentials(), lstCalendars, check)
            lstTemporaryMessages = check
            print("Pulled google sheet data")
        except IOError:
            # if the internet is down, do nothing
            print("Found no internet connection when pulling google sheet data.")
            pass
        except ValueError:
            print("No google service when opening google sheet.")
            lstTemporaryMessages.append(BasicTextMessage("No Google Service"))

        # get files from google drive
        try:
            service = build('drive', 'v3', credentials=get_credentials())

            # Call the Drive v3 API
            results = service.files().list(q=google_drive_folder,
                                           pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
            else:
                for item in items:
                    print(u'{0} ({1})'.format(item['name'], item['id']))
                    file_id = item['id']
                    request = service.files().get_media(fileId=file_id)
                    fh = io.FileIO("./drive_images/" + item['name'], mode='wb')
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        print("Download %d%%." % int(status.progress() * 100))
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')

        # add google drive files to messages to display
        for file in os.listdir("./drive_images"):
            lstTemporaryMessages.append(Image.open("./drive_images/" + file).convert(mode='1'))

        # for each calendar in the list of google calendars we want to display
        # if the internet connection check earlier was unsuccessful, then this will be an empty list and the whole block
        # will be skipped
        for cal in lstCalendars:
            # create a temporary list of messages from the google calendar routine
            temp = []
            try:
                # run the message creation
                in_tuple = cal.create_messages(5)
                # the first element of the tuple is a list of event messages
                temp = in_tuple[0]
                # the second element of the tuple is a list of tuples
                # first element of each tuple is the location string
                # second element is the number of days until that event
                for location in in_tuple[1]:
                    # turn the first element of each tuple into a weather location
                    weather_location = WeatherLocation(location[0], location[0], weather_API_key,
                                                       default_font_path, google_location_key=google_location_key,
                                                       home_location=home_location)
                    # get the forecast - go ahead a max of five days or until the event starts
                    num_of_days_until = min(5, location[1])
                    weather_forecast = weather_location.ten_day_forecast(rows=21, columns=168,
                                                                         daysfromnow=num_of_days_until)
                    temp.append(weather_forecast)
                print("Created messages from google calendar.")
            except IOError:
                pass
                print("No internet connection when pulling from google calendar.")
            # for each message we got back from GCal, add that to the list of temporary messages
            for message in temp:
                lstTemporaryMessages.append(message)
        # if it's between 6 and 9 AM, we care a lot more about transit than anything else, add a lot more of those
        if 6 < datetime.now().hour < 9:
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
                               font=ImageFont.truetype(default_font_path, size=9))
                time.sleep(wait_time)
            # if we've got an internet connection problem, tell the user about it
            except IOError:
                Display.update(SimpleTransition, BasicTextMessage("Check Internet"),
                               font=ImageFont.truetype(default_font_path, size=9))
            except DateMessageInPastError:
                # if it's a one time specific date message, then valueerror means the date is passed
                # if it's not a one-time specific date message, then this is a real error
                if isinstance(message, OneTimeSpecificDateMessage):
                    print("Had a case where a one-time specific date message was in the past.")
                    pass
            except StringTooLongError:
                trysize = fontsize - 1
                while trysize >= minfontsize:
                    try:
                        Display.update(SimpleTransition, message,
                                       font=ImageFont.truetype(default_font_path, size=trysize))
                        time.sleep(wait_time)
                        break
                    except StringTooLongError:
                        trysize += -1

        # give the dots some exercise
        # flip to all white and then all black
        # PIL wants the image size as width, height so run the tuple backwards
        Display.show(Image.new('1', Display.get_size()[::-1], 1))
        time.sleep(1)
        Display.show(Image.new('1', Display.get_size()[::-1], 0))
