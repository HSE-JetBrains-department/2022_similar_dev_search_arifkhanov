import time
from calendar import calendar
from collections import Counter
from tqdm import tqdm
from commits_info import write_down_content

from github import Github, RateLimitExceededException
from typing import Dict, Any, List


def get_stargazer_info(repo_name: str, github_key: str, path: str = None,
                       max_user_stars: int = 300,
                       per_page: int = 80) -> Any[List[Dict], Dict]:
    """
    Method investigates stargazers of given repository and return the most popular
    repositories amongst them.

    :param repo_name: name of repository which stargazers to investigate
    :param github_key: personal github key to get access to the github API
    :param path: path to .jsonl file to log all the repositories
    :param max_user_stars: skip users with bigger amount of stars
    :param per_page: pagination parameter for GitHub request API

    :return: Dict
    """
    top_repos = Counter()
    account = Github(github_key, per_page=per_page)

    repo = None
    while True:
        try:
            repo = account.get_repo(repo_name)
            break
        except RateLimitExceededException:
            sleep_until_unblock(account)
            continue
        # other errors should strike

    users = []
    for user in tqdm(repo.get_stargazers()):
        try:
            user_stars = user.get_starred().totalCount
            if user_stars > max_user_stars:
                continue
            users.append(user)
            continue
        except RateLimitExceededException:
            sleep_until_unblock(account)
            user_stars = user.get_starred().totalCount
            if user_stars > max_user_stars:
                continue
            users.append(user)
            continue

    for user in tqdm(users):
        try:
            reps = user.get_starred()
            for r in reps:
                top_repos[r.full_name] += 1
        except RateLimitExceededException:
            sleep_until_unblock(account)
            reps = user.get_starred()
            for r in reps:
                top_repos[r.full_name] += 1

    if path is not None:
        write_down_content(dict(top_repos), path)
    return top_repos


def sleep_until_unblock(account: Github) -> None:
    """
    Method to minimize code duplication. Forces the programme to wait until
    GitHub rate_limit restarts
    :param account: your GitHub account
    :return: None
    """
    search_rate_limit = account.get_rate_limit().search
    print('search remaining: {}'.format(search_rate_limit.remaining))
    reset_timestamp = calendar.timegm(search_rate_limit.reset.timetuple())
    # add 10 seconds to be sure the rate limit has been reset
    sleep_time = reset_timestamp - calendar.timegm(time.gmtime()) + 10
    time.sleep(sleep_time)
