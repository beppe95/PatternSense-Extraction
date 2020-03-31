import pickle
from collections import defaultdict, OrderedDict, deque, Counter
from operator import itemgetter
from os.path import dirname
from pathlib import Path

from lxml import etree
from nltk.corpus import wordnet
from numpy import zeros

from data_structure.Item import Item

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')


def get_all_hypernyms(wn_synset: str):
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


def get_pattern_supersense(synsets_pairs: list):
    """
    Using the first hypernym only.

    :param synsets_pairs:
    :return:
    """
    concept, filler = synsets_pairs[4]

    concept_wn_synsets = get_all_hypernyms(wordnet.synset(bn_to_wn_dict[concept][0]))
    filler_wn_synsets = get_all_hypernyms(wordnet.synset(bn_to_wn_dict[filler][0]))

    kv1 = [(k, v) for k, v in Counter(concept_wn_synsets).items()]
    kv2 = [(k, v) for k, v in Counter(filler_wn_synsets).items()]

    row_number = len(kv1)
    col_number = len(kv2)
    supersenses_graph = zeros(shape=(row_number, col_number), dtype=int)
    for i in range(row_number):
        for j in range(col_number):
            supersenses_graph[i][j] += kv1[i][1]
    for j in range(col_number):
        for i in range(row_number):
            supersenses_graph[i][j] += kv2[j][1]

    print(supersenses_graph)


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

"""
('L_', 'is a') 
[4, [
    ('bn:00009589n', 'bn:00083813v'), 
    ('bn:00020414n', 'bn:00024410n'), 
    ('bn:00068899n', 'bn:00027574n'), 
    ('bn:00069164n', 'bn:00009566n')]]
"""

concepts_fillers_pairs = sorted_dict[('L_', 'is a')].concepts_fillers_list
get_pattern_supersense(concepts_fillers_pairs)
