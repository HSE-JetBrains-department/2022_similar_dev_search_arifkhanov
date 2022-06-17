from typing import Union

class SavedLanguagesHolder(object):
    """
    Holder class that helps to accumulated parsed in single repo files' languages

    """
    def __init__(self):
        self.files_languages_dict = {}

    def is_file_defined(self, file_path: str) -> bool:
        """
        Checks whether there is already file information in Holder
        :param file_path: path of the file inside of repository
        :return: bool
        """
        return file_path in self.files_languages_dict

    def add_file_info(self, file_path: str, language: str) -> None:
        """
        Adds file info to the holder in case if there is no file information already
        :param file_path: path of the file inside of repository
        :param language: file's programming language
        :return: None
        """
        if not self.is_file_defined(file_path):
            self.files_languages_dict[file_path] = language

    def get_file_info(self, file_path: str) -> Union[str, None]:
        """
        Get information about given file's language
        :param file_path: path of the file inside of repository
        :return: its programming language
        """
        if not self.is_file_defined(file_path):
            return None
        return self.files_languages_dict[file_path]
