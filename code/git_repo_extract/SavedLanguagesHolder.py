class SavedLanguagesHolder(object):

    def __init__(self):
        self.files_languages_dict = {}

    def is_file_defined(self, file_path: str):
        return file_path in self.files_languages_dict

    def add_file_info(self, file_path: str, language: str):
        if not self.is_file_defined(file_path):
            self.files_languages_dict[file_path] = language

    def get_file_info(self, file_path: str):
        if not self.is_file_defined(file_path):
            return None
        return self.files_languages_dict[file_path]
