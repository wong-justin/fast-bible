'''Shared constants, and also an appctxt needed in multiple places.'''

from utils import *
# print(dir(utils))
import updating

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from fbs_runtime.application_context import is_frozen
from PyQt5.QtCore import Qt, QProcess, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog, QMessageBox, QPushButton

from pathlib import Path
import sys
import requests
from time import sleep
from threading import Thread
import os

def _read_csv(fp):
    '''Returns list of chunks per line'''
    with open(fp, 'r') as file:
        line = file.readline()
        while line:
            yield line.split(',')
            line = file.readline()

class MyAppContext(ApplicationContext, QObject):
    # wraps main widget with meta-functions like restarting and updating
    # extends QObject for sake of having slots
    # has slot for sake of initiating gui update from worker thread

    update_available = pyqtSignal()
    download_finished = pyqtSignal()

    def __init__(self, *args, **kwargs):
        ApplicationContext.__init__(self, *args, **kwargs)
        QObject.__init__(self)

        self.update_available.connect(self.ask_to_update)

    def run(self, main, title):

        self.main = main
        main.setWindowTitle(title)
        main.show()

        Thread(target=self.check_for_update).start()

        if _first_time_running_app():
            self.show_downloading_bible()

        exit_code = self.app.exec_()

        # app is closed and told to restart
        if exit_code == RESTART_EXIT_CODE:
            self.run_app_in_new_process()
            exit_code = 0

        sys.exit(exit_code)

    def run_app_in_new_process(self):
        # used to restart after downloading updated executable app, but also work when built from source
        # if is_frozen(): # running compiled app
        exe = sys.executable   # Fast Bible.exe in target
        args = []
        # testing
        # exe = sys.executable   # python.exe
        # args = [str(Path.cwd() / 'src/main/python/main.py')]
        QProcess.startDetached(exe, args)

    def check_for_update(self):
        # done in worker thread to prevent http time from blocking gui
        if updating.check_for_update(self.build_settings['version']):
            self.update_available.emit()

        # testing
        # sleep(2)
        # self.update_signal.emit('https://some_url')

    def ask_to_update(self):

        # new way, choice to restart
        curr = updating.info['v_curr']
        latest = updating.info['v_latest']
        title = 'Update'
        text = 'FastBible has been updated! Download now?'
        details = f'Version {curr} -> {latest}'#\n changelog')
        on_accept = self.show_downloading_update

        ChoiceDialog(title, text, details, on_accept, parent=self.main).show()

    def show_downloading_update(self):
        dialog = DownloadDialog('Updating', '', (0,1), self.main)
        dialog.show()

        # download http request blocks gui, so do that in main thread as first part of progress
        # then unzip result (which is pretty fast) as last part of progress
        def download():
            # sleep(3)    # testing
            updating.download_update()  # real
            self.download_finished.emit()

        def on_download_finished():
            # dialog.setMaximum(updating.info['num_files'])
            # dialog.setMaximum(100)  # testing
            i = 1
            for filename in updating.extract_progress_iterator():
            # for filename in range(10000): # testing
                # filename = str(filename) + 'abcdefghkljaslkdaasjdakjsd'   # testing
                # dialog.setLabelText(_quick_elide(filename))
                dialog.setLabelText(filename)   # testing; full looks ugly
                dialog.setValue(i)
                i += 1

            dialog.close()

            # wait for user to acknowledge to restart
            AcknowledgeDialog('Updating',
                              'Finished. Restart to take effect.',
                              on_accept=lambda:self.app.exit(RESTART_EXIT_CODE),
                              parent=self.main).show()
            # old way: not really cancelling, just using default button signal from progress dialog to show user when done
            # dialog.canceled.connect(lambda:self.app.exit(RESTART_EXIT_CODE)) # restart when done
            # dialog.setCancelButton(QPushButton('Ok', dialog))
            # dialog.setLabelText('Update finished.\nRestart to take effect.')

        dialog.setLabelText('Downloading files..')
        self.download_finished.connect(on_download_finished)
        Thread(target=download).start()

    def show_downloading_bible(self):
        dialog = DownloadDialog('Downloading the Bible',
                                'fetching from jw.org...',
                                (0, 66), self.main)
        dialog.show()

            # probably should catch errors here
        import setup
        i = 1
        for book_name in setup.main_progress_iterator():
            dialog.setLabelText(book_name)
            dialog.setValue(i)
            i += 1
        dialog.close()  # become normal app; main window focused

def _first_time_running_app():
    return len( os.listdir(BOOK_DIR) ) <= 1

def _quick_elide(long_str):
    if len(long_str) < 20 + 3:
        return long_str
    return long_str[:20] + '...'

class DownloadDialog(QProgressDialog):
    # config dialog to block main window until progress finished
    def __init__(self, title, label='', _range=(0,0), parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setRange(*_range)
        self.setCancelButton(None)
        self.setWindowTitle(title)
        self.setLabelText(label)
        self.setModal(True)
        self.setMinimumDuration(0)

class ChoiceDialog(QMessageBox):
    # convenience for an ok/cancel dialog
    def __init__(self, title='', text='', subtext='', on_accept=lambda:None, on_reject=lambda:None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(text)
        self.setDetailedText(subtext)
        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel);
        self.setDefaultButton(QMessageBox.Ok);
        self.on_accept = on_accept
        self.on_reject = on_reject

    def show(self):
        clicked = self.exec()
        if clicked == QMessageBox.Ok:
            self.on_accept()
        else:
            self.on_reject()

class AcknowledgeDialog(QMessageBox):
    # only one option and callback, but still notifies user
    def __init__(self, title='', text='', on_accept=lambda:None, on_reject=lambda:None, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowTitle(title)
        self.setText(text)
        self.setStandardButtons(QMessageBox.Ok);
        self.on_accept = on_accept

    def show(self):
        self.exec()
        self.on_accept()

appctxt = MyAppContext()
# print(appctxt.build_settings)

RES_DIR = appctxt.get_resource('./')
BOOK_DIR = appctxt.get_resource('data/cleaned/')
BOOK_FP_TEMPLATE = BOOK_DIR + '/{}.json'

CHAPTER_COUNTS = {
    book_name: int(count)
    for book_name, count in _read_csv(appctxt.get_resource('data/chapter_counts.csv'))
    # for book_name, count in _read_csv('../resources/data/chapter_counts.csv')
}
# CHAPTER_COUNTS = {'Zephaniah': 3, 'Haggai': 2, 'Zechariah': 14, 'Malachi': 4, 'Matthew': 28, 'Mark': 16, 'Luke': 24, 'John': 21, 'Acts': 28, 'Romans': 16, '1 Corinthians': 16, '2 Corinthians': 13, 'Galatians': 6, 'Ephesians': 6, 'Philippians': 4, 'Colossians': 4, '1 Thessalonians': 5, '2 Thessalonians': 3, '1 Timothy': 6, '2 Timothy': 4, 'Titus': 3, 'Philemon': 1, 'Hebrews': 13, 'James': 5, '1 Peter': 5, '2 Peter': 3, '1 John': 5, '2 John': 1, '3 John': 1, 'Jude': 1, 'Revelation': 22}
BOOK_NAMES = list(CHAPTER_COUNTS.keys())

RESTART_EXIT_CODE = 2