from _collections import defaultdict
from os.path import dirname
from pathlib import Path

from lxml import etree

SEMAGRAM_PATH = Path(dirname(dirname(__file__))) / 'semagram_base.xml'


def parse_semagram_base() -> defaultdict:
    """
    Handle 'semagram_base' XML file and generate to respective dictionary which contains:
        - key
        - value

    :return: dictionary which contains the information inside the given file.
    """
    with open(SEMAGRAM_PATH, mode='r') as semagram_base:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, xml_parser).getroot()

    # s_dict = defaultdict(list)

    # check_multiple_semagram_annotations(xml_root)

    for semagram in xml_root:
        for slot in list(semagram):
            for value in list(slot):
                print((semagram.attrib['babelsynset'], semagram.attrib['name']),
                      (value.attrib['babelsynset'], value.text),
                      slot.attrib['name'])
                '''for v in [s.split('#') for s in value.text.split(',')]:
                    if len(v) == 1:
                        v.append('')

                print((semagram.attrib['babelsynset'], semagram.attrib['name']),
                      (value.attrib['babelsynset'], v[0]),
                      slot.attrib['name'])'''

    '''
      for v in [s.split('#') for s in value.text.split(',')]:
        if len(v) == 1:
            v.append('')
        s_dict[semagram.attrib['name']].append((slot.attrib['name'], v[0], v[1]))

    '''


def parse_xml_file(filename):
    """

    :param filename:
    :return:
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
