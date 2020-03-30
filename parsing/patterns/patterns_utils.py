import pickle
from collections import defaultdict, OrderedDict, deque, Counter
from operator import itemgetter
from os.path import dirname
from pathlib import Path

from lxml import etree
from nltk.corpus import wordnet

from data_structure.Item import Item

file = 'accessory'
PATTERN_PATH = Path(dirname(dirname(__file__))) / 'patterns' / 'data' / Path(f'{file}_patterns.xml')


def get_pattern_supersense1(synsets: list):
    encountered_wn_synsets = []
    for syn in synsets:
        print(syn)
        '''
        # Init deque and its possible elements.
        # '''
        queue = deque()
        for wn_syn in bn_to_wn_dict[syn]:
            s = wordnet.synset(wn_syn)
            queue.append(s)
            encountered_wn_synsets.append(s)

        while queue:
            wn_syn = queue.popleft()
            for hyp in wn_syn.hypernyms():
                queue.append(hyp)
                encountered_wn_synsets.append(hyp)

    sorted_cnt = OrderedDict(sorted(Counter(encountered_wn_synsets).items(), key=itemgetter(1), reverse=True))
    for k, v in sorted_cnt.items():
        print(k, v)


def get_pattern_supersense2(synsets: list):
    di = defaultdict(list)
    for syn in synsets:
        '''
        # Init deque and its possible elements.
        # '''
        queue = deque()
        encountered_wn_synsets = []
        for wn_syn in bn_to_wn_dict[syn]:
            s = wordnet.synset(wn_syn)
            queue.append(s)
            encountered_wn_synsets.append(s)

        while queue:
            wn_syn = queue.popleft()
            for hyp in wn_syn.hypernyms():
                queue.append(hyp)
                encountered_wn_synsets.append(hyp)

        di[syn] = encountered_wn_synsets

    for k, v in di.items():
        print(k,v)

#     print(k, v)
    # sorted_cnt = OrderedDict(sorted(Counter(encountered_wn_synsets).items(), key=itemgetter(1), reverse=True))
    # for k, v in sorted_cnt.items():
    #     print(k, v)


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

# get_pattern_supersense1(concepts)
get_pattern_supersense2(concepts)

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
