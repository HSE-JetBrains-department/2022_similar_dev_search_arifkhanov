import pathlib
from typing import List

import pytest

from source_code.utils import parallel_function, split_into_batches


def sum_args(A, B, C):
    return A + B + C


def test_parallel_functions():
    print(pathlib.Path.cwd())
    iterator = [i for i in range(1, 30)]
    results = parallel_function(sum_args, iterator, 0, A=1, B=2, C=None)

    assert [sum_args(1, 2, i) for i in iterator] == results


@pytest.mark.parametrize("arr, splitted_arr",
                         [([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]),
                          ([1, 2, 3, 4, 5, 6, 7, 8, 9], [[1, 2, 3], [4, 5, 6], [7, 8, 9]])])
def test_split_into_batches(arr: List[str], splitted_arr: List[List[str]]):
    result = split_into_batches(arr, 3)
    assert result == splitted_arr
