import concurrent.futures
import logging
import os
import pickle
from os.path import dirname
from pathlib import Path

from lxml import etree
from whoosh import index
from whoosh.qparser import QueryParser, MultifieldParser

from data_structure.SemagramAnnotation import SemagramAnnotation

dir_path = Path(dirname(dirname(__file__))) / 'indices'
out_path = Path(dirname(dirname(__file__))) / 'querying' / 'material.txt'

extraction = etree.Element("extraction")


def get_sentences_from_index(query_data: SemagramAnnotation, index_num: int, verbose: bool = True):
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
        with concurrent.futures.ThreadPoolExecutor(10) as executor:
            future_to_index = {executor.submit(get_sentences_from_index, query, index_num, verbose): index_num for
                               index_num in range(10)}

            # hits = etree.SubElement(extraction, "hits",
            #                         babelsynset_1=query.sense1.babelsynset, name_1=query.sense1.text,
            #                         babelsynset_2=query.sense2.babelsynset, name_2=query.sense2.text)

        with open(out_path, mode='a', encoding='utf-8') as out_txt:
            out_txt.write(f'@{query.sense1.babelsynset}-{query.sense1.text},'
                          f' {query.sense2.babelsynset}-{query.sense2.text}\n')
            for future in concurrent.futures.as_completed(future_to_index):
                file = future_to_index[future]
                try:
                    flag, index_results = future.result()
                    for item in index_results:
                        # hit = etree.SubElement(hits, "hit", got_by=flag, score=str(item[1]))
                        #
                        # annotations = etree.SubElement(hit, "annotations")
                        # sentence = etree.SubElement(hit, "sentence")
                        #
                        # annotations.text = item[0]['annotations']
                        # sentence.text = item[0]['free_text']
                        out_txt.write(f'{flag}, {str(item[1])}\n'
                                      f'{item[0]["annotations"]}\n'
                                      f'{item[0]["free_text"]}\n\n')

                except Exception as exc:
                    print('Generated an exception', (file, exc))

        # return etree.tostring(hits)


if __name__ == '__main__':
    PARSED_DATA_PATH = Path(dirname(dirname(__file__))) / 'querying' / 'pattern_list.pkl'
    with open(PARSED_DATA_PATH, mode='rb') as inp:
        pattern_list = pickle.load(inp)

    slot = pattern_list[13][0]
    queries = pattern_list[13][1]

    if not os.path.exists(f'{slot}.xml'):
        extraction = etree.Element("extraction", slot=slot)
        with open(f'{slot}.xml', mode='wb') as out:
            out.write(etree.tostring(extraction, xml_declaration=True, encoding='utf-8', pretty_print=True))

    hits_list = []
    for cq in range(400,500):

        hit_list = []

        hits = etree.SubElement(extraction, "hits",
                                babelsynset_1=queries[cq].sense1.babelsynset, name_1=queries[cq].sense1.text,
                                babelsynset_2=queries[cq].sense2.babelsynset, name_2=queries[cq].sense2.text)

        for i in range(10):
            hit_list.append(get_sentences_from_index(queries[cq], i))

            for flag, index_results in hit_list:
                for item in index_results:
                    hit = etree.SubElement(hits, "hit", got_by=flag, score=str(item[1]))

                    annotations = etree.SubElement(hit, "annotations")
                    sentence = etree.SubElement(hit, "sentence")

                    annotations.text = item[0]['annotations']
                    sentence.text = item[0]['free_text']

        hits_list.append(hits)
        print(cq)

    with open(f'{slot}.xml', mode='rb') as input_file:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(input_file, xml_parser).getroot()

    for hits in hits_list:
        xml_root.append(hits)

    with open(f'{slot}.xml', mode='wb') as out:
        out.write(etree.tostring(xml_root, xml_declaration=True, encoding='utf-8', pretty_print=True))
