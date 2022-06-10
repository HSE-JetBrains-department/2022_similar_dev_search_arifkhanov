import calendar
import logging
import time

from collections import Counter
from typing import Any, Iterator, List, Tuple

from github import BadCredentialsException, Github, GithubException, RateLimitExceededException
from tqdm import tqdm

logger = logging.getLogger(__name__)


def get_stargazer_info(repo_name: str,
                       github_key: str,
                       max_user_stars: int = 300,
                       per_page: int = 100) -> Iterator[str]:
    """
    Method investigates stargazers of given repository and return the most popular
    repositories amongst them.

    :param repo_name: name of repository which stargazers to investigate
    :param github_key: personal github key to get access to the github API
    :param max_user_stars: limit of repos taken from user
    :param per_page: pagination parameter for GitHub request API

    :return: Dict
    """
    account = Github(github_key, per_page=per_page)

    repo = None
    while repo is None:
        try:
            repo = account.get_repo(repo_name)
        except RateLimitExceededException as e:
            logger.exception(f"GitHub api limit: {e}")
            sleep_until_unblock(account)
        except BadCredentialsException as e:
            raise ValueError(f"Wrong token provided - {github_key}, exception - {e}")

    for user in tqdm(repo.get_stargazers()):
        try:
            user_stars = user.get_starred()
            for i, repos in enumerate(user_stars):
                if i > max_user_stars:
                    break
                yield repos.full_name
        except RateLimitExceededException as e:
            sleep_until_unblock(account)
        except GithubException as e:
            logger.exception(f"GithubException {e}")


def sleep_until_unblock(account: Github) -> None:
    """
    Method to minimize code duplication. Forces the programme to wait until
    GitHub rate_limit restarts
    :param account: your GitHub account
    :return: None
    """
    search_rate_limit = account.get_rate_limit().search
    print("search remaining: {}".format(search_rate_limit.remaining))
    reset_timestamp = calendar.timegm(search_rate_limit.reset.timetuple())
    # add 10 seconds to be sure the rate limit has been reset
    sleep_time = max(reset_timestamp - calendar.timegm(time.gmtime()), 0)
    time.sleep(sleep_time + 10)


def file_writer(line: str, path: str):
    """
    Appends a string line to a given file
    :param line: dictionary of elements
    :param path: name of file
    :return: None
    """
    with open(path, "a") as ap:
        ap.write(line + "\n")


def get_top_repos(path: str, n_top_repos: int = 100) -> List[Tuple[Any, int]]:
    """
    Extracts all the repositories from the generated file from file_writer
    and returns Top used repositories
    :param path: path to file with list of repositories
    :param n_top_repos: limit of given number of top repos
    :return: List
    """
    top_repos = Counter()
    with open(path, "r") as rp:
        for line in rp:
            top_repos[line.rstrip("\n")] += 1

    return top_repos.most_common(n_top_repos)
