import itertools
import pickle
import string
from os.path import dirname
from pathlib import Path

import regex as re
from lxml import etree
from nltk import WordNetLemmatizer

from data_structure.SemagramAnnotation import SemagramAnnotation
from data_structure.Sense import Sense

file = 'activity'
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
<pattern direction="&lt;L_&gt;">boat that could only be used in large</pattern>
Possiamo notare che large è relativo a cosa c’è dopo, e non a boat. Per “scartare” questi casi, 
potremmo usare delle windows (that could only be used in -> sono 6 token), o meccanismi più “clever”
"""


def get_patterns():
    with open(SLOT_PATH, mode='rb') as slot_file:
        xml_parser = etree.XMLParser(encoding='utf-8')
        extraction = etree.parse(slot_file, xml_parser).getroot()

    pattern_root = etree.Element("patterns", slot=file)

    window = 8
    patterns_list = []
    for hits in extraction:
        concept_name, concept_id = hits.attrib["name_1"], hits.attrib["babelsynset_1"]
        filler_name, filler_id = hits.attrib['name_2'], hits.attrib['babelsynset_2']
        for hit in hits:
            sentence = clean_sentence(hit[1].text)
            matches = re.findall(rf'\b{concept_name}\b.*?\b{filler_name}\b'
                                 rf'|\b{filler_name}\b.*?\b{concept_name}\b',
                                 sentence, overlapped=True)
            if not matches:
                pass
                # print(f'Concept:{concept_name}, Filler:{filler_name} \nSentence:{sentence}\n')
            else:
                for match in matches:
                    splitted_match = match.split()
                    if len(splitted_match) < window:
                        index_first_marker = splitted_match.index(concept_name)
                        index_second_marker = splitted_match.index(filler_name)

                        if (index_first_marker + 1 == index_second_marker) or (
                                index_second_marker + 1 == index_first_marker):
                            direction = '*'
                        elif index_first_marker < index_second_marker:
                            direction = 'L_'
                        elif index_first_marker > index_second_marker:
                            direction = 'R_'
                        else:
                            direction = 'N/A'

                        pattern_text = ' '.join(
                            filter(lambda word: word != splitted_match[index_first_marker] and word != splitted_match[
                                index_second_marker], splitted_match))

                        patterns_list.append(
                            (direction, concept_name, filler_name, concept_id, filler_id, pattern_text))

    patterns_list = list(set(patterns_list))

    patterns_list = sorted(patterns_list, key=lambda item: (
        item[1], item[2], item[3], item[4]))

    grouped_patterns_list = [(key, list(group)) for key, group in
                             itertools.groupby(patterns_list, key=lambda item: (
                                 item[1], item[2], item[3], item[4]))]

    for group in grouped_patterns_list:
        markers = etree.SubElement(pattern_root, "markers", concept=group[0][0], filler=group[0][1],
                                   concept_babelsynset=group[0][2], filler_babelsynset=group[0][3])

        for pattern in group[1]:
            marker_child = etree.SubElement(markers, "pattern", direction=pattern[0])
            marker_child.text = pattern[5]

        markers[:] = sorted(markers, key=lambda child_pattern: child_pattern.get('direction'))

    with open(f'{file}_patterns.xml', mode='wb') as pattern_file:
        pattern_file.write(
            etree.tostring(pattern_root, xml_declaration=True, encoding='utf-8', pretty_print=True))


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
