import concurrent.futures
import logging
import os
from os.path import dirname
from pathlib import Path

from lxml import etree
from whoosh import index
from whoosh.qparser import QueryParser, MultifieldParser

from data_structure.SemagramAnnotation import SemagramAnnotation

dir_path = Path(dirname(dirname(__file__))) / 'indices'

extraction = etree.Element("extraction")


def get_sentences_from_index(query_data: SemagramAnnotation, index_num: int, verbose: bool):
    """
    no check su sense1 (ID del concetto associato al semagram) poiché ha sempre un valore.
    :param query_data:
    :param index_num:
    :param verbose:
    :return:
    """
    if verbose:
        logging.info(f'Querying index {index_num} ...')

    ix = index.open_dir(dir_path / Path('index_' + str(index_num)))
    with ix.searcher() as searcher:

        if query_data.sense2.babelsynset:
            flag = 'b_syn'
            query = QueryParser('annotations', ix.schema).parse(
                f'{query_data.sense1.babelsynset} {query_data.sense2.babelsynset}')
            results = searcher.search(query, limit=None)

            if results.estimated_length() == 0:
                flag = 'b_syn + txt'
                query = MultifieldParser(['annotations', 'free_text'], ix.schema).parse(
                    f'{query_data.sense1.babelsynset} {query_data.sense2.text}')
                results = searcher.search(query, limit=None)
        else:
            flag = 'b_syn + txt'
            query = MultifieldParser(['annotations', 'free_text'], ix.schema).parse(
                f'{query_data.sense1.babelsynset} {query_data.sense2.text}')
            results = searcher.search(query, limit=None)

        h = [(hit.fields(), hit.score) for hit in results]

    return flag, h


class IndexProcess:

    def __new__(cls, query: SemagramAnnotation, verbose: bool):
        with concurrent.futures.ProcessPoolExecutor(os.cpu_count()) as executor:
            future_to_index = {executor.submit(get_sentences_from_index, query, index_num, verbose): index_num for
                               index_num in range(10)}

            hits = etree.SubElement(extraction, "hits",
                                    babelsynset_1=query.sense1.babelsynset, name_1=query.sense1.text,
                                    babelsynset_2=query.sense2.babelsynset, name_2=query.sense2.text)
            for future in concurrent.futures.as_completed(future_to_index):
                file = future_to_index[future]
                try:
                    flag, index_results = future.result()
                    for item in index_results:
                        hit = etree.SubElement(hits, "hit", got_by=flag, score=str(item[1]))

                        annotations = etree.SubElement(hit, "annotations")
                        sentence = etree.SubElement(hit, "sentence")

                        annotations.text = item[0]['annotations']
                        sentence.text = item[0]['free_text']
                except Exception as exc:
                    print('Generated an exception', (file, exc))

        return etree.tostring(hits)
