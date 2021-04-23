from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog)

from book_logic import *
from constants import appctxt

import re
import ctypes
import sys
import time
import os

# book names or chapters - list
# verses / chapter content - text (even JW font?)
# backspace - back a screen
# alhpanumeric - open search box
#   search box for book names or chapters - just narrow list
#   for verses / chapter content - go to verse in middle of screen? or just isolate verse
#
# parsing -
#   download zip from jw link: https://download-a.akamaihd.net/files/media_publication/57/nwt_E.rtf.zip
#       https://www.jw.org/en/library/bible/  (nwt '13, NOT study-bible, rtf)
#   unzip
#   parsing.py to strip unneccesary text
#   put into plaintext files
#       Remove backtick accents? (`) bad formatting in notosans and hurts potential searches
#   then delete rtf
#   result:
#   ./data
#       |__ books*.txt
# (package with this preparsed already? faster and no need for urlopen import but maybe less trustworthy)

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

    # custom font

    font_db = QFontDatabase()
    # font_db.addApplicationFont('../assets/Noto_Serif/NotoSerif-Regular.ttf')
    # font_db.addApplicationFont('../resources/assets/Noto_Sans/NotoSans-Regular.ttf')
    font_db.addApplicationFont(appctxt.get_resource('assets/Noto_Sans/NotoSans-Regular.ttf'))
    # font = QFont('Noto Serif')
    font = QFont('Noto Sans')
    font.setPointSize(10)
    app.setFont(font)

    # # icon
    # icon = QIcon()
    # # icon.addFile('../resources/assets/icon4.ico')
    # icon.addFile(appctxt.get_resource('assets/icon4.ico'))
    #     # something hacky for windows to show icon in taskbar
    # myappid = 'biblenavigation.myapp' # arbitrary string
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    #
    # app.setWindowIcon(icon)

class NavStack(QStackedWidget):
    # going forward or back between main widget screens

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.skip = 1

    def nav_forward(self):
        i = self.currentIndex() + self.skip
        if i < self.count():
            self.setCurrentIndex(i)

    def nav_backward(self):
        i = self.currentIndex() - self.skip
        if i >= 0:
            self.setCurrentIndex(i)

            main.decrement_title()

    def set_skip(self, on=True):
        # turn on to move by 2 pages.
        # used for chapterless book to skipping middle chapter screen
        self.skip = 2 if on else 1

class Filterable:
    # Abstract class to implement to react to searchbox filtering your items.
    # Uses self.all_items, an iterable.
    # Need to implement show_items(items) and maybe filter_items(search_text)

    # reserved for this widget to nagivate items
    keys = {Qt.Key_Up,
            Qt.Key_Down,
            Qt.Key_Left,
            Qt.Key_Right,
            Qt.Key_Return}

    def set_items(self, items):
        self.all_items = items
        self.show_all()

    def show_all(self):
        self.show_items(self.all_items)

    def show_items(self, items):
        # to implement
        pass

    def filter_items(self, search_text):
        # basic is show regex matches, but probably should override
        # search_key = lambda x:re.search(search_text, x)
        # self.show_items( filter(self.all_items, search_key) )

        self.show_items( index_first_search(self.all_items, search_text) )

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

class ListWidget(QListWidget, Filterable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # styling
        # self.setFlow(QListWidget.LeftToRight)
        # self.setResizeMode(QListWidget.Adjust)
        # self.setGridSize(QSize(30, 30))
        # # self.setSpacing(10)
        # self.setViewMode(QListWidget.IconMode)
        #             # width: 30px;
        #             # height: 30px;
        # self.setStyleSheet('''
        # QListWidget::item {
        #     margin: 2px;
        #     background-color: lightgrey;
        # }
        # QListWidget::item::selected {
        #     background-color: white;
        #     color: black;
        # }
        # QListView {
        #     outline: 0;
        # }
        # ''')

    def keyPressEvent(self, event):
        # do all the things the widget normally does, excluding searchbox activation keys
        # if SearchBox.is_searchable_char(event.text()):
        #     event.ignore()
        # else:
        #     super().keyPressEvent(event)

        # print(True if event.text() else False, event.text(), len( event.text() ))

        if event.key() in Filterable.keys:
            super().keyPressEvent(event)
        else:
            event.ignore()

    # def filter_items(self, pattern):
    #     filtered = [o for o in self.all_items
    #                 if re.search(pattern, o.lower()) or
    #                 re.search(pattern, o.lower().replace(' ', ''))]
    #     # filtered_options = [o for o in self.all_options if pattern in o]
    #     # for o in self.all_options:
    #     #     print(o, re.match(pattern, o))
    #     self.show_items(filtered)
    #
    #
    #     self.show_items( index_first_search(self.all_items, search_text) )

    def show_items(self, items):
        self.clear()
        self.insertItems(0, items)
        self.setCurrentRow(0)

class TextArea(QTextEdit, Filterable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setReadOnly(True)
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

        # maybe make line spacing a little bigger?


        text_color = self.palette().color(QPalette.Text)
        r,g,b,_ = text_color.getRgb()
        self.OPACITY_TEMPLATE = f'<span style="color:rgba({r}, {g}, {b}, 0.5);">{{}}</span>'

    def keyPressEvent(self, event):
        # do all the things the widget normally does, excluding searchbox activation keys
        # if SearchBox.is_searchable_char(event.text()):
        #     event.ignore()
        # else:
        #     super().keyPressEvent(event)

        if event.key() in Filterable.keys:
            super().keyPressEvent(event)
        else:
            event.ignore()

    def filter_items(self, pattern):

        # self.find(pattern)    # old naive search but move cursor

        # make sure the verse is there

        if not pattern.isdigit():
            self.show_all()
            return

        v = int(pattern)
        v_next = v + 1

        match = re.search(num_template.format(v), data.current_text)
        if not match:
            self.show_all()
            return

        # isolate verse position

        start = match.start()
        end = len(data.current_text)
        next_match = re.search(num_template.format(v_next), data.current_text)
        if next_match:
            end = next_match.start()

        # highlight the verse

        verse = self.highlight_between(data.current_text, start, end)

        # start in textedit is plaintext, different from existing start

        # self.ensureCursorVisible()
        plain_verse = to_plain_text(verse)
        # plain_start = re.search(plain_verse, self.toPlainText()).start()
        plain_start = self.toPlainText().index(plain_verse)
        c = self.textCursor()
        c.setPosition(plain_start)
        self.setTextCursor(c)

        # scroll to beginning of verse

        rect = self.cursorRect()
        top = rect.top()
        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.value() + top)   # top of verse is top of screen
        if not vbar.value() == vbar.maximum():  # last verse should stay maximum scroll, else hiding last line
            vbar.triggerAction(QAbstractSlider.SliderSingleStepSub) # but content looks nicer when not pinned to top


    def show_all(self):
        # overriding to just show all normal text, no highlights
        self.set_html(data.current_text)

    def set_html(self, html):
        # wrapping textEdit.setHtml to keep scroll position
        scroll_pos = self.verticalScrollBar().value()
        self.setHtml(html)   # this resets scroll
        self.verticalScrollBar().setValue(scroll_pos)

    def highlight_between(self, html, start, end):
        # make everything translucent besides text[start:end]

        pre  = html[:start]
        main = html[start:end]
        post = html[end:]

        opacity_template = self.OPACITY_TEMPLATE #'<span style="color:rgba(222, 226, 247, 0.5);">{}</span>'    # hard coded from theme for now

        highlighted_text = (self.OPACITY_TEMPLATE.format(pre) +
                            main +
                            self.OPACITY_TEMPLATE.format(post))

        self.set_html(highlighted_text)
        return main

def to_plain_text(html):
    # imitating textedit.toPlainText to find substring positions
    replaced = html.replace('\xa0', ' ').replace('\n', ' ')
    tagless = ''.join( strip_tags(replaced) )
    return tagless

def strip_tags(html):
    # helping to_plain_text
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

class Main(QWidget):
    # final show widget, for things like set windowtitle,
    # and also captures keypresses
    #   maybe us QShortcut for general nav instead of awakardly capturing here?
    #   QtGui.QShortcut(QtCore.Qt.Key_Backsapce, widget, function)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Title
        self.scripture_components = [] # book, chapter, verse
        self.show_title()

    def keyPressEvent(self, event):

        keypress = event.key()
        char = event.text()

        if not searchbox.isVisible():
            if keypress == Qt.Key_Backspace:
                # go back in stack
                stack.nav_backward()

            elif SearchBox.is_searchable_char(char):
                searchbox.activate(char)

        else:
            if keypress == Qt.Key_Escape:
                searchbox.deactivate()
            else:
                searchbox.keyPressEvent(event)

    def increment_title(self, book=None, chapter=None, verse=None):
        # they're going to add the next one that makes sense and take away properly,
        # so no need to validate. Just
        self.scripture_components.append(book or chapter or verse)
        self.show_title()

    def decrement_title(self):
        self.scripture_components.pop(-1)
        self.show_title()

    def show_title(self):
        template = {
            0: 'Bible',
            1: '{}',
            2: '{} {}',
            3: '{} {}:{}'
        }[ len(self.scripture_components) ]

        self.setWindowTitle(template.format(*self.scripture_components))

class SearchBox(QLineEdit):

    def is_searchable_char(c):
        # if char will be used by searchbox
        return c.isalnum() or c == ' '

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        self.textChanged.connect(self.on_change)

    def on_change(self, text):

        if not text:  # cleared
            self.deactivate()
            screen = stack.currentWidget()
            screen.show_all()
        else:
            # narrow current list
            pattern = text
            screen = stack.currentWidget()
            screen.filter_items(pattern)
            # print(text)

    def activate(self, initial_text):
        self.setText(initial_text)
        self.on_change(initial_text) # covers bug where first key of search wouldn't cause action
        self.show()
        # self.setFocus()

    def deactivate(self):
        self.hide()
        # self.clear()
        stack.currentWidget().show_all()

app = QApplication([])
set_theme(app)

# --- Create all widgets used in app
text_screen = TextArea()
books_screen = ListWidget()
chapters_screen = ListWidget()
searchbox = SearchBox()
stack = NavStack()
main = Main()

# --- User actions and interactions between widgets, data
init_data()

def list_chapters_for(book):
    n = get_num_chapters_for(book)
    nums = [str(i) for i in range(0+1, n+1)]
    chapters_screen.set_items(nums)

def on_book_selected(book_item):
    book = book_item.text()
    start_loading_book(book)    # file io takes a bit, so start now in other thread

    if has_chapters(book):
        # go to chapter screen
        list_chapters_for(book)
        stack.set_skip(False)   # could still be true from previous book
        stack.nav_forward()
    else:
        stack.set_skip(True)    # skip chapter screen
        # show the content
        wait_for_loaded_book()
        verses = get_current_book()
        display_verses(verses)

    # widget cleanup
    main.increment_title(book)
    searchbox.deactivate()
    books_screen.show_all()     # reset any searches when naving back

def on_chapter_selected(chapter_item):
    chapter = chapter_item.text()

    # show the content
    wait_for_loaded_book()
    verses = get_chapter(chapter)
    display_verses(verses)

    # widget cleanup
    main.increment_title(chapter)
    searchbox.deactivate()
    chapters_screen.show_all()  # reset any searches when naving back

num_template = '<b>{}</b>\xa0\xa0'
def display_verses(verses):
    # data.current_text = '\xa0\xa0'.join( f'<b>{n}</b>\xa0\xa0{v}' for n,v in verses.items() )
    data.current_text = '\xa0\xa0'.join( num_template.format(n) + v for n,v in verses.items() )
    # data.current_text = '  '.join( num_template.format(n) + v for n,v in verses.items() )
    text_screen.setHtml(data.current_text) # reset scroll to top
    # text_screen.set_items([]) # placeholder for now; should probably pass something about verses + locations
    stack.nav_forward()

books_screen.set_items(get_book_names())
books_screen.itemActivated.connect(on_book_selected)
chapters_screen.itemActivated.connect(on_chapter_selected)

# --- Grouping widgets for show
stack.addWidget(books_screen)
stack.addWidget(chapters_screen)
stack.addWidget(text_screen)

grid = QGridLayout()
grid.addWidget(stack, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)
grid.addWidget(searchbox, 0, 0, Qt.AlignRight | Qt.AlignBottom)
# grid.setContentsMargins(0,0,0,0)
grid.setContentsMargins(2,2,2,2)
main.setLayout(grid)

# --- run
if __name__ == '__main__':

    # main.setWindowFlag(Qt.WindowContextHelpButtonHint, True)
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
