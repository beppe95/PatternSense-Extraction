import os.path
from os.path import dirname
from pathlib import Path

from lxml import etree

dir_path = Path(dirname(dirname(__file__))) / 'indices' / 'index_0'

extraction = etree.Element("extraction")


def make_xml(result_set):
    hits = etree.SubElement(extraction, "hits", babelsynset_1="bn:00043021n", name_1="harmonica",
                            babelsynset_2="bn:00046965n", name_2="musical_instrument,instrument")

    for item in result_set:
        hit = etree.SubElement(hits, "hit", score=str(item.score))

        annotations = etree.SubElement(hit, "annotations")
        sentence = etree.SubElement(hit, "sentence")

        annotations.text = item['annotations']
        sentence.text = item['free_text']

    with open('test.xml', mode='wb') as out:
        out.write(etree.tostring(extraction, xml_declaration=True, pretty_print=True))

    '''with open('test.xml', mode='rb') as inp:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(inp, xml_parser).getroot()

    print(xml_root.tag)'''


def new_xml():
    if not os.path.exists('test.xml'):
        Path('test.xml').touch()

    root = etree.Element("root")
    with open('test.xml', mode='wb') as out:
        out.write(etree.tostring(root, xml_declaration=True, encoding='utf-8', pretty_print=True))


def append_xml():
    with open('test.xml', mode='rb') as input_file:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        tree = etree.parse(input_file, xml_parser)
        xml_root = tree.getroot()

    e2 = etree.Element("e2")
    xml_root.append(e2)

    tree.write('test.xml')


if __name__ == '__main__':
    new_xml()
    #append_xml()
