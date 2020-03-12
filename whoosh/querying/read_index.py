import os.path
from builtins import print
from os.path import dirname
from pathlib import Path

from whoosh import index
from whoosh.qparser import QueryParser

dir_path = Path(dirname(dirname(__file__))) / 'indices' / 'index_0'

if __name__ == '__main__':
    if os.path.exists(dir_path):

        exists = index.exists_in(dir_path)
        ix = index.open_dir(dir_path)

        with ix.searcher() as searcher:
            query = QueryParser('annotations', ix.schema).parse('bn:00043021n bn:00081263n')
            results = searcher.search(query, limit=None)

            print(results.estimated_length())
            '''for r in results:
                print('Result:', r)
                print('Score:', r.score)
                print('\n')'''
