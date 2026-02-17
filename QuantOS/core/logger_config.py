import logging
import os

class CustomFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        
        # Mask current User's home dynamically
        User_home = os.path.expanduser("~")
        if User_home in msg:
             msg = msg.replace(User_home, "~")
             
        return msg

def get_console_handler():
    handler = logging.StreamHandler()
    # Using a clean format for console output
    handler.setFormatter(CustomFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
    return handler

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(get_console_handler())
    logger.propagate = False
    return logger
