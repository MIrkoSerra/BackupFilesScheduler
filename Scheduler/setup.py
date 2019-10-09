from PyQt5.QtWidgets import *
from PyQt5.QtCore import (Qt, QThreadPool)
from PyQt5.QtGui import QIcon
from os.path import basename
import sys
from Scheduler.cron import *
from Scheduler.crud import *


class CustomTextBox(QLineEdit):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.crud = Crud()
        self.files = self.crud.init_config()
        self.threadpool = QThreadPool()
        self.setWindowIcon(QIcon('Icon.ico'))
        self.title = 'Save Files'
        self.left = 10
        self.top = 10
        self.width = 600
        self.height = 262
        self.init_ui()
        self.cron()

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
        self.crud.write_config_file(self.files)
        return self.get_table_rows(self.table_widget)

    def add_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder:
            self.files.set('SAVE_PATH', "dir", folder)
        self.crud.write_config_file(self.files)
        return self.textbox_path.insert(folder)

    def remove_files(self):
        file = []
        for option in self.files['PATH']:
            file.append(option)

        file, ok = QInputDialog.getItem(self, "Remove File", "Select file:", file, 0, False)

        if ok and file:
            self.files.remove_option('PATH', file)
            self.crud.write_config_file(self.files)
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
