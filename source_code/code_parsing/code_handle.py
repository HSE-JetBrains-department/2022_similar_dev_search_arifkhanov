from typing import Dict, List, Iterable

from dulwich.repo import Repo
from joblib import parallel_backend, Parallel, delayed
from tqdm import tqdm

from .RepoParser import RepoParser
from source_code.git_repo_extract.repo_ops import operate_temporary_repo


def parallelize_extraction(temp_repo_path: str,
                           parsed_lines: Iterable,
                           supported_languages: List[str],
                           commits_limit: int):
    """
    Method decomposes extract_from_json function
    :param commits_limit: maximum number of commits that should be parsed inside of repo
    :param temp_repo_path: path to folder, where temporaryDirectories for repositories should be created
    :param parsed_lines: lines of different repos commit_info data
    :param supported_languages: which programming languages should be overviewed
    :return:
    """
    with parallel_backend(backend="multiprocessing"):
        parallel = Parallel(n_jobs=1, verbose=100)
        funcs = (delayed(operate_temporary_repo)(temp_repo_path=temp_repo_path,
                                                 url=line[0]["repo_url"],
                                                 operation=extract_repo_variables_imports,
                                                 arguments=(line, supported_languages, commits_limit))
                 for line in parsed_lines if line)
        return parallel(funcs)


def extract_repo_variables_imports(repo: Repo,
                                   commits_info_list: List[Dict],
                                   supported_languages: List[str],
                                   commits_limit: int = 1000):
    """
    Method that parses given repository and gets variables and imports data for given commit_infos
    :param commits_limit: maximum number of commits that should be parsed inside of repo
    :param supported_languages: list of programming languages that should be parsed
    :param repo: repo object to being parsed
    :param commits_info_list: list of commits_info objects for current repo
    :return: Iterator of dicts with author file data
    """
    repo_parser = RepoParser(repo, supported_languages=supported_languages)
    repo_parser.parse_files(commits_limit)

    for entity in tqdm(commits_info_list, desc="Checking entities"):

        if not entity:
            continue

        result = {"author": entity["author_name"], "path": entity["file_path"]}
        variables = repo_parser.handle_author_variables(entity)
        imports = repo_parser.handle_author_imports(entity)

        if not (variables and imports):  # something gone wrong
            continue

        result["imports"] = list(imports)
        result["variables"] = list(variables)  # make it suitable for json

        yield result
