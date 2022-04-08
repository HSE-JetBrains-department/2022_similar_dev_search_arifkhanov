import time
from typing import Dict, Any, List

from calendar import calendar
from collections import Counter
from github import Github
from tqdm import tqdm


def get_stargazer_info(repo_name: str, github_key: str,
                       max_user_stars: int = 300,
                       per_page: int = 100) -> Any[List[Dict], Dict]:
    """
    Method investigates stargazers of given repository and return the most popular
    repositories amongst them.

    :param repo_name: name of repository which stargazers to investigate
    :param github_key: personal github key to get access to the github API
    :param max_user_stars: skip users with bigger amount of stars
    :param per_page: pagination parameter for GitHub request API

    :return: Dict
    """
    top_repos = Counter()
    account = Github(github_key, per_page=per_page)

    sleep_until_unblock(account)
    repo = account.get_repo(repo_name)

    users = []
    for user in tqdm(repo.get_stargazers()):
        sleep_until_unblock(account)  # not sure this is optimal way. It will be called each iteration
        user_stars = user.get_starred().totalCount
        if user_stars > max_user_stars:
            continue
        users.append(user)

    for user in tqdm(users):
        sleep_until_unblock(account)
        reps = user.get_starred()
        for r in reps:
            top_repos[r.full_name] += 1

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
    sleep_time = max(0.01, reset_timestamp - calendar.timegm(time.gmtime()) + 10)
    time.sleep(sleep_time)
