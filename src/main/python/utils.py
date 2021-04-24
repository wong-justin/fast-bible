'''Refactoring pages of app for more consistency and extensibility.'''

from book_logic import *
from shared import *

from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon, QFontMetrics
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog, QTableWidget, QTableWidgetItem,
    QListWidgetItem, QStyledItemDelegate, QStyle)

from types import SimpleNamespace
# import ctypes

class Scripture:
    '''Abstraction to divide scripture into sequential parts.

    Scripture().inc('Psalms').inc(83).inc(18)
    >>> 'Psalms 83:18'

    Scripture().inc('Jude').inc(4)
    >>> 'Jude 4'

    Scripture('Genesis', 3, 15).dec().dec()
    >>> 'Genesis'
    '''

    _templates = {
        0: 'Bible',
        1: '{}',
        2: '{} {}',
        3: '{} {}:{}'
    }

    def __init__(self, *parts):
        self.parts = list(parts)

    def dec(self, inplace=False):
        if inplace:
            if self.parts:
                self.parts.pop(-1)
            return str(self)

        if self.parts:
            return Scripture(self.parts[:-1])
        else:
            return Scripture()

    def inc(self, book=None, chapter=None, verse=None, inplace=False):
        if inplace:
            self.parts.append(book or chapter or verse)
            return str(self)
        else:
            return Scripture(*self.parts, book or chapter or verse)

    def __repr__(self):
        template = Scripture._templates[ len(self.parts) ]
        return template.format(*self.parts)

data = SimpleNamespace(
    bible=None,
    curr_scripture=Scripture(),
)

def init_data():
    data.bible = load_bible_json()
    data._all_verses = list(_iter_verses_in_whole_bible())  # maybe this will be faster?

### --- widgets to implement

class Page:
    '''Abstract class for a widget used in PageManager.

    Recieves PageManager as a nav attribute, allowing communication with other pages.
    Implement load_state() so other pages can send data when navigating to this one.

    PageA(Page):
        ...
        a.nav.to(PageB, state=data_for_b)
        a.nav.back()
        a.nav.set_title('title')

    PageB(Page):
        def load_state(self, state):
            # do something
    '''

    # page recreatable with state
    def load_state(self, state):
        pass

    # def set_title(self, str):
    #     pass

    def keyPressEvent(self, event):
        # default navigation; fall back on
        if event.key() == Qt.Key_Backspace:
            self.nav.back()

class PageManager(QStackedWidget):
    '''Groups Page subclasses for navigating among each other or back in history.

    Needs to be child of main window.'''

    def __init__(self, *page_types, parent=None):
        '''*args: classes to be instantiated.
        Each class must be distinct and extend Page, QWidget.

        PageManager(PageA, PageB, ...)'''

        super().__init__(parent)

        self._pages = {}
        for _type in page_types:

            page = _type()
            page.nav = self

            self.addWidget(page)
            self._pages[_type] = page

        self._history = []   # page ids, not page objects themselves
        self._curr_id, self.curr_page = list(self._pages.items())[0]  # the first page in given args

    def to(self, new_id, state=None):#, title=None):
        '''Used by a page to nav to another page, communicating any new data with state.

        new_id: class of page to nav to. Must be one given in constructor.
        state: data to given to new_page.load_state()
            default None to reuse old state

        class PageA:
            ...
            self.nav.to(PageB, state='new_data')'''

        self._history.append(self._curr_id)

        new_page = self._pages[new_id]
        if state is not None:
            new_page.load_state(state)

        self._set_curr_page(new_id, new_page)

    def back(self):
        '''Go to previous page. Used in default Page keyPressEvent listener.'''
        if self._history:
            prev_id = self._history.pop()
            prev_page = self._pages[prev_id]
            self._set_curr_page(prev_id, prev_page)

    def _set_curr_page(self, _id, page):
        self._curr_id = _id
        self.curr_page = page
        self.setCurrentWidget(page)

    def set_title(self, _str):
        # self will be the highest-level obj in the app that pages have access to
        #  so it makes sense to put app title method in self
        self.setWindowTitle(_str)
        self.parentWidget().setWindowTitle(_str)

class Filterable(QWidget):
    '''Generic widget with an activatable searchbox for filtering items.
    Main inspiration from fman.

    Holds self.all_items, an iterable.
    Subclasser needs to implement show_items(items) at minimum.
    filter_items(search_text) good to override filtering method.'''

    def __init__(self):
        self.searchbox = SearchBox(self)
        add_grid_child(self, self.searchbox, Qt.AlignRight | Qt.AlignBottom)

    def set_items(self, items):
        # self.all_items = items
        self.all_items = [str(i) for i in items]
        self.show_all()

    def show_all(self):
        self.show_items(self.all_items)

    def show_items(self, items):
        # to implement, show items from anywhere
        pass

    def filter_items(self, search_text):
        # basic implementation would return self.show_items(self.all_items, lambda i:search_text in i)
        self.show_items( index_first_search(self.all_items, search_text) )

    def search_is_active(self):
        # convenience
        return self.searchbox.isVisible()

    def keyPressEvent(self, event):
        # determine activating, using, and deactivint searchbox
        keypress = event.key()

        # active searchbox, middle of typing
        if self.search_is_active():
            if keypress == Qt.Key_Escape:
                self.searchbox.deactivate()
            else:
                self.searchbox.keyPressEvent(event)
        # inactive searchbox
        else:
            if keypress_produces_symbol(keypress):
                self.searchbox.activate(event.text())

class SearchBox(QLineEdit):
    # helper coupled within Filterable. No need to instantiate elsewhere.

    def __init__(self, parent_filterable):
        super().__init__()

        sp = self.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.setSizePolicy(sp)
        self.hide()

        font = self.font()
        font.setPointSize(8)
        self.setFont(font)

        p = self.palette()
        p.setColor(QPalette.Text, QColor(199, 196, 152))
        p.setColor(QPalette.Base, QColor(49, 52, 64))
        self.setPalette(p)
        self.setStyleSheet('border: 1px solid rgba(199, 196, 152, 64)')

        self.filterable = parent_filterable
        self.textChanged.connect(self.on_change)

    def on_change(self, text):

        if not text:  # was just cleared
            self.deactivate()
            self.filterable.show_all()
        else:
            # narrow current list
            pattern = text
            self.filterable.filter_items(pattern)
            # print(text)

    def activate(self, initial_text):
        # show and start searching
        self.setText(initial_text)
        self.on_change(initial_text) # first key of search needs to call change too
        self.show()
        # self.setFocus()

    def deactivate(self):
        # hide and stop searching
        self.hide()
        # self.clear()
        self.setText('')
        self.filterable.show_all()

class FilterableList(QListWidget, Filterable):
    '''Implements Filterable as a standard list widget.
    Shows placeholder when list is empty.'''

    NAVIGATION_KEYPRESSES = {
        Qt.Key_Up,
        Qt.Key_Down,
        Qt.Key_Left,
        Qt.Key_Right,
        Qt.Key_Return,
    }

    def __init__(self, placeholder='no results.\ntype something else'):
        QListWidget.__init__(self)
        Filterable.__init__(self)

        self.placeholder = EmptyPlaceholderWidget(self, placeholder)
        self.placeholder.hide()
        add_grid_child(self, self.placeholder, Qt.AlignCenter, grid=self.layout())

    def addItem(self, *args, **kwargs):
        super().addItem(*args, **kwargs)
        self.placeholder.hide()

    def clear(self):
        # completely blank page looks bad; give a message
        super().clear()
        self.placeholder.show()

    def show_items(self, items):
        self.clear()
        if len(items) == 0:
            return

        self.placeholder.hide()
        self.insertItems(0, (str(i) for i in items) )
        # self.insertItems(0, items)
        self.setCurrentRow(0)

    def keyPressEvent(self, event):
        if event.key() in FilterableList.NAVIGATION_KEYPRESSES:
            # save up, down, enter for default list widget behavior.
            QListWidget.keyPressEvent(self, event)
            return

        Filterable.keyPressEvent(self, event)

### --- some convenience widgets

def EmptyPlaceholderWidget(parent=None, msg='placeholder'):
    # unassuming label showing that nothing is here
    label = QLabel(msg, parent)
    label.setAlignment(Qt.AlignCenter)
    set_half_transparent(label)
    return label

def MarginParent(widget):
    # create parent with small margins around widget
    parent = QWidget()
    widget.setParent(parent)

    margins = MarginGrid()
    margins.addWidget(widget, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)

    parent.setLayout(margins)
    return parent

def MarginGrid():
    # returns grid layout with small margin around outside
    layout = QGridLayout()
    layout.setContentsMargins(2,2,2,2)
    return layout

### --- widget helpers / styling / convenience

def add_grid_child(parent, child, position, grid=None):
    # supplies grid layout if not specified
    g = MarginGrid() if not grid else grid
    g.addWidget(child, 0, 0, position)
    parent.setLayout(g)

def set_half_transparent(label):
    p = label.palette()
    color = p.color(QPalette.WindowText)
    color.setAlpha(255//2)
    p.setColor(QPalette.WindowText, color)
    label.setPalette(p)

def set_theme(app):
    # dark theme:
    # https://gist.githubusercontent.com/mstuttgart/37c0e6d8f67a0611674e08294f3daef7/raw/8502123d9bf8ae9a10be880953c7fc0c1a095a21/dark_fusion.py

    dark_palette = QPalette()
    # dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Window, QColor(49, 52, 64))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    # dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.Base, QColor(38, 40, 49))
    # dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.AlternateBase, QColor(49, 52, 64))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    # dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Text, QColor(222, 226, 247))
    # dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Button, QColor(49, 52, 64))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    # dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(158, 161, 179))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
    app.setStyle("Fusion")

    # # icon
    # icon = QIcon()
    # # icon.addFile('../resources/assets/icon4.ico')
    # icon.addFile(appctxt.get_resource('assets/icon4.ico'))
    #     # something hacky for windows to show icon in taskbar
    # myappid = 'biblenavigation.myapp' # arbitrary string
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    #
    # app.setWindowIcon(icon)

    # custom font
    font_db = QFontDatabase()
    # font_db.addApplicationFont('../assets/Noto_Serif/NotoSerif-Regular.ttf')
    # font_db.addApplicationFont('../resources/assets/Noto_Sans/NotoSans-Regular.ttf')
    font_db.addApplicationFont(appctxt.get_resource('assets/Noto_Sans/NotoSans-Regular.ttf'))
    # font = QFont('Noto Serif')
    font = QFont('Noto Sans')
    font.setPointSize(10)
    app.setFont(font)

def set_font_size(widget, size):
    font = widget.font()
    font.setPointSize(11)
    widget.setFont(font)

def ctrl_f_event(event):
    return event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F

def keypress_produces_symbol(key):
    # returns False for backspace, modifiers, arrows, etc
    # https://doc.qt.io/qt-5/qt.html#Key-enum

    # return (
    #     key < Qt.Key_Escape or
    #     key in (Qt.Key_Shift, Qt.Key_CapsLock)
    # )
    # return bool( event.text() )
    return key < Qt.Key_Escape

### --- iterating verses depending on scripture location scope

def iter_verses_in_whole_bible():
    yield from data._all_verses

def _iter_verses_in_whole_bible():
    for book_name in BOOK_NAMES:
        book_scripture = Scripture(book_name)

        if has_chapters(book_name):
            yield from iter_verses_in_book(book_scripture)
        else:
            verses = data.bible[book_name]
            scriptures_with_verses(book_scripture, verses)

def iter_verses_in_book(book_scripture):
    # for book with chapters

    # book = data.bible[scripture.parts[0]]
    book = get_bible_content(book_scripture)
    for chapter_num, verses in book.items():
        # chapter_scripture = book_scripture.inc(chapter_num)
        yield from scriptures_with_verses(book_scripture.inc(chapter_num), verses)

def iter_verses_in_chapter(chapter_scripture):
    verses = get_bible_content(chapter_scripture)
    yield from scriptures_with_verses(chapter_scripture, verses)

def scriptures_with_verses(scripture, verses):
    # chapter scripture, or possibly book scripture if book doesn't have chapters
    yield from (
        (scripture.inc(verse_num), text)
        for verse_num, text in verses.items()
    )

# def verses_around_scripture(scripture):
#     return get_bible_content(scripture.dec())
#
# def get_verse(scripture):
#     return get_bible_content(scripture)

def get_bible_content(scripture):
    # returns content at finest scope of scripture
    scope = data.bible
    for component in scripture.parts:
        scope = scope[component]
    return scope

### --- boring python utils

def index_first_search(items, search_text):
    # matches that contain search_text, with matches at index 0 ordered first
    # [Exodus, Zephaniah, Ephesians], 'eph' => [Ephesians, Zephaniah]
    results = [x for x in items if search_text in x.lower()]    #s.lower().replace(' ', '') # for 1/2/3 <book>, skipping user needing space
    best_results, remaining = partition(results, starts_with(search_text))
    return [*best_results, *remaining]

def partition(items, key):
    matches = []
    remaining = []
    for item in items:
        if key(item):
            matches.append(item)
        else:
            remaining.append(item)
    return matches, remaining

def starts_with(s):
    return lambda x:x.lower().index(s) == 0

def format_to_html(verses):
    # returns numbers spaced and bolded preceding verse content.
    return '   '.join(          # 2 nbsps post-num and 4 spaces pre-num looks good, even
        f'<b>{num}</b>\xa0\xa0{verse}'     # spacing probably changes with diff fonts
        for num, verse in verses.items()
    )

def to_plaintext(html):
    # used to precisely match QTextEdit text content (for searching index)
    replaced = html.replace('\xa0', ' ').replace('\n', ' ')
    tagless = ''.join( strip_tags(replaced) )
    return tagless

def strip_tags(html):
    # helping to_plaintext
    in_tag = False
    for c in html:
        if in_tag:
            if c == '>':
                in_tag = False
            continue
        else:
            if c == '<':
                in_tag = True
                continue
            else:
                yield c

def dict_where_keys(d, filter_key_fn):
    return {k:v for k,v in d.items() if filter_key_fn(k)}

OPACITY_TEMPLATE = '<span style="color:rgba(222, 226, 247, 0.5);">{}</span>'
