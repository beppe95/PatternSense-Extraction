import os.path
from whoosh import index
from whoosh.qparser import QueryParser

if __name__ == '__main__':
    if os.path.exists('parsing\\sew_index'):
        ix = index.open_dir('parsing\\sew_index')

        with ix.searcher() as searcher:
            query = QueryParser('annotations', ix.schema).parse('bn:00006608n')

            #By default, Searcher.search(myquery) limits the number of hits to 20, So the number of scored hits in the
            #Results object may be less than the number of matching documents in the index.

            results = searcher.search(query, terms=True)

            for r in results:
                print('Result:', r)
                print('Score:', r.score)
                print('\n')