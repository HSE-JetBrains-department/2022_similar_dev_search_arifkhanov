from typing import Any,Dict, Iterator, Tuple

import json
import difflib
from dulwich.diff_tree import TreeChange
from dulwich.repo import Repo


def get_diffs_num(repos: Repo, sha1: bytes, sha2: bytes) -> Tuple[int, int]:
    """
    A method that gives blob differences
    Args:
        :param repos: source repository
        :param sha1: old blob's sha
        :param sha2: new blob's sha
    Returns:
        :return (Added, Deleted)
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
    return added, deleted


def get_commits_info_floored(repo: Repo, limit: int = -1) -> Iterator[Dict[str, Any]]:
    """
      A method returns Dictionaries with info about authors commits on given repo

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
        :param limit: limit of entities to check. Useful for pipeline check
      Returns:
        :return Iterator of dicts
    """
    repo_url = (repo.get_config().get((b"remote", b"origin"), b"url")).decode()
    i = 0
    for walk in repo.get_walker():
        name = walk.commit.author.decode()
        mail = name[name.find("<") + 1:-1]
        name = name[:name.find(">")].strip()

        for changes in walk.changes():
            if not isinstance(changes, list):
                changes = [changes]

            for change in changes:
                try:
                    content = process_change(change, repo)
                except RuntimeError:
                    continue
                content["repo_url"] = repo_url
                content["name"] = name
                content["mail"] = mail
                content["commit_id"] = walk.commit.id

                if limit != -1 and i == limit:
                    break
                i += 1
                yield content


def process_change(ch: TreeChange, repo: Repo) -> Dict:
    """
    Method for parsing blob change info into dict

    Arguments
        :param ch: entry of a Repo walker
        :param repo: source Repo
    Returns
        :return: dictionary with necessary elements
    """
    content = {"path": ch.new.path, "blob_id": ch.new.sha}

    if ch.old.sha is None:
        content["added"] = len(repo.get_object(ch.new.sha).data.decode().splitlines())
        content["deleted"] = 0
    elif ch.new.sha is None:
        content["deleted"] = len(repo.get_object(ch.old.sha).data.decode().splitlines())
        content["added"] = 0
    else:
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
