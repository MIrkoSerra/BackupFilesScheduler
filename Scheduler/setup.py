from PyQt5.QtWidgets import *
from PyQt5.QtCore import (Qt, QThreadPool, QMetaObject)
from PyQt5.QtGui import QIcon
import traceback
import qdarkstyle
from os.path import basename
from cron_local import *
from crud import *
from cron_drive import DriveWorker


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

        tab2.layout = QVBoxLayout()
        tab2.layout.addLayout(self.drive_tab(), 1)
        tab2.setLayout(tab2.layout)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        self.show()

    # LOCAL UI

    def local_tab(self):
        main_box = QVBoxLayout()
        table = self.create_table()
        label_1 = QLabel('Files to backup')
        main_box.addWidget(label_1, alignment=Qt.AlignBottom)
        main_box.addWidget(table)

        box_buttons = QHBoxLayout()
        # Add file to backup
        button_load = QPushButton('Load File', self)
        button_load.clicked.connect(self.add_local_files)
        box_buttons.addWidget(button_load, alignment=Qt.AlignLeft)

        # Remove file to backup
        button_delete = QPushButton('Remove File', self)
        button_delete.clicked.connect(self.remove_local_files)
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
        table_widget = self.get_local_table_rows(table_widget)
        table_widget.setHorizontalHeaderLabels(["NAME", "PATH"])
        self.table_widget = table_widget
        return table_widget

    def get_local_table_rows(self, table_widget):
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

    def add_local_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Select files PATH", "",
                                                "All Files (*);;Sav files (*.sav)", options=options)

        for path in files:
            filename = basename(path)
            self.files.set('PATH', filename, path)
        self.crud.write_config_file(self.files)
        return self.get_local_table_rows(self.table_widget)

    def add_save_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", options=options)
        if folder:
            self.files.set('SAVE_PATH', "dir", folder)
            self.crud.write_config_file(self.files)
            self.textbox_path.clear()
            return self.textbox_path.insert(folder)

    def remove_local_files(self, *args):
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
        return self.get_local_table_rows(self.table_widget)

    # DRIVE UI

    def drive_tab(self):
        main_box = QVBoxLayout()
        table = self.create_drive_table()
        label_1 = QLabel('Files to upload')
        main_box.addWidget(label_1, alignment=Qt.AlignBottom)
        main_box.addWidget(table)

        box_buttons = QHBoxLayout()
        # Add file to backup
        button_load = QPushButton('Load File', self)
        button_load.clicked.connect(self.add_drive_files)
        box_buttons.addWidget(button_load, alignment=Qt.AlignLeft)

        # Remove file to backup
        button_delete = QPushButton('Remove File', self)
        button_delete.clicked.connect(self.remove_drive_files)
        box_buttons.addWidget(button_delete, alignment=Qt.AlignLeft)

        box_buttons.addStretch(1)

        box_commands = QHBoxLayout()
        box_commands.addLayout(box_buttons)

        # Save Path TextBox
        button_login = QPushButton('Login', self)
        button_login.clicked.connect(self.login)
        box_commands.addWidget(button_login, alignment=Qt.AlignRight)

        button_upload = QPushButton('Upload Now', self)
        button_upload.clicked.connect(self.upload_now)
        box_commands.addWidget(button_upload, alignment=Qt.AlignRight)

        self.label_timer_drive = QLabel()
        box_buttons.addWidget(self.label_timer_drive, alignment=Qt.AlignLeft)
        main_box.addLayout(box_commands)
        return main_box

    def create_drive_table(self):
        # Create table
        table_widget = QTableWidget()
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = table_widget.horizontalHeader()
        header.setStretchLastSection(True)
        table_widget.setColumnCount(2)
        table_widget = self.get_drive_table_rows(table_widget)
        table_widget.setHorizontalHeaderLabels(["NAME", "PATH"])
        self.table_drive_widget = table_widget
        return table_widget

    def get_drive_table_rows(self, table_widget):
        file = []
        if self.files:
            for option in self.files['PATH_DRIVE']:
                file.append(option)
            table_widget.setRowCount(file.__len__())
            i = 0
            for value in file:
                table_widget.setItem(i, 0, QTableWidgetItem(value))
                table_widget.setItem(i, 1, QTableWidgetItem(self.files['PATH_DRIVE'][value]))
                i = i + 1
        return table_widget

    def add_drive_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Select files PATH", "",
                                                "All Files (*);;Sav files (*.sav)", options=options)

        for path in files:
            filename = basename(path)
            self.files.set('PATH_DRIVE', filename, path)
        self.crud.write_config_file(self.files)
        return self.get_drive_table_rows(self.table_drive_widget)

    def remove_drive_files(self, *args):
        if not args[0]:
            file = []
            for option in self.files['PATH_DRIVE']:
                file.append(option)

            file, ok = QInputDialog.getItem(self, "Remove File", "Select file:", file, 0, False)

            if ok and file:
                self.files.remove_option('PATH_DRIVE', file)
                self.crud.write_config_file(self.files)
        else:
            for option in args[0]:
                self.files.remove_option('PATH_DRIVE', option)
            self.crud.write_config_file(self.files)
        return self.get_drive_table_rows(self.table_drive_widget)

    # END UI

    def cron(self):
        # Local Worker
        worker = LocalWorker(self.files)
        worker.raise_error.connect(self.raise_error)
        worker.remove_files.connect(self.remove_local_files)
        worker.counter.connect(self.counter)
        self.threadpool.start(worker)
        # Drive Worker
        self.worker2 = DriveWorker(self.files, self.crud)
        self.worker2.counter.connect(self.counter_drive)
        self.threadpool.start(self.worker2)

    def login(self):
        self.worker2.login()

    def upload_now(self):
        self.worker2.upload_file_to_drive()

    def counter(self, timer):
        self.label_timer.setText(str(timer))

    def counter_drive(self, timer):
        self.label_timer_drive.setText(str(timer))

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
