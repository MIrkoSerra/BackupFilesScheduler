from PyQt5.QtWidgets import *
from PyQt5.QtCore import (Qt, QThreadPool)
from PyQt5.QtGui import QIcon
import traceback
import qdarkstyle
from os.path import basename
from cron import *
from crud import *


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
        self.height = 320
        self.init_ui()
        self.cron()

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        tab1 = QWidget()
        tab2 = QWidget()

        self.tabs.addTab(tab1, "Local")
        self.tabs.addTab(tab2, "Drive")

        tab1.layout = QVBoxLayout()
        tab1.layout.addLayout(self.local_tab(), 1)
        tab1.setLayout(tab1.layout)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.show()

    def local_tab(self):
        main_box = QVBoxLayout()
        table = self.create_table()
        label_1 = QLabel('Files to backup')
        main_box.addWidget(label_1, alignment=Qt.AlignBottom)
        main_box.addWidget(table)

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
        textbox.clicked.connect(self.add_save_path)
        textbox.setReadOnly(True)
        textbox.setMinimumWidth(250)
        self.textbox_path = textbox
        path_dir = self.files['SAVE_PATH']['dir']
        if path_dir:
            self.textbox_path.insert(path_dir)
        self.label_timer = QLabel()
        box_buttons.addWidget(self.label_timer, alignment=Qt.AlignLeft)
        box_buttons.addWidget(textbox, alignment=Qt.AlignRight)
        main_box.addLayout(box_commands)
        return main_box

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

    def add_save_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder:
            self.files.set('SAVE_PATH', "dir", folder)
            self.crud.write_config_file(self.files)
            self.textbox_path.clear()
            return self.textbox_path.insert(folder)

    def remove_files(self, *args):
        if not args[0]:
            file = []
            for option in self.files['PATH']:
                file.append(option)

            file, ok = QInputDialog.getItem(self, "Remove File", "Select file:", file, 0, False)

            if ok and file:
                self.files.remove_option('PATH', file)
                self.crud.write_config_file(self.files)
        else:
            for option in args[0]:
                self.files.remove_option('PATH', option)
            self.crud.write_config_file(self.files)
        return self.get_table_rows(self.table_widget)

    def cron(self):
        worker = Worker(self.files)
        worker.raise_error.connect(self.raise_error)
        worker.remove_files.connect(self.remove_files)
        worker.counter.connect(self.counter)
        self.threadpool.start(worker)

    def counter(self, timer):
        self.label_timer.setText(str(timer))

    def raise_error(self, error):
        if error == 100:
            QMessageBox.warning(self, 'PATH Error!',
                                "You have to insert a destination path for your files", QMessageBox.Ok)

        elif error == 200:
            QMessageBox.warning(self, 'PATH Error', "Your destination path doesn't exist", QMessageBox.Ok)

        elif error == 300:
            QMessageBox.warning(self, 'Generic Error', traceback.format_exc(), QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    sys.exit(app.exec_())
