from math import floor
import pickle
from collections import defaultdict, OrderedDict, deque
from operator import itemgetter
from os.path import dirname
from pathlib import Path
from itertools import chain
import numpy as np
from lxml import etree
from nltk.corpus import wordnet
from nltk.corpus.reader.wordnet import Synset

from data_structure.Item import Item

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')


def get_all_hypernyms(wn_synset: Synset):
    """
    Init deque and its possible elements.

    :param wn_synset:
    :return:
    """
    queue = deque()
    queue.append(wn_synset)
    all_hypernyms = [wn_synset]
    while queue:
        wn_syn = queue.popleft()
        for hyp in wn_syn.hypernyms():
            queue.append(hyp)
            all_hypernyms.append(hyp)

    return all_hypernyms


def get_pattern_supersense(synsets_pairs: list, cover_threshold: float = 0.7):
    """

    :param synsets_pairs:
    :param cover_threshold:
    :return:
    """
    all_pairs_hypernyms = [(
        get_all_hypernyms(wordnet.synset(bn_to_wn_dict[pair[0]][0])),
        get_all_hypernyms(wordnet.synset(bn_to_wn_dict[pair[1]][0]))
    ) for pair in synsets_pairs]

    concepts_hypernyms_dict = {k: v for v, k in
                               enumerate(set([s for hyp_pair in all_pairs_hypernyms for s in hyp_pair[0]]))}

    fillers_hypernyms_dict = {k: v for v, k in
                              enumerate(set([s for hyp_pair in all_pairs_hypernyms for s in hyp_pair[1]]))}

    row_number = len(concepts_hypernyms_dict.keys())
    col_number = len(fillers_hypernyms_dict.keys())
    supersenses_graph = np.zeros(shape=(row_number, col_number), dtype=int)

    for hyp_pair in all_pairs_hypernyms:
        for ws1 in hyp_pair[0]:
            i = concepts_hypernyms_dict[ws1]
            for ws2 in hyp_pair[1]:
                j = fillers_hypernyms_dict[ws2]
                supersenses_graph[i, j] += 1

        for ws2 in hyp_pair[1]:
            j = fillers_hypernyms_dict[ws2]
            for ws1 in hyp_pair[0]:
                i = concepts_hypernyms_dict[ws1]
                supersenses_graph[i, j] += 1

    desired_cover_W = floor(np.amax(supersenses_graph) * cover_threshold)

    result_W = np.where(supersenses_graph >= desired_cover_W)

    supersenses_set = set(chain.from_iterable(
        (list(concepts_hypernyms_dict.keys())[list(concepts_hypernyms_dict.values()).index(e)],
         list(fillers_hypernyms_dict.keys())[list(fillers_hypernyms_dict.values()).index(y)])
        for e, y in zip(result_W[0], result_W[1])
    )) if result_W else Exception('Empty set')

    n_supersense_hyper = {s: len(get_all_hypernyms(s)) - 1 for s in supersenses_set}

    temp_supersenses_list = [(list(concepts_hypernyms_dict.keys())[list(concepts_hypernyms_dict.values()).index(e)],
                              list(fillers_hypernyms_dict.keys())[list(fillers_hypernyms_dict.values()).index(y)])
                             for e, y in zip(result_W[0], result_W[1])]

    supersenses_list = sorted([((super_c, n_supersense_hyper[super_c]), (super_f, n_supersense_hyper[super_f])) for
                               super_c, super_f in temp_supersenses_list], key=lambda item: (item[0][1], item[1][1]),
                              reverse=True)

    for ss in supersenses_list:
        print(ss)


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
('R_', 'into the')
 [4, [
        ('bn:00071766n', 'bn:00045342n'), 
        ('bn:00012873n', 'bn:00014249n'), 
        ('bn:00007329n', 'bn:00077910n'), 
        ('bn:00018038n', 'bn:00012873n')
     ]
 ]
"""

concepts_fillers_pairs = sorted_dict[('R_', 'into the')].concepts_fillers_list
get_pattern_supersense(concepts_fillers_pairs)
