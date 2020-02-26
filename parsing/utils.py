import os
from _collections import defaultdict
from os.path import dirname
from pathlib import Path

from lxml import etree
from whoosh import index
from whoosh.fields import Schema, TEXT

DATASET_PATH = Path(dirname(dirname(__file__))) / 'sew_subset'
SEMAGRAM_PATH = Path(dirname(dirname(__file__))) / 'semagram_base.xml'

schema = Schema(annotations=TEXT(stored=True),
                free_text=TEXT(stored=True))


def parse_semagram_base() -> defaultdict:
    """
    Handle 'semagram_base' XML file and generate to respective dictionary which contains:
        - key
        - value

    :return: dictionary which contains the information inside the given file.
    """

    with open(SEMAGRAM_PATH, mode='r') as semagram_base:
        magical_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, magical_parser).getroot()

    s_dict = defaultdict(list)
    for semagram in xml_root:
        for slot in list(semagram):
            for value in list(slot):
                # remember to add elem to dict!
                print((semagram.attrib['babelsynset'], semagram.attrib['name']),
                      (value.attrib['babelsynset'], value.text),
                      slot.attrib['name'])
    return s_dict


def parse_sew(_writer):
    for subdir in [f.path for f in os.scandir(DATASET_PATH) if f.is_dir()]:
        print('Processing directory:', subdir)
        for xml_file in [f.path for f in os.scandir(subdir) if f.is_file()]:
            parse_xml_file(xml_file, _writer)
        print('Ending processing directory:', subdir)


def parse_xml_file(filename: str, _writer):
    with open(filename, mode='r') as xml_file:
        magical_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(xml_file, magical_parser).getroot()

    free_text, annotations = xml_root[0].text, xml_root[1]
    tok_free_text = free_text.split('\n')

    start, end, i = 0, 0, 0
    for sent in tok_free_text:
        token = sent.split()
        end = start + len(token) - 1

        babel_id = []
        while i <= (len(annotations) - 1) and int(annotations[i][3].text) <= end:
            babel_id.append(annotations[i][0].text)
            i += 1

        _writer.add_document(annotations=' '.join(babel_id),
                             free_text=sent)
        start += len(token) + 1


if __name__ == '__main__':
    if not os.path.exists('sew_index'):
        os.mkdir('sew_index')

    ix = index.create_in("sew_index", schema)
    ix = index.open_dir('sew_index')

    with ix.writer(procs=4, limitmb=256, multisegment=True) as writer:
        parse_sew(writer)
    # parse_semagram_base()
