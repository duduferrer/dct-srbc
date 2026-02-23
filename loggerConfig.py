import logging
import sys


def setup_logger():
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%d-%m-%Y %H:%M:%S')

    file_handler = logging.FileHandler('dct_srbc_log.txt', mode='a', encoding='utf-8')
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.DEBUG)


    logger = logging.getLogger("DCT_SRBC")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


log = setup_logger()