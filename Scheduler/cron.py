from shutil import copy
import datetime
from PyQt5.QtCore import (QRunnable, QObject, pyqtSignal)
from pathlib import Path
import schedule
import time
import sys


# Create a thread that schedule and copy the files present in the config.ini
# The thread has as parameter, the configparser obj, loaded by the gui (self.files)
class Worker(QRunnable):
    ERROR_NO_DIRECTORY = 000
    ERROR_GENERIC = 100

    def __init__(self, files, *args, **kwargs):
        super(Worker, self).__init__()
        self.files = files
        self._signal_helper = SignalHelper()
        self.raise_error = self._signal_helper.raise_error
        self.remove_files = self._signal_helper.remove_files
        self.counter = self._signal_helper.counter
        self.args = args
        self.kwargs = kwargs

    def run(self):
        waiting_time = int(self.files['TIMER']['default'])
        schedule.every(waiting_time).minutes.do(self.copy)
        timer = 0

        while 1:
            schedule.run_pending()
            self.check_path()
            timer = self.timer(waiting_time, timer)
            self.counter.emit(timer)
            time.sleep(1)

    def timer(self, waiting_time, timer):
        if timer == 0:
            timer = (waiting_time * 60) - 1
            return timer
        else:
            return timer - 1

    def check_path(self):
        bad_files = []
        for option in self.files['PATH']:
            file = Path(self.files['PATH'][option])
            # Check if the file path exist
            if not file.is_file():
                bad_files.append(option)
        if bad_files:
            self.remove_files.emit(bad_files)

    def copy(self):
        now = datetime.datetime.today().strftime("%d-%b %H:%M")
        if sys.platform == "linux":
            date = "/[" + now + "]"
        elif sys.platform == "win32":
            date = "\[" + now + "]"

        if self.files['SAVE_PATH']['dir']:
            try:
                for option in self.files['PATH']:
                    copy(self.files['PATH'][option], self.files['SAVE_PATH']["dir"] + date + option)
            except IOError:
                self.raise_error.emit(self.ERROR_GENERIC)
        else:
            self.raise_error.emit(self.ERROR_NO_DIRECTORY)


# To handle the signal problem (source https://pastebin.com/npnwenyw)
# Signals problem: with QRunnable i couldn't pass signals so i had to create an obj and connect through this
class SignalHelper(QObject):
    raise_error = pyqtSignal(object)
    remove_files = pyqtSignal(object)
    counter = pyqtSignal(object)
