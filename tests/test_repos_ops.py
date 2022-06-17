import pathlib

import dulwich.repo
import pytest

from source_code.git_repo_extract.repo_ops import try_find_repo


@pytest.mark.parametrize("path, repo_name",
                         [(pathlib.Path.cwd().parent / "tests" / "test_sources", "tested_repo")])
def test_try_find_repo(path: pathlib.Path, repo_name: str):
    test_repo = try_find_repo(str(path), repo_name)
    assert_repo = dulwich.repo.Repo(str(path / "tested_repo"))

    assert test_repo.path == assert_repo.path
