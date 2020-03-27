import concurrent.futures
import logging
import os
import pickle

from parsing.sew.FolderProcess import FolderProcess

logging.basicConfig(level=logging.INFO)


def spawn_folder_process(folder_num: int, verbose: bool):
    return FolderProcess(folder_num, verbose)


class SubsetProcess:
    def __new__(cls, subset_num: int, verbose: bool):
        if verbose:
            logging.info(f'Parsing directories from {72 * subset_num} to {72 * (subset_num + 1) - 1} ...')

        subset_dir_annotations = []

        with concurrent.futures.ProcessPoolExecutor(min(32, os.cpu_count() + 4)) as executor:
            future_to_file = {executor.submit(spawn_folder_process, i, verbose): i
                              for i in range(72 * subset_num, 72 * (subset_num + 1))}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    ann_text = future.result()
                    subset_dir_annotations.append(ann_text)
                except Exception as exc:
                    print('Generated an exception', (file, exc))

        filename = 'annotations_subset_' + str(subset_num) + '.pkl'
        with open(filename, mode='wb') as output_file:
            pickle.dump(subset_dir_annotations, output_file, protocol=pickle.HIGHEST_PROTOCOL)

        return f'Folder subset {72 * subset_num, 72 * (subset_num + 1) - 1} done!'
