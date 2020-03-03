import concurrent.futures
import os

from mth.FolderThread import FolderThread


def make_folder_thread(folder_num: int):
    return FolderThread(folder_num)


class SubsetThread:
    def __new__(cls, subset_num: int):

        subset_dir_annotations = []

        with concurrent.futures.ProcessPoolExecutor(min(32, os.cpu_count() + 4)) as executor:
            future_to_file = {executor.submit(make_folder_thread, i): i
                              for i in range(10 * subset_num, 10 * (subset_num + 1) - 1)}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    ann_text = future.result()
                    subset_dir_annotations.append(ann_text)
                except Exception as exc:
                    print('Generated an exception', (file, exc))

        return subset_dir_annotations
