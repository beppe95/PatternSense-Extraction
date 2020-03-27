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


def get_lemmas_from_babelsynset(synset: str, key: str, search_lang: str = 'EN', target_lang: str = 'EN'):
    """
    Handles REST messages exchange with BabelNet server in order to get each gloss of our babel synset ID.

    :param synset: babel synset ID of the input concept
    :param key: key used to access BabelNet REST service
    :param search_lang: search language. Default language is ENGLISH: 'EN'.
    :param target_lang: target language. Default language is ENGLISH: 'EN'.

    :return:
    """

    # key = 'd98e5389-2438-4db4-8672-fcdd4ce6d4f9'    # key1
    # key2 = '34461ea6-4c3a-411f-9531-d9e3cae24954'   # key2
    # key3 = '8e149252-ac13-4e51-96ba-e7055f6d56e2'   # key3

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

    return set([' '.join(lemmatizer.lemmatize(sense['properties']['simpleLemma'].lower()).split('_'))
                for sense in results['senses']]) if 'message' not in results else set()


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
        babel_dict[synset] = get_lemmas_from_babelsynset(synset, key=key)

    filler_synsets_set = list(filler_synsets_set)
    for synset in filler_synsets_set:
        if synset not in babel_dict:
            babel_dict[synset] = get_lemmas_from_babelsynset(synset, key=key)

            with open(Path(dirname(dirname(__file__))) / 'indices_extraction' / 'babel_dict.pkl',
                      mode='wb') as output_file:
                pickle.dump(babel_dict, output_file, protocol=pickle.HIGHEST_PROTOCOL)