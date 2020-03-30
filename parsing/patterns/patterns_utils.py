import pickle
from collections import defaultdict, OrderedDict, deque
from operator import itemgetter
from os.path import dirname
from pathlib import Path

from lxml import etree
from nltk.corpus import wordnet

from data_structure.Item import Item

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')


def get_pattern_supersense(synsets: list):
    queue = deque()
    for wn_syn in bn_to_wn_dict['bn:00009589n']:
        queue.append(wordnet.synset(wn_syn))

    while queue:
        wn_syn = queue.popleft()
        print(wn_syn, wn_syn.hypernyms())
        for hyp in wn_syn.hypernyms():
            queue.append(hyp)
    print(queue)


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
                obj.add_to_concept_bn_set(ids.get('concept_babelsynset'))
                obj.add_to_filler_bn_set(ids.get('filler_babelsynset'))
                text_pattern_dict[test_pat] = obj
            else:
                obj = text_pattern_dict[test_pat]
                obj.increment_counter()
                obj.add_to_concept_bn_set(ids.get('concept_babelsynset'))
                obj.add_to_filler_bn_set(ids.get('filler_babelsynset'))

sorted_dict = OrderedDict(sorted(text_pattern_dict.items(), key=itemgetter(1), reverse=True))

# ('L_', 'is a')
# [4,
#  {'bn:00009589n', 'bn:00069164n', 'bn:00020414n', 'bn:00068899n'},
#  {'bn:00027574n', 'bn:00009566n', 'bn:00083813v', 'bn:00024410n'}
# ]

# print(sorted_dict[('L_', 'is a')])
concepts = sorted_dict[('L_', 'is a')].concept_bn_set
fillers = sorted_dict[('L_', 'is a')].filler_bn_set

get_pattern_supersense(concepts)


# supersense1_dict, supersense2_dict = None, None
# for k, v in sorted_dict.items():
#     print(k,v)
#     supersense1_dict = defaultdict.fromkeys(v.concept_bn_set)
#     supersense2_dict = defaultdict.fromkeys(v.filler_bn_set)

# # devo contare quante volte ci sono i WN_SYNSET non i babelsynset
# wn_count = defaultdict()
# for k in supersense1_dict.keys():
#     print(k)
#     if k in bn_to_wn_dict:
#         wordnet_synsets_list = bn_to_wn_dict[k]
#         for syn in wordnet_synsets_list:
#             wn_count = defaultdict()
#             wn_syn = wordnet.synset(syn)
#             print(wn_syn)
#
#             #wn_count[wn_syn.name()]
#             while wn_syn.hypernyms():
#                 print(wn_syn.hypernyms())
#                 print(wn_syn.hypernyms()[0]) # ci sono più ipernomi, ocio!
#                 wn_syn = wn_syn.hypernyms()[0]
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
#
# print(wn_syn.hypernyms())
# wn_syn = wn_syn.hypernyms()[0]
# print(wn_syn)
# break
