import pickle


class PickleDB:
    def __init__(self):
        self.DIR_PATH = 'dir_path'
        self.name = None
        self.file_name = 'source/properties.pickle'
        self.properties = {}
        self.dir_path = ''

    def set_dir_path(self, dir_path):
        self.dir_path = dir_path
        self.save_K_V(self.DIR_PATH, dir_path)

    def get_dir_path(self):
        return self.dir_path

    def save_K_V(self, key, value):
        try:
            self.read()
        except:
            pass
        finally:
            self.properties[key] = value
            with open(self.file_name, 'wb') as file:
                pickle.dump(self.properties, file)

    def read(self):
        with open(self.file_name, 'rb') as file:
            self.properties = pickle.load(file)

    def get_value_from_key(self, key):
        try:
            self.read()
            return self.properties[key]
        except:
            return ''





# p = PickleDB()
# p.set_dir_path('ccccccc')
# p.read()
