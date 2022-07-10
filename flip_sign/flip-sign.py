## The main python script which is run to control the sign
from factories import GoogleSheetFactory
from helpers import recursive_factory_runner
import serial
import os
from datetime import time as dt_time
