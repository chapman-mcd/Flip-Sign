from flip_sign.run_sign import run_sign
import logging

logging.basicConfig(level=logging.DEBUG)
logging.root.handlers = []  # remove initial console handler, will be replaced

run_sign()
