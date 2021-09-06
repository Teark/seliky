"""
close print in rf，because testing framework has it's own logger
If you need to generate log files, open the log folder and configure the path as you need
"""

# import os
import logging
import sys

from datetime import datetime
from colorama import Fore, Style

now_time = str(datetime.now())[:-7]
# log_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "report")
# log_file = os.path.join(log_folder, now_time.strftime('%Y-%m-%d') + ".log")
# if not os.path.exists(log_folder):
#     os.makedirs(log_folder)

_logger = logging.getLogger('selek')
# f_file = logging.FileHandler(log_file, encoding='utf-8')
_logger.setLevel(logging.DEBUG)

# f_file.setLevel(logging.DEBUG)
# f_file.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
# _logger.addHandler(f_file)

_handler = logging.StreamHandler(sys.stdout)
_logger.addHandler(_handler)

print("\033[1;32mbeginning at %s ..." % now_time)


def debug(msg):
    _logger.debug("DEBUG " + str(msg))


def info(msg):
    # print('\033[1;32m%s' % msg)
    # _logger.info("INFO " + str(msg))
    _logger.info(Fore.GREEN + "INFO " + str(msg) + Style.RESET_ALL)


def error(msg):
    # print('\033[1;31m%s' % msg)
    # _logger.error("ERROR " + str(msg))
    _logger.error(Fore.RED + "ERROR " + str(msg) + Style.RESET_ALL)


def warn(msg):
    # print('\033[1;33m%s' % msg)
    # _logger.warning("WARNING " + str(msg))
    _logger.warning(Fore.YELLOW + "WARNING " + str(msg) + Style.RESET_ALL)
