import os
import pickle
from collections import deque, OrderedDict, defaultdict
from itertools import chain, groupby
from math import floor
from operator import itemgetter
from os.path import dirname
from pathlib import Path
import numpy as np
from lxml import etree
from more_itertools import unique_everseen
from nltk import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk.corpus.reader.wordnet import Synset
from nltk import pos_tag
from data_structure.Item import Item

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')
simmetric_patterns = ['and', 'or', ', and', ', or', ',']
lemmatizer = WordNetLemmatizer()

resource_patterns_path = Path(dirname(dirname(__file__))) / 'pattern_sense'
if not os.path.exists(resource_patterns_path):
    os.mkdir(resource_patterns_path)

if not os.path.exists(resource_patterns_path / 'accessory.xml'):
    with open(resource_patterns_path / f'{file}.xml', mode='wb') as out:
        pass

patternsense = etree.Element('patternsense')


def get_all_hyponyms(wn_synset: Synset = None, ret: str = 'no_depth'):
    """
    :param wn_synset: for now bounded to 'physical_entity.n.01' synset
    :param ret:
    :return:
    """
    wn_synset = list(wordnet.all_synsets('n'))[1]
    queue = deque()
    queue.append((wn_synset, 0))
    all_hyponyms = [(wn_synset, 0)]
    while queue:
        wn_syn, depth = queue.popleft()
        for hyp in wn_syn.hyponyms():
            queue.append((hyp, depth + 1))
            all_hyponyms.append((hyp, depth + 1))

    return all_hyponyms if ret == 'depth' else [hyp[0] for hyp in all_hyponyms]


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
    ) for pair in synsets_pairs if bn_to_wn_dict[pair[0]] and bn_to_wn_dict[pair[1]]]

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

    supersenses_list = sorted([((super_c, n_supersense_hyper[super_c]), (super_f, n_supersense_hyper[super_f]))
                               for super_c, super_f in temp_supersenses_list],
                              key=lambda item: (item[0][1], item[1][1]))

    return [(s[0][0], s[1][0]) for s in supersenses_list]


def check_supersense_key(_ss1, _ss2):
    for h_c, n1 in _ss1:
        for h_f, n2 in _ss2:
            if (h_c, h_f) in supersenses_occurrences:
                return h_c, h_f
    return None


with open('bn_to_wn_dict.pkl', mode='rb') as babel_file:
    bn_to_wn_dict = pickle.load(babel_file)

with open('physical_entity_hypos.pkl', mode='rb') as pe_hypos:
    physical_entity_hypos = pickle.load(pe_hypos)

with open('hyponyms_dict.pkl', mode='rb') as hypo_dict:
    hyponym_dict = pickle.load(hypo_dict)

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
                obj.add_to_concepts_fillers_list((ids.get('concept_babelsynset'), ids.get('filler_babelsynset')))
                obj.add_to_examples((markers.get('concept_name'), markers.get('filler_name')))
                text_pattern_dict[test_pat] = obj
            else:
                obj = text_pattern_dict[test_pat]
                obj.increment_frequency()
                obj.add_to_concepts_fillers_list((ids.get('concept_babelsynset'), ids.get('filler_babelsynset')))
                obj.add_to_examples((markers.get('concept_name'), markers.get('filler_name')))

key_to_delete = [([(k[0], k[1]), ('R_', k[1])]) for k in text_pattern_dict.keys()
                 if (k[0] == 'L_' and k[1] in simmetric_patterns) and ('R_', k[1]) in text_pattern_dict]

for left_key, right_key in key_to_delete:
    left_item = text_pattern_dict.pop(left_key)
    right_item = text_pattern_dict.pop(right_key)

    pattern = left_key[1]
    obj = Item(frequency=(left_item.frequency + right_item.frequency))
    obj.concepts_fillers_list = [*left_item.concepts_fillers_list, *right_item.concepts_fillers_list]
    obj.examples = [*left_item.examples, *right_item.examples]
    text_pattern_dict[('L_R', pattern)] = obj

sorted_dict = OrderedDict(sorted(text_pattern_dict.items(), key=itemgetter(1), reverse=True))

frequency_delete = set()
for k, v in sorted_dict.items():
    if k[1] is not None and v.frequency >= 3:
        for word_key, pos in pos_tag(k[1].split()):
            lem_word_key = lemmatizer.lemmatize(word_key)
            if lem_word_key != 'type' and lem_word_key in physical_entity_hypos and pos.startswith('N'):
                frequency_delete.add((k[0], k[1]))
    elif v.frequency < 3:
        frequency_delete.add((k[0], k[1]))

for ktd in frequency_delete:
    sorted_dict.pop(ktd)

#
# sss = set()
# for k in sorted_dict.keys():
#     concepts_fillers_pairs = sorted_dict[k].concepts_fillers_list
#     sss.update(get_pattern_supersense(concepts_fillers_pairs))
# print(sss)

for k in sorted_dict.keys():
    concepts_fillers_pairs = sorted_dict[k].concepts_fillers_list
    pattern_supersenses = get_pattern_supersense(concepts_fillers_pairs)
    supersenses_occurrences = defaultdict.fromkeys(pattern_supersenses, 0)

    for c, f in concepts_fillers_pairs:

        wn_concept = bn_to_wn_dict[c]
        wn_filler = bn_to_wn_dict[f]

        ss1 = []
        if wn_concept:
            ss1 = list(unique_everseen(
                sorted(get_all_hypernyms(wordnet.synset(wn_concept[0]), ret='depth'), key=itemgetter(1),
                       reverse=True)))
            ss1.sort(key=itemgetter(1))

        ss2 = []
        if wn_filler:
            ss2 = list(unique_everseen(
                sorted(get_all_hypernyms(wordnet.synset(wn_filler[0]), ret='depth'), key=itemgetter(1),
                       reverse=True)))
            ss2.sort(key=itemgetter(1))

        key = None
        if ss1 and ss2:
            key = check_supersense_key(ss1, ss2)

        if key:
            supersenses_occurrences[key] += 1

    supersense_key_list = [k for k, v in supersenses_occurrences.items() if v > 0]

    supersenses_set = set(chain.from_iterable((s1, s2) for s1, s2 in supersense_key_list))

    n_supersense_hyper = {s: len(get_all_hypernyms(s)) - 1 for s in supersenses_set}

    supersense_key_list = [(ss1.name(), ss2.name()) for ss1, ss2, _ in
                           sorted([(ss1, ss2, n_supersense_hyper[ss1] + n_supersense_hyper[ss2])
                                   for ss1, ss2 in supersense_key_list], key=lambda elem: elem[2])]

    first_pair = supersense_key_list[0]
    if first_pair[0] not in hyponym_dict:
        hyponym_dict[first_pair[0]] = {hypo.name() for hypo in get_all_hyponyms(wn_synset=first_pair[0])}

    if first_pair[1] not in hyponym_dict:
        hyponym_dict[first_pair[1]] = {hypo.name() for hypo in get_all_hyponyms(wn_synset=first_pair[1])}

    clusters_dict = defaultdict()
    clusters_dict[first_pair] = [first_pair]

    single_clusters = []
    for s1, s2 in supersense_key_list[1:]:

        if s1 not in hyponym_dict:
            hyponym_dict[s1] = {hypo.name() for hypo in get_all_hyponyms(wn_synset=s1)}

        if s2 not in hyponym_dict:
            hyponym_dict[s2] = {hypo.name() for hypo in get_all_hyponyms(wn_synset=s2)}

        for key in clusters_dict.keys():
            if s1 == key[0] and s2 in hyponym_dict[key[1]]:
                try:
                    clusters_dict[key].append((s1, s2))
                except KeyError:
                    single_clusters.append((s1, s2))
            elif s2 == key[1] and s1 in hyponym_dict[key[0]]:
                try:
                    clusters_dict[key].append((s1, s2))
                except KeyError:
                    single_clusters.append((s1, s2))
            else:
                single_clusters.append((s1, s2))

    for s1, s2 in single_clusters:
        clusters_dict[(s1, s2)] = [(s1, s2)]

    s_examples = [f'{c} {f}' for c, f in unique_everseen(sorted_dict[k].examples)]

    val_list = [v for vals in clusters_dict.values() for v in reversed(vals)]

    ord = [(v1, v2) for v1, v2, _ in
           sorted([(v[0], v[1], n_supersense_hyper[wordnet.synset(v[0])] + n_supersense_hyper[wordnet.synset(v[1])])
                   for v in val_list], key=lambda elem: elem[2], reverse=True)]

    examples_dict = {v: [] for v in ord}


    for ex in unique_everseen(s_examples):
        w0, w1 = ex.split(' ')
        try:
            w0_hypernyms = get_all_hypernyms(wn_synset=wordnet.synsets(w0)[0])
            w1_hypernyms = get_all_hypernyms(wn_synset=wordnet.synsets(w1)[0])

            for val_k in examples_dict.keys():
                if wordnet.synset(val_k[0]) in w0_hypernyms and wordnet.synset(val_k[1]) in w1_hypernyms:
                    examples_dict[(val_k[0], val_k[1])].append(ex)
                    break

        except IndexError:
            print(f'No hypernyms for {w0} or {w1}')
            pass

    if k[1]:
        pattern = etree.SubElement(patternsense, 'pattern', direction=k[0], value=k[1])
    else:
        pattern = etree.SubElement(patternsense, 'pattern', direction=k[0], value='')

    slot = etree.SubElement(pattern, 'slot', name=file)

    clusters = etree.SubElement(slot, 'clusters')

    for clust in clusters_dict.values():
        cluster = etree.SubElement(clusters, 'cluster')
        rank = 0
        for ss1, ss2 in clust:
            supersenses = etree.SubElement(cluster, 'supersenses',
                                           supersense1=ss1,
                                           supersense2=ss2,
                                           rank=str(rank))

            cluster_examples = [' '.join(ex.split(' ')) if k[0] == 'L' or k[0] == 'L_R'
                                else ' '.join(reversed(ex.split(' ')))
                                for ex in examples_dict[(ss1, ss2)]]

            examples = etree.SubElement(supersenses, 'examples')

            examples.text = '|'.join(
                                    [f' {k[1]} '.join(ex.split(' ')) if k[1]
                                     else ' '.join(ex.split(' '))
                                     for ex in examples_dict[(ss1, ss2)]]
                                    )
            rank += 1

with open('hyponyms_dict.pkl', mode='wb') as hypo_dict:
    pickle.dump(hyponym_dict, hypo_dict)

with open(resource_patterns_path / f'{file}.xml', mode='wb') as out:
    out.write(etree.tostring(patternsense, xml_declaration=True, encoding='utf-8', pretty_print=True))
