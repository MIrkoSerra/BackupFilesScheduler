import configparser


class Crud:

    def init_config(self):
        config = configparser.ConfigParser()
        try:
            return self.read_config_file(config)
        except IOError:
            self.write_config_file(self.create_config_file(config))
            return self.read_config_file(config)

    def create_config_file(self, configparser):
        configparser["PATH"] = {}
        configparser["SAVE_PATH"] = {
            'dir': ""
        }
        configparser["TIMER"] = {
            'default': '1',
        }

        return configparser

    def read_config_file(self, configparser):
        with open('config.ini', 'r') as configfile:
            configparser.readfp(configfile)
            return configparser

    def write_config_file(self, confiparser):
        with open('config.ini', 'w') as configfile:
            confiparser.write(configfile)
