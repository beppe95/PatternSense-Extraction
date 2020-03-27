import concurrent.futures
import logging
import os

from parsing.sew.SubsetProcess import SubsetProcess

logging.basicConfig(level=logging.INFO)
verbose = True


def spawn_subset_process(subset_num: int, _verbose: bool):
    return SubsetProcess(subset_num, _verbose)


if __name__ == '__main__':
    if verbose:
        logging.info(f'Parsing Semantically Enriched Wikipedia ...')

    with concurrent.futures.ProcessPoolExecutor(min(32, os.cpu_count() + 4)) as executor:
        future_to_file = {executor.submit(spawn_subset_process, i, verbose): i for i in range(10)}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                if verbose:
                    logging.info(future.result())
            except Exception as exc:
                print('Generated an exception', (file, exc))
