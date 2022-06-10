import random
import time

from pathlib import Path

from joblib import delayed, parallel_backend, Parallel

from src.git_repo_extract.repo_ops import write_down_content


def check_multithread_write():

    commits_info_path = Path.cwd().parent / "cloned_repos/test_multithreading_writing.txt"

    with open(str(commits_info_path), "a") as f:
        with parallel_backend(backend="multiprocessing"):
            parallel = Parallel(n_jobs=-1)
            funcs = (delayed(execution_method)(i) for i in range(100))
            for repo_result in parallel(funcs):
                write_down_content(repo_result, f)


def execution_method(i):
    print(f"Process {i}")
    lines = ["line1", "line2", "line3"]
    iterator = ({i: x} for x in lines)
    time.sleep(random.random()*2)
    return [x for x in iterator]