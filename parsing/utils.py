import itertools
import pickle
import string
import regex as re
from os.path import dirname
from pathlib import Path

from lxml import etree
from nltk import WordNetLemmatizer

from data_structure.SemagramAnnotation import SemagramAnnotation
from data_structure.Sense import Sense

file = 'movement'
SEMAGRAM_PATH = Path(dirname(dirname(__file__))) / 'semagram_base.xml'
SLOT_PATH = Path(dirname(dirname(__file__))) / 'my_whoosh' / 'xml_slots' / Path(f'{file}.xml')
translator = str.maketrans('', '', string.punctuation)
lemmatizer = WordNetLemmatizer()


def parse_semagram_base():
    """
    Handle 'semagram_base' XML file and generate to respective dictionary which contains:
        - key
        - value

    """
    with open(SEMAGRAM_PATH, mode='r') as semagram_base:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, xml_parser).getroot()

    semagram_annotations = []
    for semagram in xml_root:
        for s in semagram.attrib['babelsynset'].split(','):
            for slot in list(semagram):
                for value in list(slot):
                    for v in value.attrib['babelsynset'].split(','):
                        for t in value.text.split(','):
                            sense1 = Sense(semagram.attrib['name'], s)
                            sense2 = Sense(t.split('#')[0], v)
                            semagram_annotations.append(SemagramAnnotation(sense1, sense2, slot.attrib['name']))

    semagram_annotations.sort(key=lambda item: item.slot)

    pattern_list = [(key, list(group)) for key, group in
                    itertools.groupby(semagram_annotations, key=lambda item: item.slot)]

    with open('../my_whoosh/querying/pattern_list.pkl', mode='wb') as output_file:
        pickle.dump(pattern_list, output_file, protocol=pickle.HIGHEST_PROTOCOL)


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


def clean_sentence(sentence: str):
    cleaned_sentence = sentence.translate(translator).lower()
    cleaned_sentence = [lemmatizer.lemmatize(word) for word in cleaned_sentence.split()]
    return ' '.join(cleaned_sentence)


"""
Stavo notando che nei pattern non c’è più l’indicazione del concept e del filler. 
Nel senso che sono all’interno del pattern. 

Ad esempio: <pattern direction="L_">fruit is a small</pattern>

Magari potresti usare: <pattern direction="L_” c=“fruit”; f=“small">is a</pattern>

Anche se cos facendo perdiamo anche l’info del synset di c e di f (se li abbiamo, potrebbero sempre servirci).

Altra nota. Consideriamo questo caso:

<pattern direction="&lt;L_&gt;">boat that could only be used in large</pattern>

Possiamo notare che large è relativo a cosa c’è dopo, e non a boat. Per “scartare” questi casi, 
potremmo usare delle windows (that could only be used in -> sono 6 token), o meccanismi più “clever”
"""


def get_patterns():
    with open(SLOT_PATH, mode='rb') as slot_file:
        xml_parser = etree.XMLParser(encoding='utf-8')
        extraction = etree.parse(slot_file, xml_parser).getroot()

    patterns_root = etree.Element("patterns", slot=file)

    patterns_list = []
    for hits in extraction:
        for hit in hits:
            sentence = clean_sentence(hit[1].text)
            matches = re.findall(rf'\b{hits.attrib["name_1"]}\b.*?\b{hits.attrib["name_2"]}\b'
                                 rf'|\b{hits.attrib["name_2"]}\b.*?\b{hits.attrib["name_1"]}\b',
                                 sentence, overlapped=True)

            if not matches:
                print(hits.attrib["name_1"], hits.attrib["name_2"], sentence)
                print('\n')
            else:
                for match in matches:
                    splitted_match = match.split()
                    # ridurre la window?
                    if len(splitted_match) <= 8:
                        index_first_marker = splitted_match.index(hits.attrib["name_1"])
                        index_second_marker = splitted_match.index(hits.attrib["name_2"])

                        # make class Pattern
                        flag = ''
                        if index_first_marker < index_second_marker:
                            flag = 'L_'
                        elif index_first_marker > index_second_marker:
                            flag = 'R_'
                        elif index_first_marker + 1 == index_second_marker:
                            flag = '*'
                        else:
                            flag = 'N/A'

                        patterns_list.append((match, flag))

    for p in set(patterns_list):
        root_child = etree.SubElement(patterns_root, "pattern", direction=p[1])
        root_child.text = p[0]
        patterns_root.append(root_child)

    with open(f'{file}_patterns.xml', mode='wb') as pattern_file:
        pattern_file.write(etree.tostring(patterns_root, xml_declaration=True, encoding='utf-8', pretty_print=True))


def get_lemmas_from_babelsynset(synset: str, key: str, search_lang: str = 'EN', target_lang: str = 'EN'):
    """
    Handles REST messages exchange with BabelNet server in order to get each gloss of our babel synset ID.
    :param synset: babel synset ID of the input concept
    :param key: key used to access BabelNet REST service
    :param search_lang:
    :param target_lang:
    :return:
    """
    # key = 'd98e5389-2438-4db4-8672-fcdd4ce6d4f9'    # key1
    # key2 = '34461ea6-4c3a-411f-9531-d9e3cae24954'   # key2

    import urllib
    import urllib3
    import json

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

    for sense in results['senses']:
        print(sense['properties']['fullLemma'], sense['properties']['fullLemma'])


def get_babelsynsets_from_lemmas(lemma: str, key: str, search_lang: str = 'EN', target_lang: str = 'EN'):
    """
    Handles REST messages exchange with BabelNet server in order to get each gloss of our babel synset ID.
    :param lemma:
    :param key: key used to access BabelNet REST service
    :param target_lang:
    :param search_lang:
    :return:
    """
    # key = 'd98e5389-2438-4db4-8672-fcdd4ce6d4f9'    # key1
    # key2 = '34461ea6-4c3a-411f-9531-d9e3cae24954'   # key2

    import urllib
    import urllib3
    import json

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
        print(sense)  # check se nel lemma ci sta quello che cerco, altrimenti cazzi.


get_patterns()
# get_lemmas_from_babelsynset('bn:00018038n', key='d98e5389-2438-4db4-8672-fcdd4ce6d4f9')
# get_babelsynsets_from_lemmas('aircraft', key='d98e5389-2438-4db4-8672-fcdd4ce6d4f9')
