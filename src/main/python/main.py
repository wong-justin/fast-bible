'''Refactoring pages of app for more consistency and extensibility.'''

from book_logic import *
del globals()['data']
import book_logic
from constants import appctxt

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog)

from types import SimpleNamespace
# import re
# import ctypes
import sys
import time
import os

class ScriptureLocation:
    '''Abstraction to divide scripture into buildable parts.

    s = ScriptureLocation()
    # some scope...
        s.increment(book='Genesis')
    # different scope...
        s.increment(chapter=1)
    # and another
        s.decrement()'''

    def __init__(self):
        self.components = []

    def increment(self, book=None, chapter=None, verse=None):
        # just add the kwarg that makes sense, no need to validate
        self.components.append(book or chapter or verse)
        return str(self)

    def decrement(self):
        if self.components:
            self.components.pop(-1)
        return str(self)

    def __repr__(self):
        template = {
            0: 'Bible',
            1: '{}',
            2: '{} {}',
            3: '{} {}:{}'
        }[ len(self.components) ]
        return template.format(*self.components)

data = SimpleNamespace(
    # bible=load_bible_json(),
    curr_scripture=ScriptureLocation(),
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

    PageA(Page):
        ...
        a.nav.to(PageB, state=data_for_b)
        a.nav.back()
        a.nav.set_title('title')

    PageB(Page):
        def load_state(self, state):
            # do something
    '''
    # def __init__(self, widget, nav):
        # self.title = Page.title
    #     self.nav = nav
    #     self.widget = widget

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
    '''Groups Page subclasses with navigating logic.

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

    # def keyPressEvent(self, event):
    #     # give control to current page instead of this widget absorbing the event
    #     self.curr_page.keyPressEvent(event)
    #     return

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

def overlay_bot_right(widget, other):
    grid = QGridLayout()
    # grid.addWidget(self, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)
    grid.addWidget(other, 0, 0, Qt.AlignRight | Qt.AlignBottom)
    grid.setContentsMargins(2,2,2,2)
    widget.setLayout(grid)

class Filterable(QWidget):
    '''Generic widget with an activatable searchbox for filtering items.
    Main inspiration from fman.

    Holds self.all_items, an iterable.
    Subclasser needs to implement show_items(items) at minimum.
    filter_items(search_text) good to override filtering method.'''

    def __init__(self):
        self.searchbox = SearchBox(self)
        overlay_bot_right(self, self.searchbox)

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
        self.filterable.show_all()

class FilterableList(QListWidget, Filterable):
    '''Implements Filterable as a standard list widget.'''

    NAVIGATION_KEYPRESSES = {
        Qt.Key_Up,
        Qt.Key_Down,
        Qt.Key_Left,
        Qt.Key_Right,
        Qt.Key_Return,
    }

    def __init__(self):
        QListWidget.__init__(self)
        Filterable.__init__(self)

    def show_items(self, items):
        self.clear()
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
        start_loading_book(book)    # old method
        # show content
        if has_chapters(book):
            # go to chapter screen
            self.nav.to(ChaptersPage, state=get_num_chapters(book))
        else:
            # skip to verses screen

            # new method
            # self.nav.to(VersesPage, state=data.bible[book])

            # old method
            wait_for_loaded_book()
            verses = get_current_book()
            self.nav.to(VersesPage, state=verses)


        # widget cleanup
        self.nav.set_title(data.curr_scripture.increment(book))
        self.searchbox.deactivate()
        self.show_all()     # reset any searches when naving back

    def keyPressEvent(self, event):
        # if not self.search_is_active() and event.key() == Qt.Key_Backspace:
        #     self.nav.back()
        #     self.nav.set_title(data.curr_scripture.decrement())
        # else:
        #     FilterableList.keyPressEvent(self, event)
        FilterableList.keyPressEvent(self, event)   # this is 0th page; don't need nav back

        # if keypress == ctrl_F:
        #     self.nav.to(SearchResultsPage, state='scope:')

    # def load_state(self, state):
    #     # book names are static so load one time, no need to change
    #     # self.books_data = state
    #     self.list_items = state # book names

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

        # show the content
        # new method
        # book = data.curr_scripture.book
        # self.nav.to(VersesPage, state=data.bible[book][chapter])

        # old method
        wait_for_loaded_book()
        verses = get_chapter(chapter)
        self.nav.to(VersesPage, state=verses)
        # self.nav.to(VersesPage, state=None) # for testing

        # widget cleanup
        self.nav.set_title(data.curr_scripture.increment(chapter))
        self.searchbox.deactivate()
        self.show_all()  # reset any searches when naving back

    def keyPressEvent(self, event):
        if not self.search_is_active() and event.key() == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(data.curr_scripture.decrement())
        else:
            FilterableList.keyPressEvent(self, event)

        # if keypress == ctrl_F:
        #     self.nav.to(SearchResultsPage, state='scope:')

class VersesPage(Page, QTextEdit, Filterable):
    '''Formats dict of verses {num: text} into text display.
    Filterable by verse num, isolating and highlighting text.'''

    def __init__(self):
        Page.__init__(self)
        QTextEdit.__init__(self)
        Filterable.__init__(self)

        # style
        self.setReadOnly(True)
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

    def load_state(self, state):
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
        # highlight given verse number

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

    def keyPressEvent(self, event):
        keypress = event.key()
        # nav back when no searchbox
        if not self.search_is_active() and keypress == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(data.curr_scripture.decrement())
            self.verticalScrollBar().setValue(0)    # back to top
        # scrolling in the text widget
        elif keypress in (Qt.Key_Down, Qt.Key_Up):
            QTextEdit.keyPressEvent(self, event)
        # keypress goes to searchbox
        else:
            Filterable.keyPressEvent(self, event)

        # if keypress == ctrl_F:
        #     self.nav.to(SearchResultsPage, state='scope:')

def format_to_html(verses):
    # returns numbers spaced and bolded before verse texts.
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

def MarginParent(widget):
    # create parent with small margins around widget
    parent = QWidget()
    widget.setParent(parent)

    margins = QGridLayout()
    margins.addWidget(widget, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)
    margins.setContentsMargins(2,2,2,2)

    parent.setLayout(margins)
    return parent

# --- run

if __name__ == '__main__':
    book_logic.init_data()
    app = QApplication([])
    set_theme(app)

    main = MarginParent(PageManager(BooksPage, ChaptersPage, VersesPage))
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




### --- new feature

# class SearchResultsPage(Page, FilterableList):
#
#
#     def __init__(self):
#         pass
#
    # def load_state(self, state):
    #     self.iter_verses = state.iter_verses
    #     self.nav.set_title('Search in ' + state.scope)
    #
    # def show_all(self):
    #     # don't want to show all verses with no search
    #     return
#
    # def show_items(self, items):
    #     # replaced by custom filter_items
    #     return
#
    # def filter_items(self, search_text):
    #     pattern = re.compile(search_text)
    #     for verse in self.iter_verses:
    #         # if self.new_search_started:
    #         #     break
    #         if re.match(pattern, verse):
    #             self.addItem(verse)     # QtListWidget method
#
#     def keyPressEvent(self, event):
#         if not self.search_is_active() and event.key() == Qt.Key_Backspace:
#             self.nav.back()
#             self.nav.set_title(data.curr_scripture.decrement())
#         else:
#             FilterableList.keyPressEvent(self, event)
