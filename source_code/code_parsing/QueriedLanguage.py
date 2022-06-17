import json
from pathlib import Path

from tree_sitter import Language


class QueriedLanguage(Language):

    def __init__(self, library_path: str, name: str, queries_path: Path):
        """

        :param library_path: path to the tree-sitter library object
        :param name: programming language that should be parsed
        :param queries_path: path to the tree-sitter queries folder
        """
        super().__init__(library_path, name)

        with (queries_path / f"{name}_queries.json").open("r") as fr:
            queries = json.load(fr)
        self.query_types = {q_type: self.query(q_text) for q_type, q_text in queries.items()}

    def capture_query(self, query_type, root_node):
        if query_type not in self.query_types:
            raise ValueError(f"{query_type} not in prepared queries."
                             f"\nChoose one of {', '.join(self.query_types.keys())}")

        return self.query_types[query_type].captures(root_node)
