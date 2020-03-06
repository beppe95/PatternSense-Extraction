import os
from _collections import defaultdict
from os.path import dirname
from pathlib import Path

from lxml import etree
from whoosh import index
from whoosh.fields import Schema, TEXT

DATASET_PATH = Path(dirname(dirname(__file__))) / 'sew_subset'
DATASET_DIM = 101
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


'''def parse_sew(_writer):
    for subdir in [f.path for f in os.scandir(DATASET_PATH) if f.is_dir()]:
        print('Processing directory:', subdir)
        for xml_file in [f.path for f in os.scandir(subdir) if f.is_file()]:
            parse_xml_file(xml_file, _writer)
        print('Ending processing directory:', subdir)'''


def parse_xml_file(filename):
    with open(filename, mode='r') as semagram_base:
        magical_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(semagram_base, magical_parser).getroot()

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


'''if __name__ == '__main__':
    if not os.path.exists('sew_index'):
        os.mkdir('sew_index')
        ix = index.create_in("sew_index", schema)

    ix = index.open_dir('sew_index')

    num_dir, checkpoint = 0, 10
    while num_dir < DATASET_DIM:
        writer = ix.writer(procs=os.cpu_count(), limitmb=1024, multisegment=True, batchsize=512)
        if num_dir % 10 == 0:
            writer.commit()

    # parse_semagram_base()'''
