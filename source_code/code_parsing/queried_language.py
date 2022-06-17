import json
from pathlib import Path

from tree_sitter import Language


class QueriedLanguage(Language):
    """
    Wrapper class for tree-sitter Language class. Uses prepared queries
    to make some operations more convenient
    """
    def __init__(self, library_path: str, name: str, queries_path: Path):
        """
        Inits tree-sitter Language object with additional capture_query method that allows
        using prepared queries

        :param library_path: path to the tree-sitter library object
        :param name: programming language that should be parsed
        :param queries_path: path to the tree-sitter queries folder
        """
        super().__init__(library_path, name)

        with (queries_path / f"{name}_queries.json").open("r") as fr:
            queries = json.load(fr)
        self.query_types = {q_type: self.query(q_text) for q_type, q_text in queries.items()}

    def capture_query(self, query_type, root_node):
        """
        Executes one of prepared query for the root_node of the given tree
        :param query_type: which query to use (check which is available in class)
        :param root_node: root node of parsed code tree
        :return: list of all captures for the query
        """
        if query_type not in self.query_types:
            raise ValueError(f"{query_type} not in prepared queries."
                             f"\nChoose one of {', '.join(self.query_types.keys())}")

        return self.query_types[query_type].captures(root_node)
