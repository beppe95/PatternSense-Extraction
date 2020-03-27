import concurrent.futures
import logging
import os
from os.path import dirname
from pathlib import Path

from parsing.semagram_base.semagram_utils import parse_xml_file

logging.basicConfig(level=logging.INFO)


class FolderProcess:

    def __new__(cls, dir_num: int, verbose: bool):
        if verbose:
            logging.info(f'Parsing directory {dir_num} ...')

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
