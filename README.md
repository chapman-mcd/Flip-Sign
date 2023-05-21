# Flip Dot Sign

This is a simple personal project -- I wanted to create a trainstation-style flip sign that could display:

- Countdowns to birthdays and holidays
- When the next bus is coming
- Countdowns to events from Google Calendar
- Weather forecasts
- Various cute text messages (song lyrics)
- Art by my kids (via images in Google Drive)

As they say, a .gif is worth a thousand words.

# Background

This project was my original motivation for learning to code / learning python, starting in 2015.  Creating the initial version of the sign was a fantastic introduction into the world of coding and APIs.

By 2022, my coding abilities had grown substantially since the sign was completed.  While I had new integration ideas, the `hello_world`-type code of the sign was a major limiting factor to any kind of new features.  A ground-up rewrite was in order.  Just as the initial sign was an opportunity to learn python, so the rewrite was a great way to take the next step and learn about packaging, logging, and test-driven development.

The flip sign has been a great playground for me, and I hope it will remain so for future steps forward in coding.

# Construction / Hardware



TODO: Describe construction of the sign
- Rear lattice
- Framing
- AlfaZeta
- French Cleat

# Installation & Usage

## Prerequisites/Dependencies

On raspberry pi (the primary deployment environment) Pillow is missing some key outside-python dependencies.  To install:
```commandline
sudo apt-get install libjpeg-dev libtiff-dev
```

Now (after creating a virtual environment) install dependencies using `requirements.txt`.
```commandline
conda create -n flip-sign
conda activate flip-sign
python -m pip install -r requirements.txt
```

## Install

Clone the repo:
```commandline
git clone https://github.com/chapman-mcd/Flip-Sign
```

## Batteries Not Included

Various API keys are needed.  A [Google Client Secret for OAuth2.0](https://support.google.com/cloud/answer/6158849) is required, with user-authorized access to the Calendar, Sheets and Drive APIs.  Also required are keys for [Google's Geocoding API](https://support.google.com/cloud/answer/6158849) and the [AccuWeather API](https://developer.accuweather.com).

These keys are expected in single-line files in `/flip_sign/assets/keys` and should be linked in by updating the `flip_sign.assets` module with the appropriate filenames.

Finally, the sign initially extracts messages from a Google Sheet.  The `sheet_id` for that sheet needs to be provided to `flip_sign.assets` as well.  The sheet ID for any Google Sheet can be extracted from the URL.

## Run

```commandline
python run_sign.py
```