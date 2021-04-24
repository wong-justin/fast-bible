
from shared import *

from types import SimpleNamespace
import json

# bible = {}
#
# def init_bible():
#     load all the jsons or the big json
#
# def all that iter logic:
#     pass

def get_book_names():
    return BOOK_NAMES

def get_num_chapters_for(book):
    return CHAPTER_COUNTS[book]

def get_num_chapters(book):
    return CHAPTER_COUNTS[book]

def has_chapters(book):
    return get_num_chapters_for(book) is not 1

### --- new, once on app startup

def load_old_book(book_name):
    fp = BOOK_FP_TEMPLATE.format(book_name)
    with open(fp, 'r') as file:
        return json.load(file)

def load_bible_json():
    bible = {}
    for book_name in BOOK_NAMES:
        book = load_old_book(book_name)

        if has_chapters(book_name):
            chapters = book
            # result = []
            result = {}
            for i in range(1, len(chapters)+1):
                verses = chapters[str(i)]
                # result.append(verses_dict_to_arr(verses))
                result[str(i)] = verses
            bible[book_name] = result
        else:
            verses = book
            # bible[book_name] = verses_dict_to_arr(verses)
            bible[book_name] = verses
    return bible

def verses_dict_to_arr(verses):
    result = []
    n = len(verses)
    for i in range(1, n+1):
        result.append(verses[str(i)])
    return result
