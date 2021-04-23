
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QColor, QFont, QFontDatabase, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QStackedWidget, QPushButton,
    QLineEdit, QTextEdit, QLabel, QListWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSpacerItem, QAbstractSlider, QDialog, QProgressDialog)

import sys
sys.path.insert(0, 'src/main/python/')

from test_main import *

# from main import ListWidget


def test_scripture_location():
    s = ScriptureLocation()

    # print(s)
    # print(s.increment('Genesis'))
    # print(s.increment('3'))
    # print(s.increment('15'))
    # print(s.decrement())
    # print(s.decrement())
    # print(s.decrement())
    # # print(s.decrement())

    assert str(s) == 'Bible'
    assert str(s.increment('Genesis')) == 'Genesis'
    assert str(s.increment('3')) == 'Genesis 3'
    assert str(s.increment('15')) == 'Genesis 3:15'
    assert str(s.decrement()) == 'Genesis 3'
    assert str(s.decrement()) == 'Genesis'
    assert str(s.decrement()) == 'Bible'


def test_navigation():

    class A(Page, QLabel):
        def __init__(self):
            super().__init__('page A')

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
            super().__init__('page B')

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


    show_widget( lambda: PageManager(A, B, C) )

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
    def f():
        return PageManager(BooksPage, ChaptersPage, VersesPage)

    show_widget(f)

def test_corner_layout():

    class make_filterable(widget_class):
        w = widget_class()
        grid = QGridLayout()
        # grid.addWidget(self, 0, 0)#, Qt.AlignLeft | Qt.AlignTop)
        grid.addWidget(QLabel('label'), 0, 0, Qt.AlignRight | Qt.AlignBottom)
        w.setLayout(grid)

    show_widget(C)


def show_widget(make_widget):
    app = QApplication([])
    w = make_widget()
    w.show()
    app.exec_()
    # exit_code = app.exec_()
    # sys.exit(exit_code)

if __name__ == '__main__':
    # test_navigation()
    # test_key_events()
    # test_filterable()
    test_all_pages()
    # test_corner_layout()
    # test_composed_widget()
    # test_basic_window()
    # show_widget(QWidget)
