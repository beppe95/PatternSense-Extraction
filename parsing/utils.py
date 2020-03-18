import itertools
import pickle
from os.path import dirname
from pathlib import Path

from lxml import etree

from data_structure.SemagramAnnotation import SemagramAnnotation
from data_structure.Sense import Sense

SEMAGRAM_PATH = Path(dirname(dirname(__file__))) / 'semagram_base.xml'


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


parse_semagram_base()
