import logging
from collections import Counter
from typing import Set

from dulwich.diff_tree import TreeChange
from dulwich.repo import Repo
from tree_sitter import Language, Parser
from tqdm import tqdm

from source_code.code_parsing.queried_language import QueriedLanguage
from source_code.git_repo_extract.commits_info import define_file_language
from source_code.git_repo_extract.repo_ops import get_repos_url, try_find_repo
from source_code.utils import *

logger = logging.getLogger(__name__)


class RepoParser(object):
    """
    Class that parses repo with tree sitter. Saves info about parsed files,
    about used imports, variable and function names.
    """
    parsers: Dict[str, Dict[str, Union[QueriedLanguage, Parser]]] = {}

    def __init__(self, repo: Repo,
                 supported_languages: List[str],
                 path_to_grammars: Path = TREE_SITTER_GRAMMARS_FOLDER,
                 path_to_library: Path = TREE_SITTER_GRAMMARS_FOLDER / "lang_lib.so",
                 path_to_queries: Path = TREE_SITTER_QUERIES_FOLDER):
        """
        Creates class that will parse a repository and extract imports and variable names for files in it

        :param repo: Repo instance to be parsed
        :param supported_languages: programming languages should be parsed
        :param path_to_grammars: path to folder with tree-sitter grammar repos
        :param path_to_library: path to tree-sitter generated library file
        """
        self.is_parsed = False
        self.imports = Counter()
        self.variables = Counter()
        self.repo = repo
        self.used_files: Dict[str, Dict[str, Set]] = {}  # saves  { filepath : { "imports": set(), "variables": set()} }
        self.repo_url = get_repos_url(self.repo)
        self.supported_languages = set([x.strip().lower() for x in supported_languages])
        self.languages_holder = dict()

        for lang in supported_languages:  # download repos if not exist
            try_find_repo(str(path_to_grammars), f"tree-sitter/tree-sitter-{lang}", True)

        Language.build_library(
            str(path_to_library),
            [str(path_to_grammars / f"tree-sitter_tree-sitter-{lang}") for lang in supported_languages]
        )

        # probably, due to multiprocessing it won't work
        if not RepoParser.parsers:  # fill class variable to avoid repeated action in different instances
            RepoParser.parsers = {}
            for language in supported_languages:
                lang = QueriedLanguage(str(path_to_library), language, path_to_queries)
                RepoParser.parsers[language] = {"parser": Parser(),
                                                "language": lang}
                RepoParser.parsers[language]["parser"].set_language(lang)

    def parse_files(self, limit_of_commits: int = 1000) -> None:
        """
        Method runs parsing of files for repository given in constructor

        :return: None
        """
        if self.is_parsed:
            logger.log(1, self.repo_url)
            return

        for index, walk in enumerate(tqdm(self.repo.get_walker(), desc=f"{self.repo_url} processing")):

            if index > limit_of_commits:
                break

            for changes in walk.changes():
                if not isinstance(changes, list):
                    changes = [changes]

                for change in changes:
                    if change.new.sha is None:
                        continue

                    file_path = change.new.path.decode()

                    if file_path in self.used_files:
                        continue

                    result = self.parse_change(change, file_path)

                    if result is None:
                        continue

                    self.variables.update(result["variables"])
                    self.imports.update(result["imports"])

                    self.used_files[file_path] = result

    def parse_change(self, change: TreeChange, file_path: str) -> Union[Dict, None]:
        """
        Method parses single change in commit, looks through its blob and takes arguments and imports from it

        :param change: tree change to parse
        :param file_path: path to the file to parse
        :return: dict {"variables" : set(), "imports" : set()}
        """
        code = self.repo.get_object(change.new.sha).as_pretty_string()  # in bytes
        language = define_file_language(file_path, code, self.languages_holder)

        if language is None or language not in self.supported_languages:
            return None

        return self.process_queries(RepoParser.parsers[language]["language"],
                                    code,
                                    RepoParser.parsers[language]["parser"])

    def process_queries(self, queried_language: QueriedLanguage, code: bytes, parser: Parser) -> Dict:
        """
        Method parses given code using tree-sitter utilities. QueriedLanguage object contains parsing queries

        :param parser: parser object in order to... parse?
        :param queried_language: QueriedLanguage object that contains parsing queries
        :param code: Code to being parsed
        :return: dict {"variables" : set(), "imports" : set()}
        """
        tree = parser.parse(code)

        result = {}
        for q_type, query in queried_language.query_types.items():
            result[q_type] = {code[x[0].start_byte:x[0].end_byte].decode("latin-1")
                              for x in queried_language.capture_query(q_type, tree.root_node)}
        return result

    def handle_author_imports(self, commit_info) -> Union[Set, None]:
        """
        Gives author's imports on file in commit_info

        :param commit_info: commit_info object to get info about file
        :return: set of imports
        """
        if commit_info["programming_language"].lower() not in self.supported_languages:
            return None
        return self.used_files[commit_info["file_path"]]["imports"]

    def handle_author_variables(self, commit_info) -> Union[Set, None]:
        """
        Gives author's imports on file in commit_info

        :param commit_info: commit_info object to get info about file
        :return set of variables
        """
        if commit_info["programming_language"].lower() not in self.supported_languages:
            return None
        return self.used_files[commit_info["file_path"]]["variables"]
