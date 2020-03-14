import os.path
from os.path import dirname
from pathlib import Path

from lxml import etree
from whoosh import index
from whoosh.qparser import QueryParser

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
        out.write(etree.tostring(extraction, pretty_print=True))

    '''with open('test.xml', mode='rb') as inp:
        xml_parser = etree.XMLParser(encoding='utf-8', recover=True)
        xml_root = etree.parse(inp, xml_parser).getroot()

    print(xml_root.tag)'''


if __name__ == '__main__':
    if os.path.exists(dir_path):
        exists = index.exists_in(dir_path)
        ix = index.open_dir(dir_path)

        with ix.searcher() as searcher:
            query = QueryParser('annotations', ix.schema).parse('bn:00043021n bn:00046965n')
            results = searcher.search(query, limit=None)

            make_xml(results)
            '''print(len(results))
            print(*results)'''

            '''query = MultifieldParser(['annotations', 'free_text'], ix.schema).parse('bn:00043021n black')
            results = searcher.search(query, limit=None)
            print(len(results))'''
