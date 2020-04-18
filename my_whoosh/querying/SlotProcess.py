import concurrent.futures
import logging
import os
import pickle
from os.path import dirname
from pathlib import Path

from lxml import etree

from data_structure.SemagramAnnotation import SemagramAnnotation
from my_whoosh.querying.IndexProcess import IndexProcess

logging.basicConfig(level=logging.INFO)
PARSED_DATA_PATH = Path(dirname(dirname(__file__))) / 'querying' / 'pattern_list.pkl'


def spawn_index_process(query: SemagramAnnotation, verbose: bool):
    return IndexProcess(query, verbose)


class SlotProcess:

    def __new__(cls, slot_list: list, verbose: True):
        if verbose:
            logging.info(f'Querying for slot:"{slot_list[0]}" data...')

        # if not os.path.exists(f'{slot_list[0]}.xml'):
        #     extraction = etree.Element("extraction", slot=slot_list[0])
        #     with open(f'{slot_list[0]}.xml', mode='wb') as out:
        #         out.write(etree.tostring(extraction, xml_declaration=True, encoding='utf-8', pretty_print=True))

        if not os.path.exists(f'{slot_list[0]}.txt'):
            with open(f'{slot_list[0]}.txt', mode='a', encoding='utf-8'):
                print('Create file')

        print(slot_list[1][499])

        # with concurrent.futures.ProcessPoolExecutor(1) as executor:
        #     future_to_file = {executor.submit(spawn_index_process, slot_list[1][query], verbose): slot_list[1][query]
        #                       for query in range(495,496)}
        #
        #     hits_list = []
        #     for future in concurrent.futures.as_completed(future_to_file):
        #         file = future_to_file[future]
        #         try:
        #             # xml_hits = future.result()
        #             # hits_list.append(etree.fromstring(xml_hits))
        #             print('ok')
        #         except Exception as exc:
        #             print('Generated an exception', (file, exc))

        #     with open(f'{slot_list[0]}.xml', mode='rb') as input_file:
        #         xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        #         xml_root = etree.parse(input_file, xml_parser).getroot()
        #
        #     for hits in hits_list:
        #         xml_root.append(hits)
        #
        # with open(f'{slot_list[0]}.xml', mode='wb') as out:
        #     out.write(etree.tostring(xml_root, xml_declaration=True, encoding='utf-8', pretty_print=True))

        return f'Slot {slot_list[0]} done'


if __name__ == '__main__':
    with open(PARSED_DATA_PATH, mode='rb') as inp:
        pattern_list = pickle.load(inp)

    SlotProcess(pattern_list[11], True)
