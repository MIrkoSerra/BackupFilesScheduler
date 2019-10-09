import configparser


class Crud:

    def __init__(self):
        # https://stackoverflow.com/questions/576169/understanding-python-super-with-init-methods
        super().__init__()
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
        config_parser["SAVE_PATH"] = {
            'dir': ""
        }
        config_parser["TIMER"] = {
            'default': '1',
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
