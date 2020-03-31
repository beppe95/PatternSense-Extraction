import itertools
import os
import pickle
import string
from collections import defaultdict
from os.path import dirname
from pathlib import Path

import regex as re
from lxml import etree
from nltk import WordNetLemmatizer

file = 'time'
SLOT_PATH = Path(dirname(dirname(__file__))) / 'indices_extractions' / 'xml_slots' / Path(f'{file}.xml')

translator = str.maketrans('', '', string.punctuation)
lemmatizer = WordNetLemmatizer()


def clean_sentence(sentence: str):
    cleaned_sentence = sentence.translate(translator).lower()
    cleaned_sentence = [lemmatizer.lemmatize(word) for word in cleaned_sentence.split()]
    return ' '.join(cleaned_sentence)


def get_patterns(stats: bool = True):
    dir_patterns_path = Path(dirname(dirname(__file__))) / 'patterns' / 'data'
    if not os.path.exists(dir_patterns_path):
        os.mkdir(dir_patterns_path)

    with open('babel_dict.pkl', mode='rb') as babel_file:
        babel_dict = pickle.load(babel_file)

    with open(SLOT_PATH, mode='rb') as slot_file:
        xml_parser = etree.XMLParser(encoding='utf-8')
        extraction = etree.parse(slot_file, xml_parser).getroot()

    pattern_root = etree.Element("patterns", slot=file)

    first_match, total_hits, total_pattern, no_match, failed_match = 0, 0, 0, 0, 0
    window = 8
    match_list = []
    for hits in extraction:

        concept_name, concept_id = hits.get("name_1").lower(), hits.get("babelsynset_1")
        filler_name, filler_id = hits.get('name_2').lower(), hits.get('babelsynset_2')

        for hit in hits:
            total_hits += 1
            sentence = clean_sentence(hit[1].text)
            matches = re.findall(rf'\b{concept_name}\b.*?\b{filler_name}\b'
                                 rf'|\b{filler_name}\b.*?\b{concept_name}\b',
                                 sentence, overlapped=True)
            if matches:
                first_match += 1
            else:
                no_match += 1
                splitted_sentence = sentence.split()
                set_sentence = set(splitted_sentence)

                try:
                    splitted_sentence.index(concept_name)
                except ValueError:
                    try:
                        concept_synsets = babel_dict[concept_id]

                        intersect_concept_lemmas = concept_synsets.intersection(set_sentence)
                        if intersect_concept_lemmas:
                            concept_name = next(iter(intersect_concept_lemmas))
                    except KeyError:
                        print(f'No synonyms found for {concept_name}')
                        pass
                try:
                    splitted_sentence.index(filler_name)
                except ValueError:
                    try:
                        filler_synsets = babel_dict[filler_id]

                        intersect_filler_lemmas = filler_synsets.intersection(set_sentence)
                        if intersect_filler_lemmas:
                            filler_name = next(iter(intersect_filler_lemmas))
                    except KeyError:
                        print(f'No synonyms found for {filler_name}')
                        pass
                matches = re.findall(rf'\b{concept_name}\b.*?\b{filler_name}\b'
                                     rf'|\b{filler_name}\b.*?\b{concept_name}\b',
                                     sentence, overlapped=True)
                if not matches: failed_match += 1
            for m in matches:
                match_list.append((concept_name, filler_name, concept_id, filler_id, m))

    total_pattern = len(match_list)

    patterns_list = []
    for match in match_list:
        splitted_match = match[4].split()
        if len(splitted_match) < window:
            # print(splitted_match)
            index_first_marker = splitted_match.index(match[0])
            index_second_marker = splitted_match.index(match[1])

            if (index_first_marker + 1 == index_second_marker) or (
                    index_second_marker + 1 == index_first_marker):
                direction = '*'
            elif index_first_marker < index_second_marker:
                direction = 'L_'
            elif index_first_marker > index_second_marker:
                direction = 'R_'
            else:
                direction = 'L_R'

            pattern_text = ' '.join(
                filter(lambda word: word != splitted_match[index_first_marker] and word != splitted_match[
                    index_second_marker], splitted_match))

            patterns_list.append((direction, match[0], match[1], match[2], match[3], pattern_text))

    patterns_list = list(set(patterns_list))
    patterns_list = sorted(patterns_list, key=lambda item: (item[1], item[2], item[3], item[4]))
    effective_patterns = len(patterns_list)

    grouped_patterns_list = defaultdict(lambda: defaultdict(list))
    for key, group in itertools.groupby(patterns_list, key=lambda item: (item[3], item[4])):
        for key_2, inner_group in itertools.groupby(list(group), key=lambda elem: (elem[1], elem[2])):
            grouped_patterns_list[key][key_2] = list(inner_group)

    for bsyn_group in grouped_patterns_list:
        ids = etree.SubElement(pattern_root, 'ids',
                               concept_babelsynset=bsyn_group[0], filler_babelsynset=bsyn_group[1])

        for text_group in grouped_patterns_list[bsyn_group]:
            markers = etree.SubElement(ids, 'markers',
                                       concept_name=text_group[0], filler_name=text_group[1])

            for pattern in grouped_patterns_list[bsyn_group][text_group]:
                marker_child = etree.SubElement(markers, "pattern", direction=pattern[0])
                marker_child.text = pattern[5]

            markers[:] = sorted(markers, key=lambda child_pattern: child_pattern.get('direction'))

    stats_dump = f'SLOT: {file}\n{50 * "-"}\n' \
        f'TOTAL HITS: {total_hits}\n1ST_MATCH: {first_match}, NO_MATCH: {no_match}\n' \
        f'2ND_MATCH: {first_match + (no_match - failed_match)}, FAILED_MATCH: {failed_match}\n' \
        f'ADDED_MATCH: {(first_match + (no_match - failed_match)) - first_match}\n{50 * "-"}\n' \
        f'TOTAL_PATTERNS: {total_pattern}, EFFECTIVE_PATTERNS: {effective_patterns}\n\n'

    if stats:
        with open('stats.txt', mode='a', encoding='utf-8') as stats_file:
            stats_file.write(stats_dump)
    with open(dir_patterns_path / f'{file}_patterns.xml', mode='wb') as pattern_file:
        pattern_file.write(etree.tostring(pattern_root, xml_declaration=True, encoding='utf-8', pretty_print=True))


get_patterns()
