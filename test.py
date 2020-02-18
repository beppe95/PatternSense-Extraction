import os
import re
from _collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree

from nltk import sent_tokenize


def parse_semagram_base() -> defaultdict:
    """
    Handle 'semagram_base' XML file and generate to respective dictionary which contains:
        - key
        - value

    :return: dictionary which contains the information inside the given file.
    """
    xml_root = ElementTree.parse(Path.cwd() / 'semagram_base.xml').getroot()

    s_dict = defaultdict(list)
    for semagram in xml_root:
        for slot in list(semagram):
            for value in list(slot):
                for v in [s.split('#') for s in value.text.split(',')]:
                    if len(v) == 1:
                        v.append('')
                    s_dict[semagram.attrib['babelsynset']].append((slot.attrib['name'], v[0], v[1]))

    return s_dict


def parse_sew():
    for subdir in [f.path for f in os.scandir(Path(Path.cwd() / 'sew_subset')) if f.is_dir()]:
        for xml_file in [f.path for f in os.scandir(subdir) if f.is_file()]:
            parse_xml_file(xml_file)
            break
        break


def parse_xml_file(filename: str):
    xml_root = ElementTree.parse(filename).getroot()

    free_text, annotations = xml_root[0], xml_root[1]
    tok_free_text = sent_tokenize(free_text.text)

    t = tok_free_text[:2]

    num_tok_read, limit, i = -1, 0, 0
    for sent in t:
        token = re.findall(r'\w+', sent)
        while num_tok_read < len(token):
            num_tok_read = limit
            print(annotations[i][2].text, annotations[i][3].text)
            # do something with annotation
            num_tok_read += int(annotations[i][3].text)
            i += 1


if __name__ == '__main__':
    parse_sew()
