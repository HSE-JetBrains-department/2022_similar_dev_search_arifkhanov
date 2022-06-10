import json

from typing import Dict, List

from dulwich.repo import Repo
from joblib import parallel_backend, Parallel, delayed

from .RepoParser import RepoParser
from ..git_repo_extract.repo_ops import operate_temporary_repo


def extract_from_json(json_path: str, temp_repo_path: str):
    """

    :param temp_repo_path:
    :param json_path:
    :return:
    """
    with open(json_path, "r") as f:
        with parallel_backend(backend="multiprocessing"):

            parallel = Parallel(verbose=100)
            parsed_lines = (json.loads(line) for line in f)

            funcs = (delayed(operate_temporary_repo)(temp_repo_path=temp_repo_path,
                                                     url=line[0]["repo_url"],
                                                     operation=extract_repo_variables_imports,
                                                     arguments=line,
                                                     verbose=2)
                     for line in parsed_lines if not line) # handle if not empty
            for repo_result in parallel(funcs):
                pass # TODO Реализовать, что делать с результатом

def extract_repo_variables_imports(repo: Repo, commits_info_list: List[Dict]):
    """

    :param repo:
    :param commits_info_list:
    :return:
    """
    repo_parser = RepoParser(repo)

    for entity in commits_info_list:
        if not entity:
            continue
        result = {"author": entity["author_name"]}
        if "file_path" in repo_parser.used_files:
            result.update(imports=repo_parser["file_path"]["imports"],
                          variables=repo_parser["file_path"]["variables"])
        result.update(repo_parser.handle_author_variables(entity))
        result.update(repo_parser.handle_author_imports(entity))

        yield result

