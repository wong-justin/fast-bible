'''Shared constants/methods for consistency between setup and gui.'''

from fbs_runtime.application_context.PyQt5 import ApplicationContext

def _read_csv(fp):
    '''Returns list of chunks per line'''
    with open(fp, 'r') as file:
        line = file.readline()
        while line:
            yield line.split(',')
            line = file.readline()

appctxt = ApplicationContext()

# paths = SimpleNamespace(
#     BOOK_DIR = appctxt.get_resource('data/cleaned/'),
#     BOOK_FP_TEMPLATE = BOOK_DIR + '/{}.json'
# )
BOOK_DIR = appctxt.get_resource('data/cleaned/')
BOOK_FP_TEMPLATE = BOOK_DIR + '/{}.json'
# BOOK_FILENAME_TEMPLATE = '{}.json'
# BOOK_FP_TEMPLATE = '../resources/data/cleaned/{}.json'
# BOOK_FP_TEMPLATE = appctxt.get_resource('data/cleaned/{}.json')
CHAPTER_COUNTS = {
    book_name: int(count)
    for book_name, count in _read_csv(appctxt.get_resource('data/chapter_counts.csv'))
    # for book_name, count in _read_csv('../resources/data/chapter_counts.csv')
}
BOOK_NAMES = list(CHAPTER_COUNTS.keys())
