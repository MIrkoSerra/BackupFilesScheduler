from PyQt5.QtWidgets import *
from PyQt5.QtCore import (Qt, QRunnable, QObject, QThreadPool, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import QIcon
from shutil import copyfile
from os.path import basename
import sys
import configparser
import datetime
import schedule
import time


# To handle the signal problem (source https://pastebin.com/npnwenyw)
# Signals problem: with QRunnable i couldn't pass signals so i had to create an obj and connect through this
class SignalHelper(QObject):
    raise_error = pyqtSignal(object)


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

    @pyqtSlot()
    def run(self):
        waiting_time = int(self.files['TIMER']['default'])
        schedule.every(waiting_time).minutes.do(self.copy)

        while 1:
            schedule.run_pending()
            time.sleep(1)


class CustomTextBox(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.files = self.setup_config()
        self.threadpool = QThreadPool()
        self.setWindowIcon(QIcon('Icon.ico'))
        self.title = 'Save Files'
        self.left = 10
        self.top = 10
        self.width = 600
        self.height = 262
        self.init_ui()
        self.cron()

    def initialize_config_file(self, configparser):
        configparser["PATH"] = {}
        configparser["SAVE_PATH"] = {
            'dir': ""
        }
        configparser["TIMER"] = {
            'default': '1',
        }

        return configparser

    def read_config(self, configparser):
        with open('config.ini', 'r') as configfile:
            configparser.readfp(configfile)
            return configparser

    def write_config(self, confiparser):
        with open('config.ini', 'w') as configfile:
            confiparser.write(configfile)

    def setup_config(self):
        config = configparser.ConfigParser()
        try:
            return self.read_config(config)
        except IOError:
            self.write_config(self.initialize_config_file(config))
            return self.read_config(config)

    def init_ui(self):

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        mainbox = QVBoxLayout()
        mainbox.addLayout(self.box1(), 1)
        self.setLayout(mainbox)
        self.show()

    def box1(self):
        box1 = QVBoxLayout()
        table = self.create_table()
        label_1 = QLabel('Files to backup')
        box1.addWidget(label_1, alignment=Qt.AlignBottom)
        box1.addWidget(table)

        box_buttons = QHBoxLayout()
        # Add file to backup
        button_load = QPushButton('Load File', self)
        button_load.clicked.connect(self.add_files)
        box_buttons.addWidget(button_load, alignment=Qt.AlignLeft)

        # Remove file to backup
        button_delete = QPushButton('Remove File', self)
        button_delete.clicked.connect(self.remove_files)
        box_buttons.addWidget(button_delete, alignment=Qt.AlignLeft)

        box_buttons.addStretch(1)

        box_commands = QHBoxLayout()
        box_commands.addLayout(box_buttons)

        # Save Path TextBox
        textbox = CustomTextBox()
        textbox.clicked.connect(self.add_path)
        textbox.setReadOnly(True)
        textbox.setMinimumWidth(250)
        self.textbox_path = textbox
        path_dir = self.files['SAVE_PATH']['dir']
        if path_dir:
            self.textbox_path.insert(path_dir)

        box_buttons.addWidget(textbox, alignment=Qt.AlignRight)
        box1.addLayout(box_commands)
        return box1

    def create_table(self):
        # Create table
        table_widget = QTableWidget()
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = table_widget.horizontalHeader()
        header.setStretchLastSection(True)
        table_widget.setColumnCount(2)
        table_widget = self.get_table_rows(table_widget)
        table_widget.setHorizontalHeaderLabels(["NAME", "PATH"])
        self.table_widget = table_widget
        return table_widget

    def get_table_rows(self, table_widget):
        file = []
        if self.files:
            for option in self.files['PATH']:
                file.append(option)
            table_widget.setRowCount(file.__len__())
            i = 0
            for value in file:
                table_widget.setItem(i, 0, QTableWidgetItem(value))
                table_widget.setItem(i, 1, QTableWidgetItem(self.files['PATH'][value]))
                i = i + 1
        return table_widget

    def add_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Select files PATH", "",
                                                "All Files (*);;Sav files (*.sav)", options=options)

        for path in files:
            filename = basename(path)
            self.files.set('PATH', filename, path)
        self.write_config(self.files)
        return self.get_table_rows(self.table_widget)

    def add_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder:
            self.files.set('SAVE_PATH', "dir", folder)
        self.write_config(self.files)
        return self.textbox_path.insert(folder)

    def remove_files(self):
        file = []
        for option in self.files['PATH']:
            file.append(option)

        file, ok = QInputDialog.getItem(self, "Remove File", "Select file:", file, 0, False)

        if ok and file:
            self.files.remove_option('PATH', file)
            self.write_config(self.files)
        return self.get_table_rows(self.table_widget)

    def cron(self):
        worker = Worker(self.files)
        worker.raise_error.connect(self.raise_error)
        self.threadpool.start(worker)

    def raise_error(self, error):
        if error == 000:
            QMessageBox.warning(self, 'PATH Error!',
                                "You have to insert a destination path for your files", QMessageBox.Ok)
        elif error == 100:
            QMessageBox.warning(self, 'Generic Error',
                                "Something went wrong!", QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.setStyle('GTK+')
    sys.exit(app.exec_())
