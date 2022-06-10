import math

from git_repo_extract.commits_info import get_commits_info_floored
from git_repo_extract.star_track import file_writer, get_stargazer_info, get_top_repos
from git_repo_extract.repo_ops import operate_temporary_repo, write_down_content

from joblib import delayed, parallel_backend, Parallel

from pathlib import Path


def main():
    source_path = Path.cwd().parent / "cloned_repos"

    key = "MY_KEY"  # TODO Удалить

    temp_repo_path = source_path / "temp_repos"
    commits_info_path = source_path / "commits_info.txt"
    source_repos_path = source_path / "selected_repos.txt"

    # write_stargazers_repos(str(stargazers_path), start_repo, key)
    write_repo_commits(str(source_repos_path), str(temp_repo_path), str(commits_info_path), start_batch=1)

def write_repo_commits(repos_file_path: str,
                       temp_repo_path: str,
                       commits_info_path: str,
                       batch_size: int = 10,
                       start_batch: int = 0) -> None:
    """
    Opens repos_file_path file, gets top repositories from it. Then operates each repository concurrently
    using commits_info.get_commits_info_base.
    Writes all the commits to commits_info_path file

    :param start_batch: number of batch from which to start (useful if previous run failed on this batch)
    :param batch_size: number of repositories should be paralleled before their return values will be written down
    :param repos_file_path: Path to file with repository info
    :param temp_repo_path: Path where to place temporary repositories
    :param commits_info_path: Path where to create file with commits info
    :return: None
    """

    repos = get_top_repos(repos_file_path, 150)
    batches = []

    for i in range(math.ceil(len(repos)/batch_size)):
        batches.append(repos[i*batch_size:min((i+1)*batch_size, len(repos)-1)])

    with open(commits_info_path, "a") as f:
        for i, batch in enumerate(batches):
            print(f"Processing batch {i}")
            if i < start_batch:
                continue
            with parallel_backend(backend="multiprocessing"):
                parallel = Parallel(n_jobs=-1, verbose=100)
                funcs = (delayed(operate_temporary_repo)(repo_path=temp_repo_path,
                                                         url=repo[0],
                                                         operation=get_commits_info_floored,
                                                         arguments=(250,),
                                                         verbose=2)
                         for repo in batch)
                for repo_result in parallel(funcs):
                    write_down_content(repo_result, f)


def write_stargazers_repos(path: str, url: str, github_key: str) -> None:
    """
    Method to look through most popular repos' stargazers' repositories
    :param path: where to write info about stargazers' repos
    :param url: url of repo from which to look through stargazers
    :param github_key: your GitHub key to get access to GitHubApi
    :return:
    """
    content = get_stargazer_info(url, github_key)
    iterator = (file_writer(line, path) for line in content)
    tuple(iterator)  # итерируюсь через генератор


if __name__ == "__main__":
    main()
