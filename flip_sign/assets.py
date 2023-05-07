from pathlib import Path
import os

root_dir = os.path.dirname(os.path.abspath(__file__))

key_names = ['AccuweatherAPI', 'GoogleLocationAPI', 'GoogleDriveFolder', 'GoogleSheet', 'Google_Calendar_Test']
key_paths = ['WeatherKey.txt',  'Google_Location_Key.txt',
             'Google_Drive_Folder.txt', 'GoogleSheet.txt', 'Google_Calendar_Test_ID.txt']
keys = {name: Path(root_dir + "/assets/keys/" + path).read_text() for name, path in zip(key_names, key_paths)}
keys['GOOGLE_CLIENT_SECRET_FILE'] = Path(root_dir + "/assets/keys/client_secret.json")
keys['GOOGLE_TOKEN_PATH'] = Path(root_dir + "/assets/keys/token.json")

font_names = ['PressStart2P', 'DatDot']
font_paths = ['PressStart2P.ttf', 'DatDot_edited_v1.ttf']
fonts = {name: root_dir + "/assets/fonts/" + path for name, path in zip(font_names, font_paths)}