from dulwich import porcelain
from dulwich.repo import Repo


def get_repo_from_url(path: str, url: str = None) -> Repo:
    """
    Return Repo object from a given folder
    If the url param is given will download repo to url folder and then return object

    Args:
        :param path: path to the folder with repository (with .git folder) / or where to save repo
        :param url: link to git repository

    Returns
        :return: dulwich.Repo object of giver repo
    """

    if url is not None:
        porcelain.clone(url, path)

    return Repo(path)
