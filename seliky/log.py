"""
close print in rf，because testing framework has it's own logger
"""

import os
import logging
import sys
import inspect
import re
from datetime import datetime

# from colorama import Fore, Style
now_time = str(datetime.now())[:-7]
print("\033[1;32mbeginning at %s ..." % now_time)


class Log:
    def __init__(self, log_folder=None, write_in_file: bool = True):
        self._logger = logging.getLogger('selek')
        self.write_in_file = write_in_file

        if write_in_file:
            log_folder = log_folder if log_folder else self.__call_file_path()
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
            log_file = os.path.join(log_folder, datetime.now().strftime('%Y-%m-%d') + ".log")
            f_file = logging.FileHandler(log_file, encoding='utf-8')
            f_file.setLevel(logging.DEBUG)
            f_file.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
            self._logger.addHandler(f_file)

        else:
            self._logger.setLevel(logging.DEBUG)
            _handler = logging.StreamHandler(sys.stdout)
            self._logger.addHandler(_handler)

    @staticmethod
    def __call_file_path():
        curframe = inspect.currentframe()
        call_frame = inspect.getouterframes(curframe, 2)
        call_file = call_frame[1][1]
        call_folder = re.sub(r'\w+.py', '', call_file)
        return call_folder

    def debug(self, msg):
        self._logger.debug("DEBUG " + str(msg))

    def info(self, msg):
        msg = 'INFO ' + str(msg)
        if self.write_in_file:
            self._logger.info(msg)
        else:
            print('\033[1;32m %s' % msg)
        # _logger.info(Fore.GREEN + "INFO " + str(msg) + Style.RESET_ALL)

    def error(self, msg):
        msg = 'ERROR ' + str(msg)
        if self.write_in_file:
            self._logger.error(msg)
        else:
            print('\033[1;31m %s' % msg)
        # self._logger.error(Fore.RED + "ERROR " + str(msg) + Style.RESET_ALL)

    def warn(self, msg):
        msg = 'WARN ' + str(msg)
        if self.write_in_file:
            self._logger.warning(msg)
        else:
            print('\033[1;33m %s' % msg)
        # self._logger.warning(Fore.YELLOW + "WARNING " + str(msg) + Style.RESET_ALL)
