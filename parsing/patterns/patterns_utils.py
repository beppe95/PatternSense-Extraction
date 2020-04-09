import os
import pickle
from collections import deque, OrderedDict, defaultdict
from itertools import chain
from math import floor
from operator import itemgetter
from os.path import dirname
from pathlib import Path

import numpy as np
from lxml import etree
from more_itertools import unique_everseen
from nltk.corpus import wordnet
from nltk.corpus.reader.wordnet import Synset

from data_structure.Item import Item

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')

resource_patterns_path = Path(dirname(dirname(__file__))) / 'pattern_sense'
if not os.path.exists(resource_patterns_path):
    os.mkdir(resource_patterns_path)

if not os.path.exists(resource_patterns_path / 'accessory.xml'):
    with open(resource_patterns_path / 'accessory.xml', mode='wb') as out:
        pass

supersenses = etree.Element('supersenses')


def get_all_hypernyms(wn_synset: Synset, ret: str = 'no_depth'):
    """
    Init deque and its possible elements.

    :param wn_synset:
    :param ret:
    :return:
    """
    queue = deque()
    queue.append((wn_synset, 0))
    all_hypernyms = [(wn_synset, 0)]
    while queue:
        wn_syn, depth = queue.popleft()
        for hyp in wn_syn.hypernyms():
            queue.append((hyp, depth + 1))
            all_hypernyms.append((hyp, depth + 1))

    return all_hypernyms if ret == 'depth' else [hyp[0] for hyp in all_hypernyms]


def get_pattern_supersense(synsets_pairs: list, cover_threshold: float = 0.7):
    """

    :param synsets_pairs:
    :param cover_threshold:
    :return:
    """
    # all_pairs_hypernyms = []
    # s = set()
    # for p in synsets_pairs:
    #     # possibile che uno di sti due sia vuoto perchè manca nel dizionario bn_to_wn
    #     if not bn_to_wn_dict[p[0]]:
    #         s.add(p[0])
    #     if not bn_to_wn_dict[p[1]]:
    #         s.add(p[1])
    # return s

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
        for wordnet_synset1 in hyp_pair[0]:
            i = concepts_hypernyms_dict[wordnet_synset1]
            for wordnet_synset2 in hyp_pair[1]:
                j = fillers_hypernyms_dict[wordnet_synset2]
                supersenses_graph[i, j] += 1

        for wordnet_synset2 in hyp_pair[1]:
            j = fillers_hypernyms_dict[wordnet_synset2]
            for wordnet_synset1 in hyp_pair[0]:
                i = concepts_hypernyms_dict[wordnet_synset1]
                supersenses_graph[i, j] += 1

    desired_cover_W = floor(np.amax(supersenses_graph) * cover_threshold)

    result_W = np.where(supersenses_graph >= desired_cover_W)

    supersenses_set = set(chain.from_iterable(
        (list(concepts_hypernyms_dict.keys())[list(concepts_hypernyms_dict.values()).index(row_index)],
         list(fillers_hypernyms_dict.keys())[list(fillers_hypernyms_dict.values()).index(column_index)])
        for row_index, column_index in zip(result_W[0], result_W[1])
    )) if result_W else Exception('Empty set')

    n_supersense_hyper = {s: len(get_all_hypernyms(s)) - 1 for s in supersenses_set}

    temp_supersenses_list = [(list(concepts_hypernyms_dict.keys())[list(concepts_hypernyms_dict.values()).index(e)],
                              list(fillers_hypernyms_dict.keys())[list(fillers_hypernyms_dict.values()).index(y)])
                             for e, y in zip(result_W[0], result_W[1])]

    supersenses_list = sorted([((super_c, n_supersense_hyper[super_c]), (super_f, n_supersense_hyper[super_f])) for
                               super_c, super_f in temp_supersenses_list], key=lambda item: (item[0][1], item[1][1]))

    return [(s[0][0], s[1][0]) for s in supersenses_list]


def check_supersense_key(_ss1, _ss2):
    for h_c, n1 in _ss1:
        for h_f, n2 in _ss2:
            if (h_c, h_f) in supersenses_occurrences:
                return h_c, h_f
    return None


with open('bn_to_wn_dict.pkl', mode='rb') as babel_file:
    bn_to_wn_dict = pickle.load(babel_file)

with open(PATTERN_PATH, mode='rb') as slot_file:
    xml_parser = etree.XMLParser(encoding='utf-8')
    patterns = etree.parse(slot_file, xml_parser).getroot()

# ['flit.v.01']
# print(len(bn_to_wn_dict.keys()))
# with open('bn_to_wn_dict.pkl', mode='wb') as babel_file:
#     pickle.dump(bn_to_wn_dict, babel_file)

text_pattern_dict = defaultdict()
for ids in patterns:
    for markers in ids:
        for pat in markers:
            test_pat = (pat.get('direction'), pat.text)
            if test_pat not in text_pattern_dict:
                obj = Item(1)
                obj.add_to_concepts_fillers_list((ids.get('concept_babelsynset'), ids.get('filler_babelsynset')))
                obj.add_to_examples((markers.get('concept_name'), markers.get('filler_name')))
                text_pattern_dict[test_pat] = obj
            else:
                obj = text_pattern_dict[test_pat]
                obj.increment_frequency()
                obj.add_to_concepts_fillers_list((ids.get('concept_babelsynset'), ids.get('filler_babelsynset')))
                obj.add_to_examples((markers.get('concept_name'), markers.get('filler_name')))

sorted_dict = OrderedDict(sorted(text_pattern_dict.items(), key=itemgetter(1), reverse=True))
#
# sss = set()
# for k in sorted_dict.keys():
#     concepts_fillers_pairs = sorted_dict[k].concepts_fillers_list
#     # pattern_supersenses = get_pattern_supersense(concepts_fillers_pairs)
#     sss.update(get_pattern_supersense(concepts_fillers_pairs))
# print(sss)

for k in sorted_dict.keys():
    concepts_fillers_pairs = sorted_dict[k].concepts_fillers_list
    pattern_supersenses = get_pattern_supersense(concepts_fillers_pairs)
    supersenses_occurrences = defaultdict.fromkeys(pattern_supersenses, 0)

    for c, f in concepts_fillers_pairs:

        ss1 = list(unique_everseen(
            sorted(get_all_hypernyms(wordnet.synset(bn_to_wn_dict[c][0]), ret='depth'), key=itemgetter(1),
                   reverse=True)))
        ss1.sort(key=itemgetter(1))

        ss2 = list(unique_everseen(
            sorted(get_all_hypernyms(wordnet.synset(bn_to_wn_dict[f][0]), ret='depth'), key=itemgetter(1),
                   reverse=True)))
        ss2.sort(key=itemgetter(1))

        key = check_supersense_key(ss1, ss2)
        if key:
            supersenses_occurrences[key] += 1

    itemMaxValue = max(supersenses_occurrences.items(), key=itemgetter(1))
    supersense_key_list = [k for k, v in supersenses_occurrences.items() if v == itemMaxValue[1]]

    supersenses_set = set(chain.from_iterable((s1, s2) for s1, s2 in supersense_key_list))

    n_supersense_hyper = {s: len(get_all_hypernyms(s)) - 1 for s in supersenses_set}

    index, hypernyms_sum = -1, -1
    for _i in range(len(supersense_key_list)):
        current_hypernyms = n_supersense_hyper[supersense_key_list[_i][0]] + n_supersense_hyper[
            supersense_key_list[_i][1]]
        if current_hypernyms > hypernyms_sum:
            index, hypernyms_sum = _i, current_hypernyms

    if k[1]:
        pattern = etree.SubElement(supersenses, 'pattern', direction=k[0], value=k[1])
    else:
        pattern = etree.SubElement(supersenses, 'pattern', direction=k[0], value='')

    slot = etree.SubElement(pattern, 'slot', name='accessory',
                            supersense1=supersense_key_list[index][0].name(),
                            supersense2=supersense_key_list[index][1].name())

    s_examples = [f'{c} {k[1]} {f}' if k[1] and k[0] == 'L_'
                  else f'{f} {k[1]} {c}' if k[1] and k[0] == 'R_'
                  else f'{c} {f}' for c, f in sorted_dict[k].examples]

    examples = etree.SubElement(slot, 'examples')
    examples.text = ', '.join(s_examples)

with open(resource_patterns_path / 'accessory.xml', mode='wb') as out:
    out.write(etree.tostring(supersenses, xml_declaration=True, encoding='utf-8', pretty_print=True))
