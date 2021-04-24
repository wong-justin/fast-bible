'''Refactoring pages of app for more consistency and extensibility.'''

from book_logic import *
del globals()['data']
import book_logic
from constants import appctxt

from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon, QFontMetrics
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog, QTableWidget, QTableWidgetItem,
    QListWidgetItem, QStyledItemDelegate, QStyle)

from types import SimpleNamespace
import re
# import ctypes
import sys
import time
import os
import json

# class ScriptureLocation:
#     '''Abstraction to divide scripture into buildable parts.
#
#     s = ScriptureLocation()
#     # some scope...
#         s.increment(book='Genesis')
#     # different scope...
#         s.increment(chapter=1)
#     # and another
#         s.decrement()'''
#
#     def __init__(self, *components):
#         # Scripture('Genesis', 3, 15)
#         # Scripture('Jude')
#         self.components = components
#
#     def increment(self, book=None, chapter=None, verse=None):
#         # just add the kwarg that makes sense, no need to validate
#         self.components.append(book or chapter or verse)
#         return str(self)
#
#     def decrement(self):
#         if self.components:
#             self.components.pop(-1)
#         return str(self)
#
#     def __repr__(self):
#         template = {
#             0: 'Bible',
#             1: '{}',
#             2: '{} {}',
#             3: '{} {}:{}'
#         }[ len(self.components) ]
#         return template.format(*self.components)

class Scripture:
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

    # @property
    # def book(self):
    #     return self.parts[0]
    #
    # @property
    # def chapter(self):
    #     return self.parts[1]
    #
    # @property
    # def verse(self):
    #     return self.parts[-1]

data = SimpleNamespace(
    bible=None,
    curr_scripture=Scripture(),
)

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

### --- generalized widgets

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

    def to(self, new_id, state=None):#, title=''):
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

        # print([_id.__name__ for _id in self._history])

    def back(self):
        '''Go to previous page. Used in default Page keyPressEvent listener.'''
        if self._history:
            prev_id = self._history.pop()
            prev_page = self._pages[prev_id]
            self._set_curr_page(prev_id, prev_page)

        # print([_id.__name__ for _id in self._history])

    def _set_curr_page(self, _id, page):
        self._curr_id = _id
        self.curr_page = page
        self.setCurrentWidget(page)

    def set_title(self, _str):
        # self will be the highest-level obj in the app that pages have access to
        #  so it makes sense to put app title method in self
        self.setWindowTitle(_str)
        self.parentWidget().setWindowTitle(_str)

# def set_grid_children(parent, grid=None, children=[], positions=[]):
#     g = MarginGrid() if not grid else grid
#     for child, position in zip(children, positions):
#         g.addWidget(child, 0, 0, position)
#     parent.setLayout(g)

def set_grid_child(parent, child, position, grid=None):
    # less verbose and more used
    g = MarginGrid() if not grid else grid
    g.addWidget(child, 0, 0, position)
    parent.setLayout(g)

class Filterable(QWidget):
    '''Generic widget with an activatable searchbox for filtering items.
    Main inspiration from fman.

    Holds self.all_items, an iterable.
    Subclasser needs to implement show_items(items) at minimum.
    filter_items(search_text) good to override filtering method.'''

    def __init__(self):
        self.searchbox = SearchBox(self)

        # set_grid_children(self,
        #     children=(self.searchbox,),
        #     positions=(Qt.AlignRight | Qt.AlignBottom,)
        # )
        set_grid_child(self, self.searchbox, Qt.AlignRight | Qt.AlignBottom)
        # overlay_bot_right(self, self.searchbox)
        # set_grid_layout(self, EmptyPlaceholderWidget(), self.searchbox)
        # self.placeholder = EmptyPlaceholderWidget(self)

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
            if key_produces_symbol(keypress):
                self.searchbox.activate(event.text())

def key_produces_symbol(key):
    # returns False for backspace, modifiers, arrows, etc
    # https://doc.qt.io/qt-5/qt.html#Key-enum

    # return (
    #     key < Qt.Key_Escape or
    #     key in (Qt.Key_Shift, Qt.Key_CapsLock)
    # )
    # return bool( event.text() )
    return key < Qt.Key_Escape

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

def set_half_transparent(label):
    p = label.palette()
    color = p.color(QPalette.WindowText)
    color.setAlpha(255//2)
    p.setColor(QPalette.WindowText, color)
    label.setPalette(p)

def EmptyPlaceholderWidget(parent=None, msg='placeholder'):
    label = QLabel(msg, parent)
    label.setAlignment(Qt.AlignCenter)
    set_half_transparent(label)
    return label

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
        # set_grid_children(self,
        #     grid=self.layout(),
        #     children=(self.placeholder,),
        #     positions=(Qt.AlignCenter,),
        # )
        set_grid_child(self, self.placeholder, Qt.AlignCenter, grid=self.layout())

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

### --- using generalized widgets

class BooksPage(Page, FilterableList):
    '''Implements list from Gen->Rev and connects to next chapters page.'''

    def __init__(self):
        Page.__init__(self)
        FilterableList.__init__(self)

        self.set_items(get_book_names())
        # self.set_items([c for c in 'abcdefghijklmnopqrstuvwxyz']) # for testing
        self.itemActivated.connect(self.on_book_selected)

    def on_book_selected(self, book_item):
        # book_item is QtListItem
        book = book_item.text()
        # start_loading_book(book)    # file io takes a bit, so start now in other thread

        # self.nav.to(ChaptersPage, state=100) # for testing
        # start_loading_book(book)    # old method
        # show content
        if has_chapters(book):
            # go to chapter screen
            self.nav.to(ChaptersPage, state=get_num_chapters(book))
        else:
            # skip to verses screen

            # new method
            self.nav.to(VersesPage, state=data.bible[book])

            # old method
            # wait_for_loaded_book()
            # verses = get_current_book()
            # self.nav.to(VersesPage, state=verses)


        # widget cleanup
        self.nav.set_title(data.curr_scripture.inc(book, inplace=True))
        self.searchbox.deactivate()
        self.show_all()     # reset any searches when naving back

    def keyPressEvent(self, event):
        # if not self.search_is_active() and event.key() == Qt.Key_Backspace:
        #     self.nav.back()
        #     self.nav.set_title(data.curr_scripture.decrement())
        # else:
        #     FilterableList.keyPressEvent(self, event)
        if ctrl_f_event(event):
            chapters = get_current_book()
            self.nav.to(SearchResultsPage, state=lambda: iter_verses_in_whole_bible())
            self.searchbox.deactivate()
        else:
            FilterableList.keyPressEvent(self, event)   # this is 0th page; don't need nav back

class ChaptersPage(Page, FilterableList):
    '''Implements list of chapters 1->n for current book and connects to next verses page.

    Uses IO/threading for book logic; probably not needed for small book jsons.
    Maybe somewhat useful for one big json before it's loaded into memory?'''

    def __init__(self):
        Page.__init__(self)
        FilterableList.__init__(self)

        self.itemActivated.connect(self.on_chapter_selected)

    def load_state(self, state):
        num_chapters = state
        self.set_items(range(1, num_chapters+1))

    def on_chapter_selected(self, chapter_item):

        chapter = chapter_item.text()
        data.curr_scripture.inc(chapter, inplace=True)

        # show the content
        # new method
        # book = data.curr_scripture.book
        verses = get_bible_content(data.curr_scripture)
        self.nav.to(VersesPage, state=verses)

        # old method
        # wait_for_loaded_book()
        # verses = get_chapter(chapter)
        # self.nav.to(VersesPage, state=verses)

        # widget cleanup
        self.nav.set_title(str(data.curr_scripture))
        self.searchbox.deactivate()
        self.show_all()  # reset any searches when naving back

    def keyPressEvent(self, event):
        if not self.search_is_active() and event.key() == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(data.curr_scripture.dec(inplace=True))
        elif ctrl_f_event(event):
            # book_scripture = data.curr_scripture
            self.nav.to(SearchResultsPage, state=lambda: iter_verses_in_book(data.curr_scripture))
            self.searchbox.deactivate()
        else:
            FilterableList.keyPressEvent(self, event)

# def read_book(book_name):
#     fp = constants.BOOK_FP_TEMPLATE.format(book_name)
#     with open(fp, 'r') as file:
#         return json.load(file)

# def iter_all_bible_verses():
#     for book_name in book_logic.data.BOOK_NAMES:
#         # book = read_book(book_name)
#         book = data.bible[book_name]
#         if has_chapters(book_name):
#             chapters = book
#             yield from iter_verses(book_name, chapters)
#         else:
#             verses = book
#             yield from (
#                 (f'{book_name} {n}',v)
#                 for n,v in verses.items()
#             )

# def iter_verses(book_name, chapters):
#     # for verses in chapters.values():
#     #     yield from verses.items()
#
#     # chapters are out of order in file, ugh. fix setup script later
#     chapter_nums = (str(i) for i in range(1, len(chapters)+1))
#     for c in chapter_nums:
#         verses = chapters[c]
#         yield from (
#             (f'{book_name} {c}:{n}',v)
#             for n,v in verses.items()
#         )

def iter_verses_in_whole_bible():
    for book_name in book_logic.data.BOOK_NAMES:
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

# def verses_around_scripture(scripture):
#     scope = data.bible
#     for component in scripture.dec().parts:
#         scope = scope[component]
#     return scope

def ctrl_f_event(event):
    return event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_F

def set_font_size(widget, size):
    font = widget.font()
    font.setPointSize(11)
    widget.setFont(font)

class VersesPage(Page, QTextEdit, Filterable):
    '''Formats dict of verses {num: text} into text display.
    Filterable by verse num, isolating and highlighting text.'''

    def __init__(self):
        Page.__init__(self)
        QTextEdit.__init__(self)
        Filterable.__init__(self)

        # style
        self.setReadOnly(True)
        set_font_size(self, 11)

    def load_state(self, state):
        # state = dict of verses in chapter
        self.verses = state
        self.show_all()

    def show_all(self):
        # render
        html = format_to_html(self.verses)
        self.set_html(html)

    def set_html(self, html):
        # wrapping textEdit.setHtml to keep scroll position
        scroll_pos = self.verticalScrollBar().value()
        self.setHtml(html)   # this resets scroll
        self.verticalScrollBar().setValue(scroll_pos)

    def filter_items(self, pattern):
        # highlight verse, given number

        # make sure the verse is there
        if pattern not in self.verses.keys():
            self.show_all()
            return

        n = int(pattern)
        verse = self.verses[str(n)]

        # divide text around verse
        pre_verses = dict_where_keys(self.verses, lambda k: int(k) < n)
        main_verse = {n: verse}
        post_verses = dict_where_keys(self.verses, lambda k: int(k) > n)

        pre, main, post = (format_to_html(vs) for vs in (pre_verses, main_verse, post_verses))

        html = (
            OPACITY_TEMPLATE.format(pre) +
            f' {main} ' +
            OPACITY_TEMPLATE.format(post)
        )
        self.set_html(html)

        # find verse position in text widget
        plain_verse = to_plaintext(main)
        plain_start = self.toPlainText().index(plain_verse)
        c = self.textCursor()
        c.setPosition(plain_start)
        self.setTextCursor(c)

        # scroll to verse position
        rect = self.cursorRect()
        top = rect.top()
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.value() + top)   # top of verse is top of screen
        if not vbar.value() == vbar.maximum():  # avoid edge case of last verse: it stays maximum scroll, else hiding last line
            vbar.triggerAction(QAbstractSlider.SliderSingleStepSub) # but in general content looks nicer when not pinned to top

    def change_highlighted_scripture(self, diff):
        # make sure a verse is already selected
        pattern = self.searchbox.text()
        if pattern not in self.verses.keys():
            return
        # make sure desired verse within bounds
        n = int(pattern) + diff
        if str(n) not in self.verses.keys():
            return

        # update searchbox, which triggers new highlight filter and updates user
        self.searchbox.activate(str(n))

    def keyPressEvent(self, event):
        keypress = event.key()

        # nav back when backspacing without searchbox
        if not self.search_is_active() and keypress == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(data.curr_scripture.dec(inplace=True))
            self.verticalScrollBar().setValue(0)    # scroll back to top

        elif event.modifiers() == Qt.ControlModifier:

            # scripture up/down
            if keypress in (Qt.Key_Down, Qt.Key_Up):
                diff = (1 if keypress == Qt.Key_Down else -1)
                self.change_highlighted_scripture(diff)

            # search this chapter
            elif keypress == Qt.Key_F:
                # scripture = data.current_scripture
                self.nav.to(SearchResultsPage, state=lambda: scriptures_with_verses(data.curr_scripture, self.verses))
                self.searchbox.deactivate()
                # self.verticalScrollBar().setValue(0)    # scroll back to top

        # scroll
        elif keypress in (Qt.Key_Down, Qt.Key_Up):
            QTextEdit.keyPressEvent(self, event)

        # keypress goes to searchbox
        else:
            Filterable.keyPressEvent(self, event)

def format_to_html(verses):
    # returns numbers spaced and bolded preceding verse content.
    return '   '.join(      # 2 nbsps post-num and 4 spaces pre-num looks good
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
    # result = dict()
    # for key in d.keys():
    #     if filter_key_fn(key):
    #         result[key] = d[key]
    # return result
    return {k:v for k,v in d.items() if filter_key_fn(k)}

OPACITY_TEMPLATE = '<span style="color:rgba(222, 226, 247, 0.5);">{}</span>'

class SearchResultDelegate(QStyledItemDelegate):
    # custom rendering of an scripture item in a list widget

    def paint(self, painter, option, index):
        # turns item text into title and subtitle.
        # imitates standard list widget item style on select.
        # title bolded, subtitle beneath.

        # maybe custom eliding for ellipsis on both left and right, focused around match?
        # or at least on right, with match surely in view starting from left

        painter.save()
        item = index.data(Qt.DisplayRole) # default item data is at role 0
            # custom data was passed into this item, no longer usual type str

        title = str(item['scripture']) + '\n'
        subtitle = '\n' + item['text']

        given_rect = option.rect    # from size hint
        states = option.state       # bitwise OR of QStyle.State_ flags

        if states & QStyle.State_Selected:
            palette = QApplication.palette()
            painter.setPen(palette.color(QPalette.HighlightedText))
            painter.fillRect(given_rect, palette.color(QPalette.Highlight))

        # text inset by small margin
        text_rect = given_rect.adjusted(2, 2, -2, -2)

        # draw title text
        em_font = QFont(option.font)    # copy
        em_font.setWeight(QFont.Bold)
        painter.setFont(em_font)
        painter.drawText(text_rect, option.displayAlignment, title)

        # draw subtitle text
        painter.setFont(option.font)    # back to default font
        # painter.translate(3, 0)   # slight indent under title might look nice
        elided_subtitle = QFontMetrics(QFont(option.font)).elidedText(subtitle, Qt.ElideRight, text_rect.width())#, Qt.TextShowMnemonic)
        # elided_subtitle = painter.fontMetrics().elidedText(subtitle, Qt.ElideRight, text_rect.width())#, Qt.TextShowMnemonic)
        painter.drawText(text_rect, option.displayAlignment, elided_subtitle)

        painter.restore()

    def sizeHint(self, option, index):
        # fit to width, creating ellipsis on long text with no need for horiz scroll
        # default height seems to have been n*line_height of str in option.data(Qt.DisplayRole)

        s = QSize()
        font_metrics = QFontMetrics(option.font)
        line_height = font_metrics.height()
        extra = 4   # produces more comfortable line spacing; 'elbow room'
        s.setHeight(2*line_height + extra)  # 1 line for title, subtitle each
        s.setWidth(0)   # don't allow horiz scroll when there's wide items
        return s

class SearchResultsPage(Page, FilterableList):
    '''Checks verses in scope for matches and shows results in list widget.
    Displays matches as scripture + text.'''

    def __init__(self):
        self.default_placeholder_msg = 'search regex:'
        Page.__init__(self)
        FilterableList.__init__(self, placeholder=self.default_placeholder_msg)

        self.setItemDelegate(SearchResultDelegate(self))
        # self.itemActivated.connect(self.on_result_item_selected)
        self.fake_searchbox = SearchBox(None)   # illusion to for better communication to user;
            # serves as extra prompt on empty screen
        # set_grid_children(self,
        #     grid=self.layout(),
        #     children=(self.fake_searchbox,),
        #     positions=(Qt.AlignRight | Qt.AlignBottom,)
        # )
        set_grid_child(self, self.fake_searchbox, Qt.AlignRight | Qt.AlignBottom, grid=self.layout())
        self.fake_searchbox.show()

    def load_state(self, state):
        # state = callable that produces iter of verses in desired scope
        self.verses_iter_factory = state
        scope = str(data.curr_scripture)
        self.nav.set_title('Search ' + scope)
        self.show_all()     # trigger empty search display

    def show_all(self):
        # called when empty search, which means
        # show placeholder and extra searchbox prompt for user.
        self.clear()
        self.fake_searchbox.show()
        self.placeholder.setText(self.default_placeholder_msg)

    def show_items(self, items):
        # replaced by custom filter_items, so override and do nothing
        return

    # def on_result_item_selected(self, item):
    #     # callback for list widget selection
    #     d = item.data(Qt.DisplayRole)
    #     self.nav.to(SearchedVersePage, state=d['location'])

    def filter_items(self, search_text):
        # show matches of search in a list
        self.fake_searchbox.hide()  # could be showing if this is first char of search
        self.placeholder.setText(self.default_placeholder_msg)  # could be diff if last search was error

        try:
            re.compile(search_text)
        except re.error:
            # invalid search pattern
            self.placeholder.setText('invalid regex')
            self.clear()
            return

        self.clear()

        for scripture, verse_text in self.verses_iter_factory():
            match = re.search(search_text, verse_text)
            if match is not None:
                item = QListWidgetItem(self)
                item.setData(Qt.DisplayRole, {
                    'scripture': scripture,
                    'text': verse_text.replace('\n', ''),
                })
                self.addItem(item)

                # self.addItem(f'{n}\n' + verse.replace('\n', ' '))    # separate header from content with \n

            # if search_text in verse:
            #     self.addItem(f'{n}\n' + verse)     # QtListWidget method

        if QListWidget.count(self) == 0:
            self.placeholder.setText('no results')

    def keyPressEvent(self, event):
        empty_search = not self.search_is_active() or self.searchbox.text() == ''
        if empty_search and event.key() == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(str(data.curr_scripture))
            # self.clear()
        else:
            FilterableList.keyPressEvent(self, event)

def MarginParent(widget):
    # create parent with small margins around widget
    parent = QWidget()
    widget.setParent(parent)

    margins = MarginGrid()
    margins.addWidget(widget, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)

    parent.setLayout(margins)
    return parent

def MarginGrid():
    layout = QGridLayout()
    layout.setContentsMargins(2,2,2,2)
    return layout

# --- run

if __name__ == '__main__':
    app = QApplication([])
    set_theme(app)

    book_logic.init_data()
    data.bible = load_bible_json()

    main = MarginParent(PageManager(BooksPage, ChaptersPage, VersesPage, SearchResultsPage))
    main.setWindowTitle('Bible')    # initial title to override fbs default
    main.show()

    # if first time loading app
    if len( os.listdir(constants.BOOK_DIR) ) <= 1: # gitignore takes up space
        # initiate content download with welcome window

        dialog = QProgressDialog('', '', 0, 66, main)
        dialog.setMinimumDuration(0)
        dialog.setCancelButton(None)
        dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        dialog.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        dialog.setWindowTitle('Downloading the Bible...')
        dialog.setModal(True)
        dialog.setLabelText('fetching from jw.org...')
        dialog.show()

            # probably should catch errors here
        import setup
        i = 1
        for name in setup.main_progress_iterator():
            dialog.setLabelText(name)
            dialog.setValue(i)
            i += 1
        dialog.close()  # become normal app; main window focused

    # appctxt = ApplicationContext()    # 1. Instantiate ApplicationContext
    exit_code = appctxt.app.exec_()     # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)
