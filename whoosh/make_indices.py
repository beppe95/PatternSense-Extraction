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

if __name__ == '__main__':
    if not os.path.exists('indices/index_9'):
        os.mkdir('indices/index_9')
        ix = index.create_in('indices/index_9', schema)

    ix = index.open_dir('indices/index_9')

    with open(PARSED_DATA_PATH / Path('cl_9.pkl'), 'rb') as f:
        cleaned_list_0 = pickle.load(f)

    i = 0
    s = time.perf_counter()
    writer = ix.writer(procs=os.cpu_count(), limitmb=512, multisegment=True, batchsize=10000)

    for item in cleaned_list_0:
        if i % 100000 == 0:
            print(f'Writing {i} item')
        writer.add_document(annotations=item[1], free_text=item[0])
        i += 1

    writer.commit()
    print(time.perf_counter() - s)
