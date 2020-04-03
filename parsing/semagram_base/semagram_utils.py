import itertools
import json
import pickle
import urllib
from collections import defaultdict
from os.path import dirname
from pathlib import Path

import urllib3
from lxml import etree
from nltk import WordNetLemmatizer
from nltk.corpus import wordnet

from data_structure.SemagramAnnotation import SemagramAnnotation
from data_structure.Sense import Sense

SEMAGRAM_PATH = Path(dirname(dirname(__file__))) / 'semagram_base' / 'semagram_base.xml'
lemmatizer = WordNetLemmatizer()


def parse_xml_file(filename):
    """
    Parse the given XML file and bind each sentence inside it to the respective annotations.

    :param filename: XML file's path to parse
    :return: list containing sentences and respective annotations
    """
    with open(filename, mode='r') as semagram_base:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, xml_parser).getroot()

    free_text, annotations = xml_root[0].text, xml_root[1]
    tok_free_text = free_text.split('\n')

    start, end, i = 0, 0, 0

    result = []
    for sent in tok_free_text:
        token = sent.split()
        end = start + len(token) - 1

        babel_id = []
        while i <= (len(annotations) - 1) and int(annotations[i][3].text) <= end:
            babel_id.append(annotations[i][0].text)
            i += 1

        result.append((sent, ' '.join(babel_id)))
        start += len(token) + 1

    return result


def get_lemmas_from_babelsynset(synset: str, key: str, ret: str, search_lang: str = 'EN', target_lang: str = 'EN'):
    """
    Handles REST messages exchange with BabelNet server in order to get each gloss of our babel synset ID.

    :param synset: babel synset ID of the input concept
    :param key: key used to access BabelNet REST service
    :param search_lang: search language. Default language is ENGLISH: 'EN'.
    :param target_lang: target language. Default language is ENGLISH: 'EN'.
    :param ret: return type. 'OFF' for WordNetSense offset, 'LEMMA' for simpleLemma value.

    :return: 'OFF' for WordNetSense offset, 'LEMMA' for simpleLemma value.
    """

    # key = 'd98e5389-2438-4db4-8672-fcdd4ce6d4f9'    # key1
    # key2 = '34461ea6-4c3a-411f-9531-d9e3cae24954'   # key2
    # key3 = '8e149252-ac13-4e51-96ba-e7055f6d56e2'   # key3
    # key4 = '9f73a72d-0ad4-4f30-bf46-5249377326cc'

    service_url = 'https://babelnet.io/v5/getSynset'
    params = {
        'id': synset,
        'key': key,
        'searchLang': search_lang,
        'targetLang': target_lang
    }

    url = service_url + '?' + urllib.parse.urlencode(params)

    http = urllib3.PoolManager()
    response = http.request('GET', url)
    results = json.loads(response.data.decode('utf-8'))

    if ret == 'OFF':
        return set([sense['properties']['wordNetOffset']
                    for sense in results['senses'] if sense['type'] == 'WordNetSense']) if 'message' not in results \
            else set()

    elif ret == 'LEMMA':
        return set([' '.join(
            (' '.join(lemmatizer.lemmatize(sense['properties']['simpleLemma'].lower()).split('_'))).split('-'))
            for sense in results['senses']]) if 'message' not in results else set()

    else:
        raise ValueError('Value for "ret" variable not handled! Must be "OFF" or "LEMMA"')


def get_babelsynsets_from_lemmas(lemma: str, key: str, search_lang: str = 'EN', target_lang: str = 'EN'):
    """
    Handles REST messages exchange with BabelNet server in order to get each gloss of our babel synset ID.

    :param lemma: lemma of the input concept
    :param key: key used to access BabelNet REST service
    :param search_lang: search language. Default language is ENGLISH: 'EN'.
    :param target_lang: target language. Default language is ENGLISH: 'EN'.

    :return: N/A.

    """
    # key = 'd98e5389-2438-4db4-8672-fcdd4ce6d4f9'    # key1
    # key2 = '34461ea6-4c3a-411f-9531-d9e3cae24954'   # key2
    # key3 = '8e149252-ac13-4e51-96ba-e7055f6d56e2'   # key3

    service_url = 'https://babelnet.io/v5/getSenses'
    params = {
        'lemma': lemma,
        'key': key,
        'searchLang': search_lang,
        'targetLang': target_lang
    }

    url = service_url + '?' + urllib.parse.urlencode(params)

    http = urllib3.PoolManager()
    response = http.request('GET', url)
    babel_synset = json.loads(response.data.decode('utf-8'))

    for sense in babel_synset:
        print(sense)


def parse_semagram_base():
    """
    """
    key = 'use your BabelNet key'

    with open(SEMAGRAM_PATH, mode='r') as semagram_base:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, xml_parser).getroot()

    semagram_annotations, semagram_synsets_set, filler_synsets_set = list(), set(), set()
    for semagram in xml_root:
        for s in semagram.attrib['babelsynset'].split(','):
            if s and s not in semagram_synsets_set:
                semagram_synsets_set.add(s)
            for slot in list(semagram):
                for value in list(slot):
                    for v in value.attrib['babelsynset'].split(','):
                        if v and v not in filler_synsets_set:
                            filler_synsets_set.add(v)
                        for t in value.text.split(','):
                            sense1 = Sense(semagram.attrib['name'], s)
                            sense2 = Sense(t.split('#')[0], v)
                            semagram_annotations.append(SemagramAnnotation(sense1, sense2, slot.attrib['name']))

    semagram_annotations.sort(key=lambda item: item.slot)
    pattern_list = [(key, list(group)) for key, group in
                    itertools.groupby(semagram_annotations, key=lambda item: item.slot)]

    with open('../my_whoosh/querying/pattern_list.pkl', mode='wb') as output_file:
        pickle.dump(pattern_list, output_file, protocol=pickle.HIGHEST_PROTOCOL)

    babel_dict = defaultdict()

    semagram_synsets_set = list(semagram_synsets_set)
    for synset in semagram_synsets_set:
        babel_dict[synset] = get_lemmas_from_babelsynset(synset, key=key, ret='LEMMA')

    filler_synsets_set = list(filler_synsets_set)
    for synset in filler_synsets_set:
        if synset not in babel_dict:
            babel_dict[synset] = get_lemmas_from_babelsynset(synset, key=key, ret='LEMMA')

    with open(Path(dirname(dirname(__file__))) / 'indices_extraction' / 'babel_dict.pkl',
              mode='wb') as output_file:
        pickle.dump(babel_dict, output_file, protocol=pickle.HIGHEST_PROTOCOL)


def make_bn_to_wn_dict():
    """
    From semagram_base.xml:
        - concept without WordNet Synset = 109 (100%)

    After many calls to BabelNet, we got:
        - concept without WordNet Synset = 65 (~59%)
        - concept with WordNet Synset = 44: (~41%) oppure (100%)
            - new Synsets = 27 (~25%) oppure (~61%)
            - already in = 17  (~16%) oppure (~39%)

    """
    with open(SEMAGRAM_PATH, mode='r') as semagram_base:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, xml_parser).getroot()

    no_wn_synset = set()
    bn_to_wn_dict = defaultdict(list)
    for semagram in xml_root:
        for s in semagram.get('babelsynset').split(','):
            if s:
                if not semagram.get('synset'):
                    no_wn_synset.add(s)
                else:
                    if s not in bn_to_wn_dict:
                        bn_to_wn_dict[s].append(semagram.get('synset'))

                for slot in list(semagram):
                    for value in list(slot):

                        value_syn = value.get('babelsynset')
                        if value_syn:
                            value_wn = value.get('wnSynset')
                            if not value_wn:
                                no_wn_synset.add(value_syn)
                            else:
                                splitted_value_syn = value_syn.split(',')
                                splitted_value_wn = value_wn.split(',')

                                if len(splitted_value_syn) == len(splitted_value_wn):
                                    for f, b in zip(splitted_value_syn, splitted_value_wn):
                                        if f not in bn_to_wn_dict:
                                            bn_to_wn_dict[f].append(b)
                                else:
                                    for f in splitted_value_syn:
                                        if f not in bn_to_wn_dict:
                                            for b in splitted_value_wn:
                                                bn_to_wn_dict[f].append(b)

    with open('disambiguate_sentences.txt', mode='r', encoding='utf-8') as ds_file:
        for line in ds_file:
            if line.strip():
                no_wn_synset.add(line.split('\n')[0].split('@')[1])

    for syn in no_wn_synset:
        set_offset = get_lemmas_from_babelsynset(syn, key='34461ea6-4c3a-411f-9531-d9e3cae24954', ret='OFF')
        if set_offset:
            syn_offset = next(iter(set_offset))
            wn_syn = wordnet.synset_from_pos_and_offset(syn_offset[-1], int(syn_offset[:-1]))
            if syn not in bn_to_wn_dict:
                bn_to_wn_dict[syn].append(wn_syn.name())
                print(f'WN_SYN {wn_syn} found for {syn}')
            else:
                print(f'{syn} already inside!')
        else:
            print(f'No WN_SYN found for {syn}')

    with open(Path(dirname(dirname(__file__))) / 'patterns' / 'bn_to_wn_dict.pkl', mode='wb') as output_file:
        pickle.dump(bn_to_wn_dict, output_file, protocol=pickle.HIGHEST_PROTOCOL)

print(get_lemmas_from_babelsynset('bn:00116917r', key='d98e5389-2438-4db4-8672-fcdd4ce6d4f9', ret='LEMMA'))