import concurrent.futures
import logging
import os

logging.basicConfig(level=logging.INFO)
verbose = True


def spawn_index_process(index_num: int, _verbose: bool):
    # return SubsetProcess(subset_num, _verbose)
    return True


if __name__ == '__main__':
    if verbose:
        logging.info(f'Querying Semantically Enriched Wikipedia ...')

    with concurrent.futures.ProcessPoolExecutor(min(32, os.cpu_count() + 4)) as executor:
        future_to_file = {executor.submit(spawn_index_process, i, verbose): i for i in range(10)}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                if verbose:
                    logging.info(future.result())
            except Exception as exc:
                print('Generated an exception', (file, exc))
