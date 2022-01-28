import json

from dulwich.diff_tree import TreeChange
from dulwich.repo import Repo
import difflib
from typing import Dict, List, Union, Optional, Any


def get_diffs_num(repos: Repo, sha1: bytes, sha2: bytes) -> List[int]:
    """
    A method that gives blob differences
    Args:
        :param repos: source repository
        :param sha1: old blob's sha
        :param sha2: new blob's sha
    Returns:
        :return [Added, Deleted]
  """

    differences = difflib.unified_diff(repos.get_object(sha1).data.decode().splitlines(),
                                       repos.get_object(sha2).data.decode().splitlines())
    added = 0
    deleted = 0
    for line in differences:
        if line.startswith("+") and not line.startswith("++"):
            added += 1
        if line.startswith("-") and not line.startswith("--"):
            deleted += 1
    return [added, deleted]


def get_commits_info(repo: Repo, limit: int = -1) -> Dict:
    """
    A method returns Dictionary with info about authors commits on given repo

    Dict architecture:
    {
      name
      email
      commit_id {
        file_path {
          blob_id
          added
          modified
          deleted
        }
      }
    }

    Args:
        repo: source repository
        limit: limit of entities to check. Useful for pipeline check
    Returns: Dict
  """

    info = {}
    i = 0
    for r in repo.get_walker():
        name = r.commit.author.decode()
        mail = name[name.find('<') + 1:-1]
        name = name[:name.find('<')].strip()

        if name not in info:
            info[name] = {}
            info[name]['mail'] = mail

        if r.commit.id not in info[name]:
            info[name][r.commit.id] = {}

        for ch in r.changes():
            info[name][r.commit.id][ch.new.path] = {}
            info[name][r.commit.id][ch.new.path]['blob_id'] = ch.new.sha
            diffs = get_diffs_num(repo, ch.old.sha, ch.new.sha)
            info[name][r.commit.id][ch.new.path]['added'] = diffs[0]
            info[name][r.commit.id][ch.new.path]['deleted'] = diffs[1]
        if limit != -1 and i == limit:
            break
        i += 1
    return info


def get_commits_info_floored(repo: Repo, path: str = None, limit: int = -1) -> List[
    Dict[str, Union[Optional[int], Any]]]:
    """
      A method returns Dictionary with info about authors commits on given repo

      Dict architecture:
      {
        name
        email
        commit_id
        file_path
        blob_id
        added
        modified
        deleted
      }

      Args:
        :param repo: source repository
        :param path: jsonl file path, where to write
        :param limit: limit of entities to check. Useful for pipeline check
      Returns:
        :return List if path is None (dicts will be collected in a List)

    """

    info = []
    i = 0
    for r in repo.get_walker():
        name = r.commit.author.decode()
        mail = name[name.find('<') + 1:-1]
        name = name[:name.find('<')].strip()

        for ch in r.changes():
            try:
                content = process_change(ch, repo)
            except:
                continue

            content["name"] = name
            content["mail"] = mail
            content["commit_id"] = r.commit.id

            if path is not None:
                write_down_content(content, path)
            else:
                info.append(content)

        if limit != -1 and i == limit:
            break
        i += 1

    return info


def process_change(ch: TreeChange, repo: Repo) -> Dict:
    """
    Method for parsing blob change info into dict

    Arguments
        :param ch: entry of a Repo walker
        :param repo: source Repo
    Returns
        :return: dictionary with necessary elements
    """
    content = {}

    if ch.old.sha is None:
        content["path"] = ch.new.path
        content["blob_id"] = ch.new.sha
        content["added"] = len(repo.get_object(ch.new.sha).data.decode().splitlines())
        content["deleted"] = 0
    elif ch.new.sha is None:
        content["path"] = ch.old.path
        content["blob_id"] = ch.old.sha
        content["deleted"] = len(repo.get_object(ch.old.sha).data.decode().splitlines())
        content["added"] = 0
    else:
        content["path"] = ch.new.path
        content["blob_id"] = ch.new.sha
        diffs = get_diffs_num(repo, ch.old.sha, ch.new.sha)
        content["added"] = diffs[0]
        content["deleted"] = diffs[1]
    return content


def write_down_content(content: Dict, path: str) -> None:
    """
    Writes down object as json line into jsonl file
    :param content: dictionary from parsed change
    :param path: name of jsonl
    :return: None
    """
    with open(path, "a") as ap:
        ap.write(json.dumps(content))
        ap.write("\n")
