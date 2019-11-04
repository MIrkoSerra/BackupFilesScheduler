from datetime import datetime
from oauth2client.client import GoogleCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from PyQt5.QtCore import (QRunnable, pyqtSignal, QObject)
import schedule
import time


class Auth(GoogleAuth):

    def __init__(self, files, crud):
        super(Auth, self).__init__()
        self.files = files
        self.crud = crud

    def SaveCredentialsFile(self, credentials_file=None):
        # Saves credentials to the file config.ini.

        if not self.credentials:
            raise NotImplementedError('No credentials to save')
        try:
            g_creds = {
                "access_token": self.credentials.access_token,
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
                "refresh_token": self.credentials.refresh_token,
                "token_expiry": self.credentials.token_expiry,
                "token_uri": self.credentials.token_uri,
                "user_agent": self.credentials.user_agent,
                "revoke_uri": self.credentials.revoke_uri
            }
            for key, value in g_creds.items():
                self.files.set('GDRIVE', key, str(value))
                # Write on file
                self.crud.write_config_file(self.files)

        except NotImplementedError:
            raise NotImplementedError("var Credentials doesn't contain the expected values")

    def LoadCredentialsFile(self, client_config_file=None):
        list_cred = []
        for option in self.files['GDRIVE']:
            if self.files['GDRIVE'][option]:
                list_cred.append(self.files['GDRIVE'][option])
        date_format = "%Y-%m-%d %H:%M:%S.%f"
        if list_cred:
            self.credentials = GoogleCredentials(access_token=list_cred[0],
                                                 client_id=list_cred[1],
                                                 client_secret=list_cred[2],
                                                 refresh_token=list_cred[3],
                                                 token_expiry=datetime.strptime(list_cred[4], date_format),
                                                 token_uri=list_cred[5],
                                                 user_agent=list_cred[6],
                                                 revoke_uri=list_cred[7]
                                                 )


class DriveWorker(QRunnable):

    def __init__(self, files, crud):
        super(DriveWorker, self).__init__()
        self._signal_helper = SignalHelper()
        self.counter = self._signal_helper.counter_drive
        self.auth = self._signal_helper.login.connect(self.login)
        self.files = files
        self.gauth = Auth(self.files, crud)
        self.drive = None

    def run(self):
        # Try to load saved client credentials
        self.gauth.LoadCredentialsFile()
        if self.gauth.credentials:
            if self.gauth.access_token_expired:
                # Refresh them if expired
                self.gauth.Refresh()
            self.drive = GoogleDrive(self.gauth)
            if self.drive:
                self.start()
        pass

    def start(self):
        waiting_time = int(self.files['TIMER']['drive'])
        schedule.every(waiting_time).minutes.do(self.upload_file_to_drive)
        timer = 0

        while 1:
            schedule.run_pending()
            timer = self.drive_timer(waiting_time, timer)
            self.counter.emit(timer)
            time.sleep(1)

    @staticmethod
    def drive_timer(waiting_time, timer):
        if timer == 0:
            timer = (waiting_time * 60) - 1
            return timer
        else:
            return timer - 1

    def login(self):
        # Try to load saved client credentials
        self.gauth.LoadCredentialsFile()
        if self.gauth.credentials is None:
            # Authenticate if they're not there
            self.gauth.LocalWebserverAuth()
        elif self.gauth.access_token_expired:
            # Refresh them if expired
            self.gauth.Refresh()
        else:
            # Initialize the saved creds
            if self.gauth.credentials:
                self.gauth.Authorize()
        # Save the current credentials to a file
        if self.gauth.credentials:
            self.gauth.SaveCredentialsFile()
            self.drive = GoogleDrive(self.gauth)
            self.start()

    def upload_file_to_drive(self):
        if self.files.options('PATH_DRIVE'):
            file = self.drive.CreateFile()
            now = datetime.today().strftime("%H:%M ")
            for option in self.files['PATH_DRIVE']:
                file.SetContentFile(self.files['PATH_DRIVE'][option])
                file['title'] = now + option
                file.Upload()


class SignalHelper(QObject):
    # DriveWorker
    login = pyqtSignal(object)
    raise_error = pyqtSignal(object)
    remove_files = pyqtSignal(object)
    counter_drive = pyqtSignal(object)
