import json
import math
from pathlib import Path
from typing import Union, Dict, List, TextIO, Callable

from joblib import Parallel, delayed

current_dir = Path(__file__)

PROJECT_DIRECTORY = [p for p in current_dir.parents if p.parts[-1] == 'source_code'][0].parent
CLONED_REPOS_FOLDER = PROJECT_DIRECTORY / "cloned_repos"
SELECTED_REPOS_FILE = CLONED_REPOS_FOLDER / "selected_repos.txt"
TEMP_REPOS_FOLDER = CLONED_REPOS_FOLDER / "temp_repos"
COMMITS_INFO_FILE = CLONED_REPOS_FOLDER / "commits_info.txt"
VARIABLES_IMPORTS_FILE = CLONED_REPOS_FOLDER / "variables_imports.txt"
SOURCE_CODE_FOLDER = PROJECT_DIRECTORY / "source_code"
ENRY_PATH = SOURCE_CODE_FOLDER / "enry" / "enry.exe"
TREE_SITTER_QUERIES_FOLDER = SOURCE_CODE_FOLDER / "code_parsing" / "tree-sitter_queries"
TREE_SITTER_GRAMMARS_FOLDER = SOURCE_CODE_FOLDER / "code_parsing" / "tree-sitter_grammars"


def update_dictionary(dictionary, key, value):
    """
    Simple method that adds key-value pair to dictionary and returns it

    :param dictionary: target dict
    :param key: key
    :param value: value of key
    :return: modified given dict
    """
    dictionary[key] = value
    return dictionary


def split_into_batches(array: List, batch_size: int) -> List[List]:
    """
    Simple method to split array into array of batches with elements of given array

    :param array: source array
    :param batch_size: size of one batch
    :return: array ogf batches
    """
    return [array[i * batch_size:min((i + 1) * batch_size, len(array))] for i in
            range(math.ceil(len(array) / batch_size))]


def parallel_function(function: Callable, source, n_jobs: int = -1, verbose: int = 50, **kwargs):
    """
    Flexible way to operate certain function in parallel way

    :param n_jobs: number of processes
    :param function: function to run asynchronously
    :param source: what to iterate asynchronously
    :param verbose: level of joblib parallel verbosity
    :param kwargs: arguments that should be passed to function.
            Should contain one None variable that will be used to pass source data
    :return: result of function operation over source
    """
    source_argument = ""
    for key, value in kwargs.items():
        if value is None:  # finding variable for passing source elements in it
            source_argument = key

    parallel = Parallel(n_jobs=n_jobs, backend="multiprocessing", verbose=verbose)
    funcs = (delayed(function)(**update_dictionary(kwargs.copy(), source_argument, element))
             for element in source if element)
    result = parallel(funcs)
    return result


def file_writer(line: str, path: Path):
    """
    Appends a string line to a given file

    :param line: dictionary of elements
    :param path: name of file
    :return: None
    """
    with path.open("a") as ap:
        ap.write(line + "\n")


def write_down_content(content: Union[Dict, str, List], f: TextIO) -> None:
    """
    Writes down object as json line into jsonl file.

    :param f: IO of writable file
    :param content: dictionary of elements
    :return: None
    """
    f.write(json.dumps(content))
    f.write("\n")
