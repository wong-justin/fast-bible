
from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog)

import sys
sys.path.insert(0, 'src/main/python/')

from utils import *

from timeit import *

def test_scripture():
    s = Scripture()

    assert str(s) == 'Bible'
    assert str(s.inc('Genesis')) == 'Genesis'
    assert str(s.inc('3')) == 'Genesis 3'
    assert str(s.inc('15')) == 'Genesis 3:15'
    assert str(s.dec()) == 'Genesis 3'
    assert str(s.dec()) == 'Genesis'
    assert str(s.dec()) == 'Bible'

def test_navigation():

    class A(Page, QLabel):
        def __init__(self):
            QLabel.__init__(self, 'page A')

        def keyPressEvent(self, event):
            keypress = event.key()

            if keypress == Qt.Key_Return:
                self.nav.to(B, state=None)

            elif keypress == Qt.Key_Up:
                print('A heard UP')

            else:
                Page.keyPressEvent(self, event)

    class B(Page, QLabel):
        def __init__(self):
            QLabel.__init__(self, 'page B')

        def keyPressEvent(self, event):
            keypress = event.key()

            if keypress == Qt.Key_Return:
                self.nav.to(C, state=None)

            elif keypress == Qt.Key_Down:
                print('B heard DOWN')

            else:
                Page.keyPressEvent(self, event)

    class C(Page, QTextEdit):
        # first base class Page means doing Page.keyPressEvent over otherWidget.keyPressEvent
        pass

    class D(QLabel, Page):
        def keyPressEvent(self, event):
            keypress = event.key()

            if keypress == Qt.Key_Left:
                print('D heard LEFT')

            else:
                Page.keyPressEvent(self, event)


    show_widget( lambda: MarginParent(PageManager(A, B, C)) )

def test_basic_window():

    show_widget( lambda: QLabel('label text') )

def test_composed_widget():

    def customListener(event):
        print(event)

    class A:
        def __init__(self):
            self.widget = QLabel('label')
            self.widget.keyPressEvent = customListener

    show_widget( lambda: A().widget )

def test_key_events():

    class Widget(QTextEdit):
        def keyPressEvent(self, event):
            t = event.text()
            # print(f'"{t}", {ord(t)}, {len(t)}, {hex(event.key())}, 0x20')
            # print(event.key())
            # print(event.key() >= Qt.Key_Escape)
            print(t, bool(t))
            super().keyPressEvent(event)

    show_widget(Widget)

def test_filterable():

    def f():
        w = FilterableList()
        w.set_items([str(i) for i in range(100)])

        return w

        print(type(w).__name__)
        print(w.searchbox)

        # main = QWidget()
        # grid = QGridLayout()
        # grid.addWidget(w, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)
        # grid.addWidget(w.searchbox, 0, 0, Qt.AlignRight | Qt.AlignBottom)
        # main.setLayout(grid)
        # return main

    show_widget(f)

def test_all_pages():
    import main

    def f():
        return PageManager(main.BooksPage, main.ChaptersPage, main.VersesPage)

    show_widget(f)

def test_corner_layout():

    def f():
        w = QTextEdit()
        add_grid_child(w, QLabel('botright'), Qt.AlignRight | Qt.AlignBottom)
        add_grid_child(w, QLabel('topleft'), Qt.AlignLeft | Qt.AlignTop, grid=w.layout())
        add_grid_child(w, QLabel('center'), Qt.AlignCenter, grid=w.layout())
        add_grid_child(w, QLabel('topcenter'), Qt.AlignCenter | Qt.AlignTop, grid=w.layout())
        return w

    show_widget(f)

def test_alternate_search_results():
    import main

    class SearchResultsB(main.SearchResultsPage):

        def filter_items(self, search_text):
            super().filter_items(search_text)
            print('subclassed in test')

    show_alternate_classes(SearchResultsPage=SearchResultsB)

def test_search_results_threaded():
    pass

def test_search_results_postpone_items_add():
    pass

def test_iter_performance():
    import utils

    init_data()

    def a():
        for v in utils._iter_verses_in_whole_bible():
            pass

    def b():
        for v in utils.data._all_verses:
            pass
    a()
    def c():
        pass

    _a = timeit(a, number=10)
    _b = timeit(b, number=10)
    print(_a, _b)


def test_search_performance():
    # try a caching decorator! no need to store list maybe or copy iterator
    pass

def test_list_widget_item_adding_performance():

    # class A(QListWidget):
    #     def add(self):
    #         for i in range(1000):
    #             item = QListWidgetItem(self)
    #             item.setData(Qt.DisplayRole, i)
    #             self.addItem(item)

    class A(QListWidget):
        def add(self):
            for i in range(1000):
                item = QListWidgetItem('')
                item.setData(0, i)
                self.addItem(item)

    class B(QListWidget):
        def add(self):
            for i in range(1000):
                item = QListWidgetItem('')
                self.addItem(item)
                item.setData(0, i)

    class C(QListWidget):
        def add(self):
            for i in range(1000):
                item = QListWidgetItem('', self)
                item.setData(0, i)

    # class C(QListWidget):
    #     def add(self):
    #         for i in range(1000):
    #             item = QListWidgetItem(str(i), self)
            # print(self.itemAt(0, 0))

    widgets = [_class() for _class in (C,B,A)]
    methods = [w.add for w in widgets]
    time_methods(*methods, n=10)

    # methods = [w.clear for w in widgets]
    # time_methods(*methods, n=1)



def test_list_widget_items_add():

    # class A(QListWidget):
    #     def add(self):
    #         items = []
    #         for i in range(1000):
    #             items.append(QListWidgetItem(str(i), self))
    #         print(self.itemAt(0, 0))

    class A(QListWidget):
        def add(self):
            for i in range(1000):
                item = QListWidgetItem(str(i), self)
            print(self.itemAt(0, 0))

    def make():
        a = A()
        a.add()
        return a
    show_widget(make)

def time_methods(*fns, n=1):
    results = []
    for fn in fns:
        results.append(timeit(fn, number=n))

    # go backwards in case maybe the order of fns affects things, like caching
    for i in range(len(fns)-1, 0-1, -1):
        fn = fns[i]
        results[i] += timeit(fn, number=n)

    for fn, t in zip(fns, results):
        print(type(fn).__name__, t)

def test_window_sizing():
    # https://gist.github.com/dgovil/d83e7ddc8f3fb4a28832ccc6f9c7f07b

    class W(QDialog):
        def __init__(self):
            super().__init__()

            self.settings = QSettings('Wong', 'test app')
            default = bytes('', encoding='utf-8')
            geometry = self.settings.value('geometry', default)
            self.restoreGeometry(geometry)

        def closeEvent(self, event):
            geometry = self.saveGeometry()
            self.settings.setValue('geometry', geometry)

            super().closeEvent(event)

    show_widget(W)

def test_list_uniform_item_size():
    # conclusion: setUniformItemSizes is not helping

    class A(QListWidget):
        def add(self):
            for i in range(10000):
                item = QListWidgetItem()
                item.setData(0, i)
                self.addItem(item)
            # return self.itemAt(0, 0) is None

    class B(QListWidget):
        def __init__(self):
            super().__init__()
            QListView.setUniformItemSizes(self, True)

        def add(self):
            for i in range(10000):
                item = QListWidgetItem()
                item.setData(0, i)
                self.addItem(item)
            # return self.itemAt(0, 0) is None

    a, b = A(), B()
    time_methods(a.add, b.add)#, n=2)


def test_file_compare():
    import filecmp

    d1 = '../navigating-release/'
    d2 = './target/Fast Bible/'

    cmp = filecmp.dircmp(d1, d2)
    print(cmp.diff_files)



def show_alternate_classes(**kwargs):

    import main

    for old_name, new_class in kwargs.items():
        setattr(main, old_name, new_class)

    def BasicApp():
        init_data()
        classes = [getattr(main, c) for c in ('BooksPage', 'ChaptersPage', 'VersesPage', 'SearchResultsPage')]
        # p = PageManager(BooksPage, ChaptersPage, VersesPage, main.SearchResultsPage)
        p = PageManager(*classes)
        return MarginParent(p)
    show_widget(BasicApp)

def show_widget(make_widget):
    app = QApplication([])
    w = make_widget()
    w.show()
    app.exec_()
    # exit_code = app.exec_()
    # sys.exit(exit_code)

if __name__ == '__main__':
    test_file_compare()
    # test_list_uniform_item_size()
    # test_window_sizing()
    # test_list_widget_item_adding_performance()
    # test_list_widget_items_add()
    # test_iter_performance()
    # test_alternate_search_results()
    # test_navigation()
    # test_key_events()
    # test_composed_widget()
    # test_corner_layout()
    # test_basic_window()
    # show_widget(QWidget)
