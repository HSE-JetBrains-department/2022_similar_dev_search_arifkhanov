import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterator, List, Tuple, Union

from dulwich.repo import Repo
from git.repo import Repo as GRepo

from .clone_progress import CloneProgress

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))


def operate_repo(repo_path: str,
                 url: str,
                 operation: Callable[[Repo, Any], Iterator],
                 arguments: Tuple) -> List:
    """
    Method for given repo parsing using given operation

    :param arguments: arguments to operation method
    :param repo_path: path where to create temporary folder
    :param url: name of user and repo in format "user/repo"
    :param operation: operation with repo itself
    :return:
    """
    repo = try_find_repo(repo_path, url)
    if repo is None:
        return operate_temporary_repo(temp_repo_path=repo_path, url=url, operation=operation, arguments=arguments)
    else:
        return operate_existing_repo(repo=repo, url=url, operation=operation, arguments=arguments)


def operate_temporary_repo(temp_repo_path: str,
                           url: str,
                           operation: Callable[[Repo, Any], Iterator],
                           arguments: Tuple) -> List:
    """
    Method for temporary repo operation such as commits_info_extraction or inner content parse,
    when there is no need to create constant folder for repo

    :param arguments: arguments to operation method
    :param temp_repo_path: path where to create temporary folder
    :param url: name of user and repo in format "user/repo"
    :param operation: operation with repo itself
    :return: List of parsed objects
    """
    logger.log(1, f"\tStarted operating {url}")

    prefix = url
    if url.startswith("https://"):
        prefix = "/".join(url.split("/")[-2:])
    prefix = prefix.replace("/", "_")

    result = []
    try:
        with tempfile.TemporaryDirectory(prefix=f"{prefix}_",
                                         dir=temp_repo_path) as td:
            repo = get_repo_from_url(td, get_repo_url(url))

            logger.log(2, f"\tInstalled {url} in {td}")

            result = operate_existing_repo(repo, url, operation, arguments)

            logger.log(2, f"\t{url} repo closed")
    except RuntimeError as e:
        logger.exception(f"Runtime Exception {e}")
    except IOError as e:
        logger.exception(f"IO Exception {e}")

    logger.log(1, f"\t{url} exited TempFolder")
    return result


def operate_existing_repo(repo: Repo, url: str, operation: Callable[[Repo, Any], Iterator], arguments: Tuple) -> List:
    """
    Method for constant repo operation such as commits_info_extraction or inner content parse,
    when there is already an existing repo

    :param repo: dulwich Repo object of given repository
    :param operation: operation with repo itself
    :param arguments: arguments to operation method
    :param url: name of user and repo in format "user/repo"
    :return:
    """
    result = []
    try:
        for entity in operation(repo, *arguments):
            try:
                result.append(entity)
            except RuntimeError as e:
                logger.exception(f"Operation error {e}")
    except KeyError as e:
        logger.exception(f"Key error {e}")

    logger.log(2, f"\t{url} finished operations")
    repo.close()

    return result


def get_repo_from_url(path: str, url: str = None) -> Repo:
    """
    Return Repo object from a given folder
    If the url param is given will download repo to url folder and then return object

    :param path: path to the folder with repository (with .git folder) / or where to save repo
    :param url: link to git repository

    :return: dulwich.Repo object of given repo
    """
    if url is not None:
        GRepo.clone_from(url, path, progress=CloneProgress(f"{url} downloading"))
    repo = Repo(path)

    return repo


def get_repo_url(repo_name: str) -> str:
    """
    Get link for the given repository

    :param repo_name: full repository name in format "{author}/{repository_name}"
    :return: link for the repo
    """
    if repo_name.startswith("https://"):  # already a url
        return repo_name
    return f"https://github.com/{repo_name}"


def try_find_repo(directory_path: str, repo_name: str, download: bool = False) -> Union[None, Repo]:
    """
    Method tries to find given repository folder in the given path

    :param download: download repo if doesn't exist
    :param directory_path: path of the directory where to search
    :param repo_name: name of searched repo in format {author_name}/{repository_name}
    :return: Either found repo or None
    """
    repo = None
    found_repo = False
    temp_repo_name = repo_name.replace("/", "_")  # {author_name}_{repository_name}

    with os.scandir(directory_path) as it:
        for entry in it:
            if entry.is_dir() and entry.name.startswith(temp_repo_name):
                try:
                    repo = get_repo_from_url(entry.path)
                    found_repo = True
                except RuntimeError as e:
                    logger.exception(f"Runtime Error while reading repo in {entry.path}\n{e}")
                    found_repo = False

    if download and not found_repo:
        repo_path = Path(directory_path) / temp_repo_name
        os.makedirs(repo_path)
        repo = get_repo_from_url(str(repo_path), get_repo_url(repo_name))

    return repo


def get_repos_url(repo: Repo) -> str:
    try:
        return (repo.get_config().get((b'remote', b'origin'), b'url')).decode()
    except KeyError as e:
        logger.exception(f"Did not found key {e}")
        return repo.path.split("\\")[-1].split("/")[-1]  # чтоб наверняка
