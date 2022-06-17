import click

from git_repo_extract.commits_info import get_commits_info_floored
from git_repo_extract.star_track import get_stargazer_info, get_top_repos
from git_repo_extract.repo_ops import operate_temporary_repo
from code_parsing.code_handle import parallelize_extraction
from utils import *


@click.group()
def cli():
    """
    A group of cli methods
    """
    pass


@cli.command()
@click.option("--repos_file_path", default=SELECTED_REPOS_FILE, type=click.Path())
@click.option("--temp_repo_path", default=TEMP_REPOS_FOLDER, type=click.Path())
@click.option("--commits_info_path", default=COMMITS_INFO_FILE, type=click.Path())
@click.option("--batch_size", default=10, type=int)
@click.option("--start_batch", default=0, type=int)
@click.option("--commits_number", default=100, type=int)
def write_repo_commits(repos_file_path: Path,
                       temp_repo_path: Path,
                       commits_info_path: Path,
                       batch_size: int,
                       start_batch: int,
                       commits_number: int) -> None:
    """
    Opens repos_file_path file, gets top repositories from it. Then operates each repository concurrently
    using commits_info.get_commits_info_base.
    Writes all the commits to commits_info_path file

    :param commits_number: max number of commits should be parsed in each repository
    :param start_batch: number of batch from which to start (useful if previous run failed on this batch)
    :param batch_size: number of repositories should be paralleled before their return values will be written down
    :param repos_file_path: Path to file with repository info
    :param temp_repo_path: Path where to place temporary repositories
    :param commits_info_path: Path where to create file with commits info
    :return: None
    """

    repos = [elem[0] for elem in get_top_repos(repos_file_path, 150)]
    batches = split_into_batches(repos, batch_size)

    with commits_info_path.open("a") as f:
        for i, batch in enumerate(batches):
            print(f"Processing batch {i}")
            if i < start_batch:
                continue

            result = parallel_function(operate_temporary_repo,  # function
                                       batch,  # source
                                       50,  # verbose
                                       repo_path=str(temp_repo_path),  # kwargs
                                       operation=get_commits_info_floored,
                                       arguments=(commits_number,),
                                       url=None)
            for repo_result in result:
                write_down_content(repo_result, f)


@cli.command()
@click.argument("github_key", type=str)
@click.option("--path", default=SELECTED_REPOS_FILE, type=click.Path())
@click.option("--url", default="scikit-learn/scikit-learn", type=str)
@click.option("--limit_stargazers", default=1000, type=int)
def write_stargazers_repos(github_key: str, path: Path, url: str, limit_stargazers: int) -> None:
    """
    Method to look through most popular repos' stargazers' repositories
    :param limit_stargazers: maximum number of stargazers parsed
    :param path: where to write info about stargazers' repos
    :param url: url of repo from which to look through stargazers
    :param github_key: your GitHub key to get access to GitHubApi
    :return:
    """
    content = get_stargazer_info(url, github_key, limit_stargazers=limit_stargazers)
    for line in content:
        file_writer(line, path)


@cli.command()
@click.option("--json_path", default=COMMITS_INFO_FILE, type=click.Path())
@click.option("--var_imp_path", default=VARIABLES_IMPORTS_FILE, type=click.Path())
@click.option("--temp_repo_path", default=TEMP_REPOS_FOLDER, type=click.Path())
@click.option("--supported_languages", default=["python", "java", "javascript"], multiple=True)
def write_imports_variables(json_path: Path, var_imp_path: Path, temp_repo_path: Path, supported_languages: List[str]):
    """
    Method opens path with commits dataset and parses it in order to get variables
    and imports of each author. It writes them
    :param var_imp_path: Where to store parsed results
    :param supported_languages: which programming languages should be overviewed
    :param temp_repo_path: path to folder, where temporaryDirectories for repositories should be created
    :param json_path: path to dataset with commit_info files
    :return: None
    """
    with json_path.open("r") as rf:
        parsed_lines = (json.loads(line) for line in rf)
        result = parallelize_extraction(str(temp_repo_path), parsed_lines, supported_languages, 300)

        with var_imp_path.open("a") as af:
            for repo_line_result in result:
                write_down_content(repo_line_result, af)


if __name__ == "__main__":
    cli()
