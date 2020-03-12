import concurrent.futures
import logging
import os
import time
from os.path import dirname
from pathlib import Path

from whoosh import index
from whoosh.qparser import QueryParser
from whoosh.query import Query

dir_path = Path(dirname(dirname(__file__))) / 'indices'


def get_sentences_from_index(query: Query, index_num: int, verbose: bool):
    if verbose:
        logging.info(f'Querying index {index_num} ...')

    ix = index.open_dir(dir_path / Path('index_' + str(index_num)))
    with ix.searcher() as searcher:
        query = QueryParser('free_text', ix.schema).parse('document')
        results = searcher.search(query, limit=None)
        print(results.estimated_length())
    # return results
    return True


class IndexProcess:

    def __new__(cls, query: Query, verbose: bool):
        with concurrent.futures.ProcessPoolExecutor(os.cpu_count()) as executor:
            future_to_index = {executor.submit(get_sentences_from_index, query, index_num, verbose): index_num for
                               index_num in
                               range(10)}
            for future in concurrent.futures.as_completed(future_to_index):
                file = future_to_index[future]
                try:
                    sentences = future.result()
                except Exception as exc:
                    print('Generated an exception', (file, exc))

        return True


if __name__ == '__main__':
    s = time.perf_counter()
    IndexProcess(None, True)
    print(time.perf_counter() - s)
