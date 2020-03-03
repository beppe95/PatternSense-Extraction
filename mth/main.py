import concurrent.futures
import os
import pickle
import time
from os.path import dirname
from pathlib import Path

from mth.SubsetThread import SubsetThread

DATASET_PATH = Path(dirname(dirname(__file__))) / 'sew_subset'


def make_subset_thread(subset_num: int):
    return SubsetThread(subset_num)


if __name__ == '__main__':
    num_dataset_subdirs = len([f.path for f in os.scandir(DATASET_PATH) if f.is_dir()])

    complete_annotations = []

    s = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(min(32, os.cpu_count() + 4)) as executor:
        future_to_file = {executor.submit(make_subset_thread, i): i for i in range(10)}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                ann_text = future.result()
                complete_annotations.append(ann_text)
            except Exception as exc:
                print('Generated an exception', (file, exc))

    with open('test.pkl', 'wb') as f:
        pickle.dump(complete_annotations, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(time.perf_counter() - s)
