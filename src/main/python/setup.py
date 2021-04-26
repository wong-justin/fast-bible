'''Setup (one-time) to prepare data for gui.'''

import constants

# import sys
# sys.path.insert(0, '../env/Lib/site-packages')
from striprtf.striprtf import rtf_to_text
import requests

import glob
import re
import json
from io import BytesIO
from zipfile import ZipFile
# from time import sleep

# LOCAL_RTF_FILEPATHS = {
#     book_name: {'old': fp_old, 'new': fp_new}
#     for book_name, fp_old, fp_new
#     in zip(constants.BOOK_NAMES,
#            glob.glob('../data/nwt_E.rtf/nwt_[0-9][0-9]_*'),
#            glob.glob('../data/nwt_E_new.rtf/nwt_[0-9][0-9]_*'),)
# }
CHAPTER_PATTERN = re.compile(r'\n(?:Chapter|Psalm) ([0-9]+)\n(?=1)') # probably best
VERSE_PATTERN = re.compile(r'([0-9]+)\xa0')
# CHAPTERLESS_PATTERN = re.compile(r'\n\n(?=1\xa0)') # for Jude and such
CHAPTERLESS_PATTERN = re.compile(r'\n(?=1\xa0)') # for Jude and such
BIBLE_URL = 'https://download-a.akamaihd.net/files/media_publication/57/nwt_E.rtf.zip'

# def test():
#
#     book = 'Obadiah'
#     def book_versions(book_name):
#         fp_old, fp_new = LOCAL_RTF_FILEPATHS[book].values()
#         return read_rtf_to_text(fp_old), read_rtf_to_text(fp_new)
#
#     from difflib import ndiff, context_diff
#
#     print(*[i for i in context_diff(old, new)])
#
#
#     # for li in ndiff(old, new):
#     #     if not li.startswith(' '):
#     #         print(li)
#     old, new = book_versions(book)
#
#     def text_for(book_name):
#
#         fp = LOCAL_RTF_FILEPATHS[book_name]['new']
#         return read_rtf_to_text(fp)


def main():
    bible_zip = fetch_content()
    parse_and_write(iter_books(bible_zip))

def main_progress_iterator():
    bible_zip = fetch_content()
    for name, plaintext in zip(constants.BOOK_NAMES,
                               iter_books(bible_zip)):
        fp = constants.BOOK_FP_TEMPLATE.format(name)
        save_as_json(parse_book(plaintext), fp)
        yield name

    # for name in constants.BOOK_NAMES:
    #     # sleep(1)
    #     for i in range(1000000):
    #         i += 1
    #     yield name

def fetch_content():
    '''Returns zip download from JW url.'''
    response = requests.get(BIBLE_URL)
    filelike = BytesIO(response.content)
    return ZipFile(filelike)

def parse_and_write(books):
    '''Write each book's parsed content to file.'''
    for name, plaintext in zip(constants.BOOK_NAMES, books):
        fp = constants.BOOK_FP_TEMPLATE.format(name)

        print(name)

        save_as_json(parse_book(plaintext), fp)

def iter_books(zip):
    '''Returns iterator of book files as strings.'''
    # remove foreword, appendixes, etc
    fps = [f.filename for f in zip.filelist
           if re.match(r'nwt_[\d]{2}_[\w]+_E.rtf', f.filename)]
    for fp in sorted(fps):  # could be in any order
        book_rtf_bytes = zip.read(fp)
        book_rtf_str = book_rtf_bytes.decode('utf-8')
        yield rtf_to_text(book_rtf_str)

def parse_book(book_text):
    '''Strips extraneous text from .RTF book content, namely the summary.
    Returns dict, structured as...
        Chapters:
        {1: {1: '..', 2: '..', ..}, 2: ..}
        or Chapterless:
        {1: '..', 2: '', ..}
    '''

    if has_chapters(book_text):
        # skip summary
        lines = iter(book_text.split('\n'))

        # print( text.split('\n')[0] )

        # dispose summary
        last_chapter = 0
        while True:
            line = next(lines)
            match = re.search('(?:Chapter|Psalm)? ?([0-9]+)', line)
            if match:
                chapter_num = int( match.group(1) )
                if chapter_num > last_chapter:
                    last_chapter = chapter_num
                else:
                    lines = (line, *lines) # add this chapter 1 line back for parsing
                    break

        # print(last_chapter)
        # print(len(lines))
        # print(lines[:2])

        # only use the important text
        book_text = '\n'.join(lines)
        chapters = dict()
        # nums_and_chapters = re.split(CHAPTER_PATTERN, book_text)#[1:] # skip summary
        nums_and_chapters = re.split('(?:Chapter|Psalm) ([0-9]+)', book_text)[1:] # skip first empty string

        for num, chapter in every2(nums_and_chapters):
            # print(num)
            # print(chapter)
            # break
            chapters[num] = parse_verses(chapter)
        return chapters
    else:
        _, chapter_text = re.split(CHAPTERLESS_PATTERN, book_text) # skip summary by splitting on gap
        return parse_verses(chapter_text)

def parse_verses(chapter_text):
    verses = dict()
    nums_and_verses = re.split(VERSE_PATTERN, chapter_text)[1:] # empty str at beginning of split
    for num, verse in every2(nums_and_verses):
        verses[num] = verse.strip()
    return verses

def has_chapters(book_text):
    return re.search(CHAPTER_PATTERN, book_text) is not None
    # return re.search(r'(?:Chapter|Psalm) ([0-9]+)', book_text) is not None

def read_rtf_to_text(fp):
    with open(fp, 'r', encoding='utf-8') as file:
        return rtf_to_text(file.read())

def save_as_json(content, fp):
    with open(fp, 'w') as file:
        json.dump(content, file)

def every2(alternating_list):
    # to help iter ['1', '<text>', '2', '<text>', 3', ...]
    it = iter(alternating_list)
    for first in it:
        second = next(it)
        yield (first, second)

# # to generate chapter_counts.csv:
# def output_chapter_counts():
#     counts = dict()
#     for book in constants.BOOK_NAMES:
#         book_text = get_book_text(book)
#         counts[book] = len(parse_raw_book(book_text)) if has_chapters(book_text) else 1
#
#     with open('data/chapter_counts.csv', 'w') as file:
#         file.write(
#             '\n'.join( f'{book},{count}' for book,count in counts.items() )
#         )

if __name__ == '__main__':
    main()
    # test()
