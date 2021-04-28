'''Shared constants, and also an appctxt needed in multiple places.'''

from fbs_runtime.application_context.PyQt5 import ApplicationContext
from fbs_runtime.application_context import is_frozen

from PyQt5.QtCore import Qt, QProcess, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QProgressDialog

from pathlib import Path
import sys
import requests
from time import sleep
from threading import Thread
import os

from utils import *

def _read_csv(fp):
    '''Returns list of chunks per line'''
    with open(fp, 'r') as file:
        line = file.readline()
        while line:
            yield line.split(',')
            line = file.readline()

class MyAppContext(ApplicationContext, QObject):

    update_signal = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        ApplicationContext.__init__(self, *args, **kwargs)
        QObject.__init__(self)

        self.update_signal.connect(self.show_downloading_update)

    def run(self, main, title):

        self.main = main
        main.setWindowTitle(title)
        main.show()

        Thread(target=self.check_for_update).start()

        if _first_time_running_app():
            show_downloading_bible(main)

        exit_code = appctxt.app.exec_()

        # app is closed and told to restart
        if exit_code == RESTART_EXIT_CODE:
            self.run_app_in_new_process()
            exit_code = 0

        sys.exit(exit_code)

    def run_app_in_new_process(self):
        # used to restart after downloading updated executable app, but also work when built from source
        if is_frozen(): # running compiled app
            exe = sys.executable   # Fast Bible.exe in target
            args = []
        else:           # running from source
            exe = sys.executable   # python.exe
            args = [str(Path.cwd() / 'src/main/python/main.py')]
        QProcess.startDetached(exe, args)

    def check_for_update(self):
        # url = _check_for_update(self.build_settings['version'])
        # if url:
        #     self.update_signal.emit(url)

        # testing
        sleep(2)
        self.update_signal.emit('https://some_url')

    def show_downloading_update(self, download_url):
        dialog = DownloadDialog('App Update', '', (0,66), self.main)
        dialog.show()

        # testing
        sleep(5)

        # outdir='./misc/tmp/'
        # with download_zip(download_url) as zip:
        #     zip_extract_all(zip, lambda path: outdir / strip_first_folder(path) )
        dialog.close()

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

def _check_for_update(curr_verison):
    # https://docs.github.com/en/rest/reference/repos#releases
    latest_release_url = 'https://api.github.com/repos/wong-justin/fast-bible/releases/latest'
    release_info = requests.get(latest_release_url).json()
    latest_version = release_info['tag_name']
    if not version_greater_than(latest_version, curr_version):
        return

    # testing with all files
    download_url = release_info['zipball_url']

    # real way when partial files asset is uploaded
    # assets = release_info['assets']
    # updated_files_asset = find_obj_where(assets, lambda x:x['name'] == '_updated_files.zip')
    # download_url = updated_files_asset['url']
    # # download_url = updated_files_asset['browser_download_url']    # maybe it's this one?

    print(version, download_url)


def version_greater_than(v1, v2):
    # ('0.12.1', '0.3.1') -> True

    # temp
    return v1 > v2

appctxt = MyAppContext()
print(appctxt.build_settings)

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
