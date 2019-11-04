import configparser


class Crud:

    def __init__(self):
        # https://stackoverflow.com/questions/576169/understanding-python-super-with-init-methods
        super(Crud, self).__init__()
        self.config_parser = configparser.ConfigParser()

    def init_config(self):
        try:
            return self.read_config_file(self.config_parser)
        except IOError:
            self.write_config_file(self.create_config_file(self.config_parser))
            return self.read_config_file(self.config_parser)

    @staticmethod
    def create_config_file(config_parser):
        config_parser["PATH"] = {}
        config_parser["PATH_DRIVE"] = {}
        config_parser["SAVE_PATH"] = {
            'dir': ""
        }
        config_parser["TIMER"] = {
            'local': '1',
            'drive': '5',
        }
        config_parser["GDRIVE"] = {
            'access_token': "",
            'client_id': "",
            'client_secret': "",
            'refresh_token': "",
            'token_expiry': "",
            'token_uri': "",
            'user_agent': "",
            'revoke_uri': "",
        }

        return config_parser

    @staticmethod
    def read_config_file(config_parser):
        with open('config.ini', 'r') as configfile:
            config_parser.readfp(configfile)
            return config_parser

    @staticmethod
    def write_config_file(config_parser):
        with open('config.ini', 'w') as configfile:
            config_parser.write(configfile)
