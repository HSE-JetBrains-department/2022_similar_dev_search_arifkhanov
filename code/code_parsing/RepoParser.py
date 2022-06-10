import logging
from collections import Counter
from typing import Dict

from dulwich.diff_tree import TreeChange
from dulwich.repo import Repo
from tqdm import tqdm

logger = logging.getLogger(__name__)

class RepoParser(object):
    """
    Class that parses repo with tree sitter. Saves info about parsed files,
    about used imports, variable and function names.
    Allows to fill sparse matrices of used variables for certain people
    """

    def __init__(self, repo: Repo):
        self.is_parsed = False
        self.imports = Counter()
        self.variables = Counter()
        self.repo = repo
        self.used_files = {}  # saves  { filepath : { imports: set(), variables: set(), is_parsed} }
        self.repo_url = f"{(self.repo.get_config().get((b'remote', b'origin'), b'url')).decode()} was already parsed"

#  TODO А что мне мешает пройтись по репозиторию с самого начала и пропарсить все файлы с помощью новейших коммитов?
    def parse_files(self):
        if self.is_parsed:
            logger.log(1, self.repo_url)
            return

        for walk in tqdm(self.repo.get_walker(), desc=f"{self.repo_url} processing"):
            for changes in walk.changes():
                if not isinstance(changes, list):
                    changes = [changes]

                for change in changes:
                    if change.new.sha is None:
                        continue
                    self.used_files[change.new.path.decode()] = self.parse_change(change)

    def parse_change(self, change: TreeChange) -> Dict:
        pass

    def handle_author_imports(self, commit_info):
        """
        adds author's imports to sparse matrix
        :param commit_info:
        """
        pass

    def handle_author_variables(self, commit_info):
        """
        adds author's variables to sparse matrix
        :param commit_info:
        :return: sparse_m
        """
        pass
