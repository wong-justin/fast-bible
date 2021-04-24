# rename me bible_logic or shared

# data
import constants

from threading import Thread
from types import SimpleNamespace
import json

data = SimpleNamespace(
    CHAPTER_COUNTS=None,
    BOOK_NAMES=None,
    thread=None,
    current_book=None,
    current_text=None,
)

def init_data():
    data.CHAPTER_COUNTS = constants.CHAPTER_COUNTS
    data.BOOK_NAMES = constants.BOOK_NAMES
    return data

def get_book_names():
    return data.BOOK_NAMES

def get_num_chapters_for(book):
    return data.CHAPTER_COUNTS[book]

def get_num_chapters(book):
    return data.CHAPTER_COUNTS[book]

def has_chapters(book):
    return get_num_chapters_for(book) is not 1

def start_loading_book(book):
    # create worker thread
    if data.thread and data.thread.is_alive():
        data.thread.stop()
    data.thread = Thread(target=load_book, args=(book,))
    data.thread.start()

def load_book(book):
    # # data.current_book = parsing.parse_book( parsing.get_book_text(book) ) # broken for psalms
    # data.current_book = parsing.load_book(book)
    # # data.current_book = open(f'{book}.txt').split('\n\t')

    # fp = constants.appctxt.get_resource(constants.BOOK_FP_TEMPLATE.format(book))
    fp = constants.BOOK_FP_TEMPLATE.format(book)
    with open(fp, 'r') as file:
        data.current_book = json.load(file)

def wait_for_loaded_book():
    data.thread.join()

def get_chapter(chapter_num):
    verses = data.current_book[chapter_num]
    return verses
    # data.current_text = '\xa0\xa0'.join( num_template.format(n) + v for n,v in verses.items() )
    # return data.current_text

def get_current_book():
    return data.current_book

# def get_verses_from_current_chapter(verse_nums):
def iter_selected_verses(verse_nums):
    for num, text in data.current_verses:
        is_selected = int(num) in verse_nums
        yield is_selected, text


### --- new

def load_old_book(book_name):
    fp = constants.BOOK_FP_TEMPLATE.format(book_name)
    with open(fp, 'r') as file:
        return json.load(file)

def load_bible_json():
    bible = {}
    for book_name in data.BOOK_NAMES:
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
