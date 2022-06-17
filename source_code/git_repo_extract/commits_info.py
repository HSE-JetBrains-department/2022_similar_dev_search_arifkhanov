import difflib
import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, Iterator, Tuple, Union

from dulwich.diff_tree import TreeChange
from dulwich.repo import Repo
from tqdm import tqdm

from source_code.git_repo_extract.SavedLanguagesHolder import SavedLanguagesHolder
from source_code.git_repo_extract.repo_ops import get_repos_url
from source_code.utils import get_enry_path

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))



def get_commits_info_floored(repo: Repo, limit: int = -1) -> Iterator[Dict[str, Any]]:
    """
      A method returns Dictionaries with info about authors commits on given repo

      Dict architecture:
      {
        repo_url
        author_name
        author_email
        commit_id
        programming_language
        file_path
        blob_id
        added_lines_num
        deleted_lines_num
      }

      Args:
        :param repo: source repository
        :param limit: limit of entities to check. Useful for pipeline check

      Returns:
        :return Iterator of dicts
    """
    languages_holder = SavedLanguagesHolder()
    repo_url = get_repos_url(repo)
    i = 0
    for walk in tqdm(repo.get_walker(), desc=f"{repo_url} processing"):
        name = walk.commit.author.decode()
        mail = name[name.find("<") + 1:-1]
        name = name[:name.find("<")].strip()

        for changes in walk.changes():
            if not isinstance(changes, list):
                changes = [changes]

            for change in changes:
                try:
                    content = process_change(change,
                                             repo,
                                             languages_holder)
                    if content is None:
                        continue
                except RuntimeError as e:
                    logger.exception(f"Runtime error {e}")
                    continue

                content["repo_url"] = repo_url
                content["author_name"] = name
                content["author_email"] = mail
                content["commit_id"] = walk.commit.id.decode()

                if limit != -1 and i >= limit:
                    return
                i += 1
                yield content


def get_diffs_num(old_content: str, new_content: str) -> Tuple[int, int]:
    """
    A method that gives blob differences
    Args:
        :param old_content: content of old version of blob
        :param new_content: content of new version
    Returns:
        :return (Added, Deleted)
    """
    old_content = old_content.splitlines()
    new_content = new_content.splitlines()

    differences = difflib.unified_diff(old_content, new_content)

    added = 0
    deleted = 0
    for line in differences:
        if line.startswith("+") and not line.startswith("++"):
            added += 1
        if line.startswith("-") and not line.startswith("--"):
            deleted += 1
    return added, deleted


def process_change(ch: TreeChange,
                   repo: Repo,
                   languages_holder: SavedLanguagesHolder,
                   max_line_restriction: int = -1) -> [Dict, None]:
    """
    Method for parsing blob change info into dict

    Arguments
        :param ch: entry of a Repo walker
        :param repo: source Repo
        :param languages_holder: accumulates information about repository files languages
        :param max_line_restriction: file analysis will be skipped if there added more than 'max_line_restriction'
            lines and None value will be returned. Negative value will make all files be counted
    Returns
        :return: dictionary with necessary elements or None if filetype doesn't suits language analysis
            or its added too many lines
    """
    if ch.new.sha is None:
        return None

    content = {"file_path": ch.new.path.decode(),
               "blob_id": ch.new.sha.decode()}

    text_to_define = repo.get_object(ch.new.sha).as_pretty_string().decode(encoding="latin-1")

    if ch.old.sha is None:
        content["added_lines_num"] = len(text_to_define.splitlines())
        content["deleted_lines_num"] = 0

    else:
        old_content = repo.get_object(ch.old.sha).as_pretty_string().decode(encoding="latin-1")

        diffs = get_diffs_num(old_content, text_to_define)
        content["added_lines_num"] = diffs[0]
        content["deleted_lines_num"] = diffs[1]

    if max_line_restriction >= 0 and content["added_lines_num"] < max_line_restriction:
        return None

    language = define_file_language(content["file_path"], text_to_define, languages_holder)

    if language is None:
        return None

    content["programming_language"] = language
    return content


def define_file_language(file_name: str, file_content: str, languages_holder: SavedLanguagesHolder) -> Union[str, None]:
    """
    Checks file on file_name and its content with Enry and returns its Programming language

    :param file_name: name of investigated file with its repository dir
    :param file_content: inner content of investigated file
    :param languages_holder: holder for already investigated files
    :return: str: language of file,  None: if file cannot be defined by language
    """
    lang = languages_holder.get_file_info(file_name)
    if lang is not None:
        return lang

    entity = eliminate_language(file_name, file_content)

    if entity["type"] != "Text" or\
            entity["vendored"] or\
            entity["language"] == "":
        return None

    return entity["language"].lower()


def eliminate_language(file_path: str, file_content: str) -> Dict:
    """
    Creates file with given content on given path. Extracts file language and deletes file
    :param file_path: Path for file creation
    :param file_content: Inner file data
    :return: File Language
    """
    file_name = file_path.split("/")[-1]
    path = get_enry_path()

    splitted_f_name = file_name.split(".")
    file_suffix = ""
    if len(splitted_f_name) != 0:
        file_suffix = splitted_f_name[-1]

    with tempfile.NamedTemporaryFile(mode="w+b",
                                     suffix="." + file_suffix,
                                     prefix=splitted_f_name[0] + "_",
                                     dir=str(path.parent),
                                     delete=False) as fp:
        try:
            fp.write(file_content)
            fp.close()

            value = subprocess.run([str(path), "-json", fp.name], capture_output=True, text=True).stdout
        except Exception as e:
            logger.exception(e)
        finally:
            os.unlink(fp.name)
    return json.loads(value)
