# Flip Dot Sign

This is a simple personal project -- want to create a trainstation style flip sign that displays:

- Reminders about birthdays / etc
- When the next bus is coming
- Events from google calendar
- Weather forecasts
- Various cute messages

# Installation

```
conda create -n flip-sign
conda activate flip-sign
python -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
conda install beautifulsoup4
python -m pip install pyserial python-dateutil pillow
```