'''App-wide constants'''

from fbs_runtime import _frozen, _source

from pathlib import Path
import sys

# constants as an alternative to using fbs app context,
#  which needs early instantiation and whatnot

_source.project_dir = Path.cwd()

IS_FROZEN = not Path(sys.executable).name == 'python.exe'   # else it would be MyApp.exe in target

RESOURCE_DIR = Path(sys.executable).parent if IS_FROZEN else _source.project_dir / 'src/main/resources/base/'

BUILD_SETTINGS = _frozen.BUILD_SETTINGS if IS_FROZEN else _source.load_build_settings(_source.project_dir)# json.load(Path.cwd() / 'src/build/settings/base.json')

BOOK_DIR = RESOURCE_DIR / 'data/cleaned'
BOOK_FP_TEMPLATE = str(BOOK_DIR / '{}.json')

###--- other app-specific constants

def _read_csv(fp):
    '''Returns list of chunks per line'''
    with open(fp, 'r') as file:
        line = file.readline()
        while line:
            yield line.split(',')
            line = file.readline()

CHAPTER_COUNTS = {
    book_name: int(count)
    for book_name, count in _read_csv(RESOURCE_DIR / 'data/chapter_counts.csv')
    # for book_name, count in _read_csv('../resources/data/chapter_counts.csv')
}
# CHAPTER_COUNTS = {'Zephaniah': 3, 'Haggai': 2, 'Zechariah': 14, 'Malachi': 4, 'Matthew': 28, 'Mark': 16, 'Luke': 24, 'John': 21, 'Acts': 28, 'Romans': 16, '1 Corinthians': 16, '2 Corinthians': 13, 'Galatians': 6, 'Ephesians': 6, 'Philippians': 4, 'Colossians': 4, '1 Thessalonians': 5, '2 Thessalonians': 3, '1 Timothy': 6, '2 Timothy': 4, 'Titus': 3, 'Philemon': 1, 'Hebrews': 13, 'James': 5, '1 Peter': 5, '2 Peter': 3, '1 John': 5, '2 John': 1, '3 John': 1, 'Jude': 1, 'Revelation': 22}
BOOK_NAMES = list(CHAPTER_COUNTS.keys())

# RESTART_EXIT_CODE = 2
