import logging
import logging.handlers
# import os
'''
日志模块
'''
# LOG_PATH = (os.path.dirname(os.getcwd()) + '/Logs/')
# LOG_PATH = ('/var/log/')
LOG_PATH=""
LOG_FILENAME = LOG_PATH+'imuEhall.log'
logger = logging.getLogger()

def set_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=10485760, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

set_logger()