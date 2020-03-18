import concurrent.futures
import logging
import os
import pickle
from os.path import dirname
from pathlib import Path

from my_whoosh.querying.SlotProcess import SlotProcess

logging.basicConfig(level=logging.INFO)
verbose = True

PARSED_DATA_PATH = Path(dirname(dirname(__file__))) / 'querying' / 'pattern_list.pkl'


def spawn_slot_process(slot_list: list, _verbose: bool):
    return SlotProcess(slot_list, _verbose)


if __name__ == '__main__':
    if verbose:
        logging.info(f'Get parsed semagram base ...')
    with open(PARSED_DATA_PATH, mode='rb') as inp:
        pattern_list = pickle.load(inp)

    for item in pattern_list:
        for t in item[1]:
            if not t.sense2.babelsynset:
                print(t)

    '''if verbose:
        logging.info(f'Querying SEW indices ...')

    with concurrent.futures.ProcessPoolExecutor(os.cpu_count()) as executor:
        future_to_file = {executor.submit(spawn_slot_process, pattern_list[i], verbose): pattern_list[i]
                          for i in range(len(pattern_list))}
        for future in concurrent.futures.as_completed(future_to_file):
            file = future_to_file[future]
            try:
                if verbose:
                    logging.info(future.result())
            except Exception as exc:
                print('Generated an exception', (file, exc))'''
