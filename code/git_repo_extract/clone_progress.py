from git import RemoteProgress
from tqdm import tqdm


class CloneProgress(RemoteProgress):
    def __init__(self, progress_name):
        super().__init__()
        self.pbar = tqdm(desc=progress_name)

    def update(self, op_code, cur_count, max_count=None, message=''):
        self.pbar.total = max_count
        self.pbar.n = cur_count
        self.pbar.refresh()
