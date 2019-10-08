from shutil import copyfile
import datetime
from PyQt5.QtCore import (QRunnable, QObject, pyqtSignal)
import schedule
import time


# Create a thread that schedule and copy the files present in the config.ini
# The thread has as parameter the configparser obj loaded by the gui (self.files)
class Worker(QRunnable):
    ERROR_NO_DIRECTORY = 000
    ERROR_GENERIC = 100

    def __init__(self, files, *args, **kwargs):
        super(Worker, self).__init__()
        self.files = files
        self._signal_helper = SignalHelper()
        self.raise_error = self._signal_helper.raise_error
        self.args = args
        self.kwargs = kwargs

    def run(self):
        waiting_time = int(self.files['TIMER']['default'])
        schedule.every(waiting_time).minutes.do(self.copy)

        while 1:
            schedule.run_pending()
            time.sleep(1)

    def copy(self):
        now = datetime.datetime.today().strftime("%d-%b | %H:%M")
        date = "/[" + now + "]"
        if self.files['SAVE_PATH']['dir']:
            try:
                for option in self.files['PATH']:
                    copyfile(self.files['PATH'][option], self.files['SAVE_PATH']["dir"] + date + option)
            except IOError:
                self.raise_error.emit(self.ERROR_GENERIC)
        else:
            self.raise_error.emit(self.ERROR_NO_DIRECTORY)


# To handle the signal problem (source https://pastebin.com/npnwenyw)
# Signals problem: with QRunnable i couldn't pass signals so i had to create an obj and connect through this
class SignalHelper(QObject):
    raise_error = pyqtSignal(object)
