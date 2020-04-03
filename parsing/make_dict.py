import pickle
from collections import defaultdict
from os.path import dirname
from pathlib import Path

from lxml import etree

from parsing.semagram_base.semagram_utils import get_lemmas_from_babelsynset

file = 'group'
SLOT_PATH = Path(dirname(dirname(__file__))) / 'parsing' / 'indices_extractions' / 'xml_slots' / Path(f'{file}.xml')

if __name__ == '__main__':
    with open(SLOT_PATH, mode='rb') as slot_file:
        xml_parser = etree.XMLParser(encoding='utf-8')
        extraction = etree.parse(slot_file, xml_parser).getroot()

    with open('ann_set.pkl', mode='rb') as ann_file:
        ann_set = pickle.load(ann_file)

    print(ann_set[2001])
    with open('annotations_dict.pkl', mode='rb') as dict_file:
        annotations_dict = pickle.load(dict_file)

    annotations_set = []
    for hits in extraction:
        for hit in hits:
            for s in hit[0].text.split():
                annotations_set.append(s)
