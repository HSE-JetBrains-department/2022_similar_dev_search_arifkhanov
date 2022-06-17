import json
import math
from pathlib import Path
from typing import Union, Dict, List, TextIO, Callable

from joblib import Parallel, delayed


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


def parallel_function(function: Callable, source, verbose: int = 50, **kwargs):
    """
    Flexible way to operate certain function in parallel way

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

    parallel = Parallel(n_jobs=-1, backend="multiprocessing", verbose=verbose)
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


def get_enry_path() -> Path:
    """
    Get enry.exe file path
    :return: enry Path object
    """
    return Path.cwd().parent / "source_code" / "enry" / "enry.exe"
