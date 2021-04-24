
from utils import *

import re
import sys
import os

class BooksPage(Page, FilterableList):
    '''Lists books from Gen->Rev and connects to next chapters page.
    First page of application.'''

    def __init__(self):
        Page.__init__(self)
        FilterableList.__init__(self)

        self.set_items(BOOK_NAMES)
        # self.set_items([c for c in 'abcdefghijklmnopqrstuvwxyz']) # for testing
        self.itemActivated.connect(self.on_book_selected)

    def on_book_selected(self, book_item):
        # book_item is QtListItem
        book = book_item.text()
        # show content
        if has_chapters(book):
            # go to chapter screen
            self.nav.to(ChaptersPage, state=get_num_chapters(book))
        else:
            # skip to verses screen
            self.nav.to(VersesPage, state=data.bible[book]) # or get_bible_content(data.curr_scripture.inc(bok))

        # widget cleanup
        self.nav.set_title(data.curr_scripture.inc(book, inplace=True))
        self.searchbox.deactivate()
        self.show_all()     # reset any searches when naving back

    def keyPressEvent(self, event):
        if ctrl_f_event(event):
            self.nav.to(SearchResultsPage, state=lambda: iter_verses_in_whole_bible())
            self.searchbox.deactivate()
        else:
            FilterableList.keyPressEvent(self, event)   # this is 0th page; don't need nav back

class ChaptersPage(Page, FilterableList):
    '''List of chapter numbers 1->n for given book and connects to next verses page.'''

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
        verses = get_bible_content(data.curr_scripture)
        self.nav.to(VersesPage, state=verses)

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
                self.nav.to(SearchResultsPage, state=lambda: scriptures_with_verses(data.curr_scripture, self.verses))
                self.searchbox.deactivate()
                self.verticalScrollBar().setValue(0)    # scroll back to top

        # scroll
        elif keypress in (Qt.Key_Down, Qt.Key_Up):
            QTextEdit.keyPressEvent(self, event)

        # keypress goes to searchbox
        else:
            Filterable.keyPressEvent(self, event)

class SearchResultDelegate(QStyledItemDelegate):
    # custom list item rendering,
    #  mainly just to format a title and subtitle while looking like default list widget item

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
    '''Searches given verses by regex from searchbox and shows matches in list.'''

    def __init__(self):
        self.default_placeholder_msg = 'search regex:'
        Page.__init__(self)
        FilterableList.__init__(self, placeholder=self.default_placeholder_msg)

        self.setItemDelegate(SearchResultDelegate(self))
        # self.itemActivated.connect(self.on_result_item_selected)

        # dummy searchbox serves as visual prompt on empty screen
        #  gives better communication to user
        self.fake_searchbox = SearchBox(None)

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

        # when finished iter and no matches
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

# --- run

if __name__ == '__main__':
    app = QApplication([])
    set_theme(app)

    data.bible = load_bible_json()

    main = MarginParent(PageManager(BooksPage, ChaptersPage, VersesPage, SearchResultsPage))
    main.setWindowTitle('Bible')    # initial title to override fbs default
    main.show()

    # if first time loading app
    if len( os.listdir(BOOK_DIR) ) <= 1: # gitignore takes up space
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
