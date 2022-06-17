from pathlib import Path
from typing import List, Set

import pytest

from source_code.code_parsing.RepoParser import RepoParser
from source_code.git_repo_extract.repo_ops import try_find_repo


@pytest.mark.parametrize("file_languages, file_names, variables_check, imports_check",
                         [(["java", "javascript", "python"],
                           ["java_code.java", "javascript_code.js", "python_code.py"],
                           {'df', 'custom_HL', 'predict', 'idx', 'tpr', 'p', 'iv', 'points', 'words', 'joinLetters',
                            'endGame', 'feature', 'temp', 'pnum', 'wantsToPlay', 'bad_rate', 'letters', 'woe', 'B',
                            'hangman', 'random', 'output', 'IV', 'randomWord', 'myFunction', 'playNewGame', 'agg',
                            'roc_plot', 'target', 'fig', 'num_buck', 'G', 'f', 'WoE', 'n_buck', 'fnum',
                            'playIndefinitely', 'ru.hse.sc.hangman', 'scanner', 'InteractiveGameSession', 'fpr'},
                           {'ru.hse.sc.hangman', 'plotly.express', 'numpy', 'java.util.Random', 'java.util.Scanner',
                            'java.io.PrintStream', 'bad_rate', 'zip', 'range', 'math', 'len', 'woe', 'log',
                            'java.util.Set', 'java.util.List'})])
def test_RepoParser(file_languages: List[str], file_names: List[str], variables_check: Set, imports_check: Set):
    supported_languages = list(set(file_languages))
    repo = try_find_repo(str(Path.cwd() / "test_sources"), "tested_repo")
    repo_parser = RepoParser(repo, supported_languages)
    repo_parser.parse_files()

    assert variables_check == set(repo_parser.variables)
    assert imports_check == set(repo_parser.imports)

