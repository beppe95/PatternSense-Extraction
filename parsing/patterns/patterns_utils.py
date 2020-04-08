from math import floor, ceil
import pickle
from collections import defaultdict, OrderedDict, deque, Counter
from operator import itemgetter
from os.path import dirname
from pathlib import Path

import numpy as np
from lxml import etree
from nltk.corpus import wordnet
from nltk.corpus.reader.wordnet import Synset

from data_structure.Item import Item
from data_structure.MatrixItem import MatrixItem

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')


def get_all_hypernyms(wn_synset: Synset):
    """
    Init deque and its possible elements.

    :param wn_synset:
    :return:
    """
    queue = deque()
    mi = MatrixItem(synset=wn_synset, depth=0)
    mi.item_covered.add(wn_synset)
    queue.append(mi)
    all_hypernyms = [mi]
    while queue:
        wn_syn = queue.popleft()
        hyps = wn_syn.synset.hypernyms()
        for hyp in hyps:

            filt = filter(lambda elem: elem.synset == hyp, all_hypernyms)
            try:
                mi = next(iter(filt))
                mi.add_hyponym(wn_syn)
                mi.item_covered.update(wn_syn.item_covered)

                q = deque()
                q.append(mi)
                while q:
                    e = q.popleft()
                    for x in filter(lambda elem: e in elem.hyponyms, all_hypernyms):
                        x.item_covered.update(mi.item_covered)
                        q.append(x)

            except StopIteration:
                mi = MatrixItem(synset=hyp, depth=wn_syn.depth + 1)
                mi.add_hyponym(wn_syn)
                mi.add_item_cov(hyp)
                mi.item_covered.update(wn_syn.item_covered)
                queue.append(mi)
                all_hypernyms.append(mi)

    return all_hypernyms


def get_pattern_supersense(synsets_pairs: list, cover_threshold: float = 0.7):
    """

    :param synsets_pairs:
    :param cover_threshold:
    :return:
    """
    for pair in synsets_pairs:
        concept, filler = pair
        concept_wn_synsets = get_all_hypernyms(wordnet.synset(bn_to_wn_dict[concept][0]))
        filler_wn_synsets = get_all_hypernyms(wordnet.synset(bn_to_wn_dict[filler][0]))

        li1 = sorted([(c.synset, len(c.item_covered)) for c in concept_wn_synsets], key=itemgetter(1))
        li2 = sorted([(f.synset, len(f.item_covered)) for f in filler_wn_synsets], key=itemgetter(1))

        row_number = len(li1)
        col_number = len(li2)
        supersenses_graph = np.zeros(shape=(row_number, col_number), dtype=int)

        for i in range(row_number):
            for j in range(col_number):
                supersenses_graph[i][j] += li1[i][1]

        for j in range(col_number):
            for i in range(row_number):
                supersenses_graph[i][j] += li2[j][1]

        # discuterne con il Prof.
        desired_cover_W = floor(np.amax(supersenses_graph) * cover_threshold)
        # desired_cover_W = ceil(np.amax(supersenses_graph) * cover_threshold)

        result = np.where(supersenses_graph == desired_cover_W)
        for e, y in zip(result[0], result[1]):
            print(f'{li1[e][0]}, {li2[y][0]}')
        break


with open('bn_to_wn_dict.pkl', mode='rb') as babel_file:
    bn_to_wn_dict = pickle.load(babel_file)

with open(PATTERN_PATH, mode='rb') as slot_file:
    xml_parser = etree.XMLParser(encoding='utf-8')
    patterns = etree.parse(slot_file, xml_parser).getroot()

text_pattern_dict = defaultdict()
for ids in patterns:
    for markers in ids:
        for pat in markers:
            test_pat = (pat.get('direction'), pat.text)
            if test_pat not in text_pattern_dict:
                obj = Item(1)
                obj.add_to_list((ids.get('concept_babelsynset'), ids.get('filler_babelsynset')))
                text_pattern_dict[test_pat] = obj
            else:
                obj = text_pattern_dict[test_pat]
                obj.increment_frequency()
                obj.add_to_list((ids.get('concept_babelsynset'), ids.get('filler_babelsynset')))

sorted_dict = OrderedDict(sorted(text_pattern_dict.items(), key=itemgetter(1), reverse=True))

# for k, v in sorted_dict.items():
#     print(k, v)

"""
('L_', 'is') 
[2, [
    ('bn:00010183n', 'bn:00012339n'), 
    ('bn:00080022n', 'bn:00012339n')
    ]
]
"""

concepts_fillers_pairs = sorted_dict[('L_', 'is')].concepts_fillers_list
get_pattern_supersense(concepts_fillers_pairs)
