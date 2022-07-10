# Flip Dot Sign

This is a simple personal project -- want to create a trainstation style flip sign that displays:

- Reminders about birthdays / etc
- When the next bus is coming
- Events from google calendar
- Weather forecasts
- Various cute messages

# Installation

## Prerequisites/Dependencies

```commandline
conda create -n flip-sign
conda activate flip-sign
python -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
python -m pip install beautifulsoup4 pyserial python-dateutil
python -m pip install pillow cachetools
python -m pip install pytest 
```

Note: on raspberry pi (the intended deployment environment) some of pillow's dependencies are missing and must be installed manually.  After configuring ```pyenv``` for python version and virtual environment needs, the remaining dependencies were:
```commandline
sudo apt-get install libjpeg-dev libtiff-dev
python -m pip install pillow
```

## Install

Clone the repo:
```commandline
git clone https://github.com/chapman-mcd/Flip-Sign
```

Various API keys are needed.  A Google API key with access to the Calendar, Sheets and Drive APIs is required, as are keys for Google's Geocoding API and the AccuWeather API.