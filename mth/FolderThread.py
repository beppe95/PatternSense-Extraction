import concurrent.futures
import os
from os.path import dirname
from pathlib import Path

from lxml import etree


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


class FolderThread:

    def __new__(cls, dir_num: int):

        dir_path = str(Path(dirname(dirname(__file__))) / 'sew_subset' / 'wiki') + ("%03d" % dir_num)

        file_annotations = []
        with concurrent.futures.ThreadPoolExecutor(min(32, os.cpu_count() + 4)) as executor:
            future_to_file = {executor.submit(parse_xml_file, xml_file): xml_file for xml_file in
                              [f.path for f in os.scandir(dir_path) if f.is_file()]}
            for future in concurrent.futures.as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    ann_text = future.result()
                    file_annotations.append(ann_text)
                except Exception as exc:
                    print('Generated an exception', (file, exc))
        return file_annotations
