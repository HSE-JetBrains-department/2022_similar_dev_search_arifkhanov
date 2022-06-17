from pathlib import Path

import pytest

from source_code.git_repo_extract.SavedLanguagesHolder import SavedLanguagesHolder
from source_code.git_repo_extract.commits_info import define_file_language, get_diffs_num


def get_code(path: Path):
    with path.open("r") as rf:
        code = rf.readlines()
    return "".join(code)


@pytest.mark.parametrize("file_name, result",
                         [(Path.cwd().parent / "tests" / "test_sources" / "tested_repo" / "ipynb_code.ipynb", "jupyter notebook"),
                          (Path.cwd().parent / "tests" / "test_sources" / "tested_repo" / "java_code.java", "java"),
                          (Path.cwd().parent / "tests" / "test_sources" / "tested_repo" / "javascript_code.js", "javascript"),
                          (Path.cwd().parent / "tests" / "test_sources" / "tested_repo" / "python_code.py", "python")
                          ])
def test_define_file_language(file_name: Path, result: str):
    code = get_code(file_name)
    language_holder = SavedLanguagesHolder()

    language = define_file_language(str(file_name), code, language_holder)
    second_try = define_file_language(str(file_name), code, language_holder)

    assert language == second_try
    assert language == result


@pytest.mark.parametrize("old_text, new_text, deleted_result, added_result",
                         [("line1\nline2\nline3","line1\nline3", 1, 0),
                          ("line1\nline3", "line1\nline2\nline3", 0, 1),
                          ("line1\nline3", "line1\nline2", 1, 1)])
def test_get_diffs_num(old_text: str, new_text: str, deleted_result: int, added_result: int):
    added, deleted = get_diffs_num(old_text, new_text)
    assert added == added_result
    assert deleted == deleted_result
