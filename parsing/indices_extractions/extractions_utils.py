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

file = 'group'
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
            sentence = hit[1].text.lower()

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
                if not matches:
                    failed_match += 1

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

    if stats:
        stats_dump = f'SLOT: {file}\n{50 * "-"}\n' \
                     f'TOTAL HITS: {total_hits}\n1ST_MATCH: {first_match}, NO_MATCH: {no_match}\n' \
                     f'2ND_MATCH: {first_match + (no_match - failed_match)}, FAILED_MATCH: {failed_match}\n' \
                     f'ADDED_MATCH: {(first_match + (no_match - failed_match)) - first_match}\n{50 * "-"}\n' \
                     f'TOTAL_PATTERNS: {total_pattern}\n\n\n'
        with open('stats.txt', mode='a', encoding='utf-8') as stats_file:
            stats_file.write(stats_dump)

    with open(dir_patterns_path / f'{file}_patterns.xml', mode='wb') as pattern_file:
        pattern_file.write(etree.tostring(pattern_root, xml_declaration=True, encoding='utf-8', pretty_print=True))


def extract():
    with open('annotations_dict.pkl', mode='rb') as test_dict:
        di = pickle.load(test_dict)

    with open(SLOT_PATH, mode='rb') as slot_file:
        xml_parser = etree.XMLParser(encoding='utf-8')
        extraction = etree.parse(slot_file, xml_parser).getroot()

    for hits in extraction:

        concept_name, concept_id = hits.get("name_1").lower(), hits.get("babelsynset_1")
        filler_name, filler_id = hits.get('name_2').lower(), hits.get('babelsynset_2')

        for hit in hits:
            if hit.get('got_by') == 'b_syn':
                annotations = ' '.join(hit[0].text.split())
                sentence = ' '.join(hit[1].text.lower().split())
                print(sentence, '\n')

                annotated_sentence = get_ann(concept_name, filler_name, annotations, sentence, di)
                c = filter(lambda elem: elem[0] == concept_id,
                           annotated_sentence)
                f = filter(lambda elem: elem[0] == filler_id,
                           annotated_sentence)

                for a in iter(c):
                    print(a)
                for a in iter(f):
                    print(a)
                print('\n')
                # break
            else:
                annotations = ' '.join(hit[0].text.split())
                sentence = ' '.join(hit[1].text.lower().split())
                print(sentence, '\n')

                annotated_sentence = get_ann(concept_name, filler_name, annotations, sentence, di)
                c = filter(lambda elem: elem[0] == concept_id,
                           annotated_sentence)
                # generator sempre vuoto, non ci sarà mai un annotation con il synset del filler considerato (POS-TAG?)
                f = filter(lambda elem: elem[0] == filler_id,
                           annotated_sentence)

                for a in iter(c):
                    print(a)
                for a in iter(f):
                    print(a)
                print('\n')
                break
        break


def get_ann(name_1, name_2, annotations, sentence, di):
    word_ann = []
    readed_word = 0
    for ann in annotations.split():
        # print(sentence[readed_word:])
        # print(readed_word)
        lemmas = di[ann]
        if name_1 in lemmas:
            lemmas = list(filter(lambda elem: len(elem) >= len(name_1), lemmas))
        elif name_2 in lemmas:
            lemmas = list(filter(lambda elem: len(elem) >= len(name_2), lemmas))
        else:
            lemmas = list(filter(lambda elem: len(elem) > 2, lemmas))
        matches = []
        for lemma in lemmas:
            m = re.finditer(lemma, sentence[readed_word:])
            if m:
                try:
                    m = next(iter(m))
                    matches.append((ann, lemma, m.start(), m.end()))
                except StopIteration:
                    pass
            else:
                pass
        # print(matches)
        if matches:
            matches = sorted(matches, key=lambda elem: elem[1])
            # print(matches)
            bsyn, matched_text, start, end = get_correct_match(matches)
            word_ann.append((bsyn, matched_text, start + readed_word, end + readed_word))
            readed_word += end + 1
        else:
            pass

    return word_ann


def get_correct_match(matches: list):
    ret = matches[0]
    for i in range(1, len(matches)):
        if ret[2] == matches[i][2] and ret[3] > matches[i][3]:
            ret = matches[i]
    return ret[0], ret[1], ret[2], ret[3]


# search = True
# i = 0
# lemmas1 = list(filter(lambda elem: len(elem) > 1, di[babelsynset_1]))
# while search and i < len(lemmas1):
#     for m in re.finditer(lemmas1[i], sentence):
#         if m:
#             print(lemmas1[i])
#             print(m.start(), m.end())
#             search = False
#     i += 1
#
# search = True
# i = 0
# lemmas2 = list(filter(lambda elem: len(elem) > 1, di[babelsynset_2]))
# while search and i < len(lemmas2):
#     for m in re.finditer(lemmas2[i], sentence):
#         if m:
#             print(lemmas2[i])
#             print(m.start(), m.end())
#             search = False
#     i += 1

# pos_tagged_sent = pos_tag(sentence.split())
# sentence = sentence.lower()
# filter_concept = list(filter(
#     lambda pos_tuple: pos_tuple[0].startswith(name_1) and pos_tuple[1].startswith(babelsynset_1[-1].upper()),
#     pos_tagged_sent))
#
# filter_filler = list(filter(
#     lambda pos_tuple: pos_tuple[0].startswith(name_2) and pos_tuple[1].startswith(babelsynset_2[-1].upper()),
#     pos_tagged_sent))
#
# if filter_concept and filter_filler:
#     splitted_sent = sentence.split()
#     for b_syn in annotations.split():
#         w_read = 0
#         for i in range(w_read, len(splitted_sent)):
#             if splitted_sent[i] in di[b_syn]:
#                 pass
#             else:
#                 pass
#             w_read += 1
#         print(w_read)
#         break
# word_sense_list = []
# # devo appiccicare i babelsynset alle parole
# for b_syn in annotations.split():
#     lemmas = list(di[b_syn])
#
#     search = True
#     i = 0
#     while search and i < len(lemmas):
#         matches = re.findall(rf'\b{lemmas[i]}\b', sentence, overlapped=True)
#         if matches:
#             search = False
#         else:
#             i += 1
#     print(matches)
#
#     break
# else:
#     pass
#     # scarto l'hit


extract()
# get_patterns(stats=False)
