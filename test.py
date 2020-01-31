from _collections import defaultdict
from xml.etree import ElementTree


def handle_xml_file(filename: str) -> defaultdict:
    """
    Handle 'semagram_base' XML file and generate to respective dictionary which contains:
        - key
        - value

    :param filename: name of file to be parsed.
    :return: dictionary which contains the information inside the given file.
    """
    xml_root = ElementTree.parse(filename).getroot()

    s_dict = defaultdict(list)
    for semagram in xml_root:
        for slot in list(semagram):
            for value in list(slot):
                for v in [s.split('#') for s in value.text.split(',')]:
                    if len(v) == 1:
                        v.append('')
                    s_dict[semagram.attrib['name']].append((slot.attrib['name'], v[0], v[1]))

    return s_dict


if __name__ == '__main__':
    semagram_dict = handle_xml_file('semagram_base.xml')
