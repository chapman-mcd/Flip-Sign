from pathlib import Path
import os

root_dir = os.path.dirname(os.path.abspath(__file__))

key_names = ['AccuweatherAPI', 'GoogleAPIs', 'GoogleLocationAPI', 'GoogleDriveFolder', 'GoogleSheet']
key_paths = ['WeatherKey.txt', 'client_secret.json', 'Google_Location_Key.txt',
             'Google_Drive_Folder.txt', 'GoogleSheet.txt']
keys = {name: Path(root_dir + "/assets/keys/" + path).read_text() for name, path in zip(key_names, key_paths)}

font_names = ['PressStart2P', 'DatDot']
font_paths = ['PressStart2P.ttf', 'DatDot_edited_v1.ttf']
fonts = {name: root_dir + "/assets/fonts/" + path for name, path in zip(font_names, font_paths)}