import os
import pickle
import time
from os.path import dirname
from pathlib import Path

from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD

schema = Schema(annotations=KEYWORD(stored=True),
                free_text=TEXT(stored=True, phrase=False))

PARSED_DATA_PATH = Path(dirname(dirname(__file__))) / 'parsing' / 'cleaned_files'


def do_indexing(index_num: str):
    index_path = 'indices/index_' + index_num
    if not os.path.exists(index_path):
        os.mkdir(index_path)
        ix = index.create_in(index_path, schema)

    ix = index.open_dir(index_path)

    with open(PARSED_DATA_PATH / Path('cl_' + index_num + '.pkl'), 'rb') as f:
        cleaned_list = pickle.load(f)

    i = 0
    s = time.perf_counter()
    writer = ix.writer(procs=os.cpu_count(), limitmb=512, multisegment=True, batchsize=10000)

    for item in cleaned_list:
        if i % 100000 == 0:
            print(f'Writing {i} item')
        writer.add_document(annotations=item[1], free_text=item[0])
        i += 1

    writer.commit()
    print(time.perf_counter() - s)


if __name__ == '__main__':
    do_indexing('0')
    # do_indexing('1')
    # do_indexing('2')
    # do_indexing('3')
    # do_indexing('4')
    # do_indexing('5')
    # do_indexing('6')
    # do_indexing('7')
    # do_indexing('8')
    # do_indexing('9')
