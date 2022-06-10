import json
import logging
import tempfile

from typing import Any,Callable, Dict, Iterator, List, TextIO, Tuple, Union

from dulwich.repo import Repo
from git.repo import Repo as GRepo

from .clone_progress import CloneProgress

logger = logging.getLogger(__name__)


def operate_temporary_repo(repo_path: str,
                           url: str,
                           operation: Callable[[Repo, Any], Iterator],
                           arguments: Tuple,
                           verbose: int = 0) -> List:
    """
    Method for temporary repo operation such as commits_info_extraction or inner content parse,
    when there is no need to create constant folder for repo
    :param arguments: arguments to operation method
    :param repo_path: path where to create temporary folder
    :param url: name of user and repo in format "user/repo"
    :param operation: operation with repo itself
    :param verbose: level of visibility 0 for nothing,
        1 for getting info about start and finish operation,
        2 for printing info about repo
    :return:
    """
    verbose_print(f"\tStarted operating {url}", verbose, 1)

    result = []
    try:
        with tempfile.TemporaryDirectory(prefix=f"{url.replace('/', '_')}_",
                                         dir=repo_path) as td:
            repo = get_repo_from_url(td, get_repo_url(url))

            verbose_print(f"\tInstalled {url} in {td}", verbose, 2)

            try:
                for entity in operation(repo, *arguments):
                    try:
                        result.append(entity)
                    except RuntimeError as e:
                        logger.exception(f"Operation error {e}")
            except KeyError as e:
                logger.exception(f"Key error {e}")

            verbose_print(f"\t{url} finished operations", verbose, 2)

            repo.close()
            verbose_print(f"\t{url} repo closed", verbose, 2)
    except RuntimeError as e:
        logger.exception(f"Runtime Exception {e}")
    except IOError as e:
        logger.exception(f"IO Exception {e}")

    verbose_print(f"\t{url} exited TempFolder", verbose, 1)
    return result


def verbose_print(string: str, level_given: int, level_to_pass: int) -> None:
    """
    Verbosed print handler

    :param string: given string
    :param level_given: given level of verbosity
    :param level_to_pass: level of verbosity required to being printed
    :return: None
    """
    if level_given >= level_to_pass:
        print(string)


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
    if repo_name.startswith("https://"):  # already a url
        return repo_name
    return f"https://github.com/{repo_name}"


def write_down_content(content: Union[Dict, str, List], f: TextIO) -> None:
    """
    Writes down object as json line into jsonl file.
    :param f: IO of writable file
    :param content: dictionary of elements
    :return: None
    """
    f.write(json.dumps(content))
    f.write("\n")
