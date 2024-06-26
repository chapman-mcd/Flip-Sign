from flip_sign.displays import FlipDotDisplay
from flip_sign.message_generation import GoogleSheetMessageFactory, recursive_message_generate, BasicTextMessage
from flip_sign.assets import root_dir
import serial
import datetime
import random
from flip_sign.assets import keys
from google.auth.exceptions import TransportError
from urllib.error import URLError
from socket import timeout as SocketTimeoutError
import flip_sign.config as config
import time
import logging

run_sign_logger = logging.getLogger(name="flip_sign.run_sign")


def run_sign():
    # logging setup
    fh = logging.FileHandler(filename=root_dir + "/cache/flip_sign.log")
    fh.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(fmt=formatter)
    ch.setFormatter(fmt=formatter)

    logging.getLogger('').addHandler(fh)
    logging.getLogger('').addHandler(ch)

    # base variables and objects
    config.HOME_LOCATION = input("Enter zip code for home location:")

    port = "/dev/ttyS0"
    serial_interface = serial.Serial(port=port, baudrate=57600, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS,
                                     timeout=1, stopbits=serial.STOPBITS_ONE)
    display = FlipDotDisplay(serial_interface=serial_interface)

    # main "event" loop
    while True:
        # update message list
        updated = False
        n_fails = 0
        while not updated:
            run_sign_logger.info("Attempting update.  n_fails: " + str(n_fails))
            try:
                messages = recursive_message_generate([GoogleSheetMessageFactory(sheet_id=keys['GoogleSheet'])])
                random.shuffle(messages)
                updated = True
            except (TransportError, URLError, SocketTimeoutError) as e:
                run_sign_logger.warning("Internet error generating messages.  Error details: " + str(e))
                wait_time = 2 * (2 ** n_fails)
                retry_time = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
                display.update(BasicTextMessage("Internet error generating messages.  Trying again at " +
                                                retry_time.isoformat()))
                time.sleep(wait_time)
            except Exception as e:
                display.update(BasicTextMessage("Unexpected error generating messages.  Stopping.  Error: " + str(e)))
                raise

        run_sign_logger.info("Message list update complete.")

        n_messages = len(messages)
        message_render_fails = 0
        message_init_fails = 0
        # run through generated messages
        for i, message in enumerate(messages):
            # observe quiet hours
            if datetime.datetime.now().time() > config.END_TIME:  # if after end time, use tomorrow start
                next_start = datetime.datetime.combine(datetime.date.today() + datetime.timedelta(days=1),
                                                       config.START_TIME)
                time.sleep((next_start - datetime.datetime.now()).total_seconds())
                break  # break display loop to force message list update
            if datetime.datetime.now().time() < config.START_TIME:  # if before start time, use today
                next_start = datetime.datetime.combine(datetime.date.today(), config.START_TIME)
                time.sleep((next_start - datetime.datetime.now()).total_seconds())
                break  # break display loop to force message list update

            # skip messages with display=False and increment init failure if applicable
            if not message:
                if message.init_failure:
                    message_init_fails += 1
                continue

            # attempt to update display until successful, counting number of failures
            update_successful = display.update(message)
            if not update_successful:
                message_render_fails += 1
                continue

            run_sign_logger.info("Sent message {} of {} to sign.".format(i, n_messages))

            time.sleep(config.WAIT_TIME.total_seconds())

        # end of cycle through messages - surface errors if there were any
        if message_render_fails > 0 or message_init_fails > 0:
            cycle_message = ("Cycle completed.  Message init failures: {}\nMessage render failures:{}"
                             .format(message_init_fails, message_render_fails))
            display.update(BasicTextMessage(cycle_message, wrap_text=False))
            time.sleep(config.WAIT_TIME.total_seconds())

        # end of cycle flip all yellow then all black
        display.cycle_dots()


if __name__ == '__main__':
    run_sign()
