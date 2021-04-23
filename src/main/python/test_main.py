'''Refactoring pages of app for more consistency and extensibility.'''

from book_logic import *

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog)

from types import SimpleNamespace

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

class Page:
    '''Abstract class for a widget used in PageManager.

    Recieves PageManager as a nav attribute, allowing communication with other pages.

    a = PageA()
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
    Current page shows on top of this widget.'''

    def __init__(self, *page_types):
        '''*args: classes to be instantiated.
        Each class must be distinct and extend Page, QWidget.

        PageManager(PageA, PageB, ...)'''

        super().__init__()

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

def overlay_bot_right(widget, other):
    grid = QGridLayout()
    # grid.addWidget(self, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)
    grid.addWidget(other, 0, 0, Qt.AlignRight | Qt.AlignBottom)
    grid.setContentsMargins(2,2,2,2)
    widget.setLayout(grid)

class Filterable(QWidget):
    # Abstract class to implement to react to searchbox filtering your items.
    # Uses self.all_items, an iterable.
    # Need to implement show_items(items) and maybe filter_items(search_text)

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
        # basic is show regex matches, but probably should override
        # search_key = lambda x:re.search(search_text, x)
        # self.show_items( filter(self.all_items, search_key) )

        self.show_items( index_first_search(self.all_items, search_text) )

    def search_is_active(self):
        return self.searchbox.isVisible()

    def keyPressEvent(self, event):
        keypress = event.key()
        # if keypress in Filterable.NAVIGATION_KEYPRESSES:
        #     event.ignore()
        #     return

        # active searchbox, middle of typing
        if self.search_is_active():
            if keypress == Qt.Key_Escape:
                self.searchbox.deactivate()
            else:
                self.searchbox.keyPressEvent(event)
        # inactive searchbox
        else:
            if is_key_for_typing(keypress):
                self.searchbox.activate(event.text())

def is_key_for_typing(key):
    # return (
    #     key < Qt.Key_Escape or
    #     key in (Qt.Key_Shift, Qt.Key_CapsLock)
    # )
    # return bool( event.text() )
    return key < Qt.Key_Escape  # renderable symbols I think

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
        self.setText(initial_text)
        self.on_change(initial_text) # covers bug where first key of search wouldn't cause action
        self.show()
        # self.setFocus()

    def deactivate(self):
        self.hide()
        # self.clear()
        self.filterable.show_all()

class FilterableList(QListWidget, Filterable):

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
        # if not self.search_is_active() and event.key() == Qt.Key_Backspace:
        #     self.nav.back()
        #     return
        if event.key() in FilterableList.NAVIGATION_KEYPRESSES:
            QListWidget.keyPressEvent(self, event)
            return

        Filterable.keyPressEvent(self, event)

class BooksPage(Page, FilterableList):

    def __init__(self):
        Page.__init__(self)
        FilterableList.__init__(self)

        # self.set_items(get_book_names())
        self.set_items([c for c in 'abcdefghijklmnopqrstuvwxyz']) # for testing
        self.itemActivated.connect(self.on_book_selected)

    def on_book_selected(self, book_item):
        # book_item is QtListItem
        book = book_item.text()
        # start_loading_book(book)    # file io takes a bit, so start now in other thread

        self.nav.to(ChaptersPage, state=100) # for testing
        # show content
        # if has_chapters(book):
        #     # go to chapter screen
        #     self.nav.to(ChaptersPage, state=get_num_chapters(book))
        # else:
        #     # skip to verses screen
        #     # wait_for_loaded_book()
        #     self.nav.to(VersesPage, state=data.bible[book])


        # widget cleanup
        self.nav.set_title(data.curr_scripture.increment(book))
        self.searchbox.deactivate()
        self.show_all()     # reset any searches when naving back

    def keyPressEvent(self, event):
        if not self.search_is_active() and event.key() == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(data.curr_scripture.decrement())
        else:
            FilterableList.keyPressEvent(self, event)

        # if keypress == ctrl_F:
        #     self.nav.to(SearchResultsPage, state='scope:')

    # def load_state(self, state):
    #     # book names are static so load one time, no need to change
    #     # self.books_data = state
    #     self.list_items = state # book names

class ChaptersPage(Page, FilterableList):

    def __init__(self):
        Page.__init__(self)
        FilterableList.__init__(self)

        self.itemActivated.connect(self.on_chapter_selected)

    def load_state(self, state):
        num_chapters = state
        self.set_items(range(num_chapters))

    def on_chapter_selected(self, chapter_item):

        chapter = chapter_item.text()

        # show the content
        # wait_for_loaded_book()
        # book = data.curr_scripture.book
        # self.nav.to(VersesPage, state=data.bible[book][chapter])
        self.nav.to(VersesPage, state=None)

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

class VersesPage(Page, QTextEdit, FilterableList):

    def __init__(self):
        Page.__init__(self)
        QTextEdit.__init__(self)
        FilterableList.__init__(self)

        # style
        self.setReadOnly(True)
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

    def load_state(self, state):
        verses = state
        # render

    def show_all():
        pass

    def filter_items(self, pattern):
        pass

    def keyPressEvent(self, event):
        if not self.search_is_active() and event.key() == Qt.Key_Backspace:
            self.nav.back()
            self.nav.set_title(data.curr_scripture.decrement())
        else:
            FilterableList.keyPressEvent(self, event)

        # if keypress == ctrl_F:
        #     self.nav.to(SearchResultsPage, state='scope:')



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
