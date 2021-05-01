
from utils import *

from fbs_runtime.application_context import cached_property
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from fbs_runtime import _frozen, _source
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QProcess, QSettings
import requests

from pathlib import Path
from threading import Thread
import os
import sys
from io import BytesIO
from zipfile import ZipFile
import shutil
import subprocess

class AutoUpdatingApp(QApplication):
    '''Minimum auto update functionality.
    Needs updated files in latest release zipped at download url
    and updated version string fetchable to compare to current version.
    Does:
        - solve issue of replacing current executable by downloading files to tmp,
        then moving/replacing files after app close
        - make update effective next app session
    Does not:
        - notify user or give user options
        - update a session that never ends, ie check for update after some time
        - necessarily update an app more than one version behind latest
        - handle possible race conditions, eg. reopening app before apply_update finishes
        - handle errors'''

    def download_update(self):
        # new update has been confirmed, so download files from previously set url
        updates_dir = Path('./updates')
        updates_dir.mkdir(exist_ok=True)

        with download_zip(self.download_url) as _zip:
            unzip(_zip, updates_dir)

    def check_for_update(self):
        # if newer version exists, sets download url and returns True
        # https://docs.github.com/en/rest/reference/repos#releases

        latest_release_url = 'https://api.github.com/repos/wong-justin/fast-bible/releases/latest'  # my repo wong-justin/fast-bible
        release_info = requests.get(latest_release_url).json()
        latest_ver = parse_github_version_tag( release_info['tag_name'] )
        current_ver = BUILD_SETTINGS['version']

        if not version_greater_than(latest_ver, current_ver):
            return False

        # real way when partial files asset is uploaded
        assets = release_info['assets']   # list of objs
        updated_files_asset = find_obj_where(assets, lambda x:x['name'] == 'updated_files.zip') # must be named this during release
        # if not updated_files_asset:
        #     return False

        self.download_url = updated_files_asset['browser_download_url']
        return True

    def apply_update(self):
        # called right before sys.exit()
        subprocess.Popen(windows_move_script, shell=True, close_fds=True)
        # QProcess.startDetached(windows_move_script, [])   # alternative, I think it works

    def download_new_release_if_available(self):
        # called in separate thread to avoid blocking gui
        if self.check_for_update():
            self.download_update()
            self.settings.setValue('updated', True)  # signal to future me

    def run(self):
        exit_code = self.exec_()
        self.quit()
        sys.exit(exit_code)
    ### --- overriding QApplication methods

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = QSettings( str(RESOURCE_DIR / 'settings.ini'), QSettings.IniFormat)  # I can specify the location
        # self.settings = QSettings('FastBible', 'FastBible')   # alternative, saved in some OS specific location

    def exec_(self):
        # check for updates, then run as normal
        if self.settings.value('updated', defaultValue=False):    # from last session
            # self.show_update_notes()  # example of when to notify user
            self.settings.setValue('updated', False)
        Thread(target=self.download_new_release_if_available).start()
        super().exec_()

    def quit(self):
        print('about to quit')
        # apply update if exists, then quit as normal
        if self.settings.value('updated', defaultValue=False):
            self.apply_update()
        super().quit()


# this is called after new executable is downloaded into tmp
#  and old main executable is done running
windows_move_script = (
    # pause to make sure the app is finished closing
    r'timeout /t 2 & ' + # more accurate pause: powershell -nop -c "& {sleep -m 1000}"
    # copy new files into main dir, overwriting existing files and including new subdirs
    r'cd updates & xcopy * ..\ /e /y & ' +
    # r'move %~dp0\updates\* %~dp0\ '   # %~dp0 is dir containing this script
    # r'move "%~dp0\tmp\Fast Bible.exe" "%~dp0\Fast Bible.exe"'

    # cleanup: delete tmp dir
    r'cd ..\ & rmdir /s %cd%\updates\*'
    # 'echo %cd%\*'
    # r'rmdir /s /q %cd%\* & del %cd%\* & echo done'
    # r'rmdir /s /q/ "*" /y & del "*" /y & echo done'
    # r'cd ..\ & rmdir /s /q/ .\updates'
)

# maybe subclass appctx to not have to instantiate app? EDIT: nvm, impossible, as QObject the QApplication must be instantiated
# class MyAppContext(fbs.runtime.ApplicationContext):

# alternative to fbs app context, which needs early instantiation and creates weird dependencies and whatnot

IS_FROZEN = not Path(sys.executable).name == 'python.exe'   # else it would be MyApp.exe in target
_source.project_dir = Path.cwd()

RESOURCE_DIR = Path(sys.executable).parent if IS_FROZEN else _source.project_dir / 'src/main/resources/base/'
RES_DIR = str(RESOURCE_DIR)
BUILD_SETTINGS = _frozen.BUILD_SETTINGS if IS_FROZEN else _source.load_build_settings(_source.project_dir)# json.load(Path.cwd() / 'src/build/settings/base.json')

BOOK_DIR = RESOURCE_DIR / 'data/cleaned'
BOOK_FP_TEMPLATE = str(BOOK_DIR / '{}.json')



class MyAppContext(ApplicationContext):
    @cached_property
    def app(self):
        return AutoUpdatingApp(sys.argv)

# appctxt = MyAppContext()

def read_csv(fp):
    '''Returns list of chunks per line'''
    with open(fp, 'r') as file:
        line = file.readline()
        while line:
            yield line.split(',')
            line = file.readline()

CHAPTER_COUNTS = {
    book_name: int(count)
    for book_name, count in read_csv(RESOURCE_DIR / 'data/chapter_counts.csv')
    # for book_name, count in _read_csv('../resources/data/chapter_counts.csv')
}
# CHAPTER_COUNTS = {'Zephaniah': 3, 'Haggai': 2, 'Zechariah': 14, 'Malachi': 4, 'Matthew': 28, 'Mark': 16, 'Luke': 24, 'John': 21, 'Acts': 28, 'Romans': 16, '1 Corinthians': 16, '2 Corinthians': 13, 'Galatians': 6, 'Ephesians': 6, 'Philippians': 4, 'Colossians': 4, '1 Thessalonians': 5, '2 Thessalonians': 3, '1 Timothy': 6, '2 Timothy': 4, 'Titus': 3, 'Philemon': 1, 'Hebrews': 13, 'James': 5, '1 Peter': 5, '2 Peter': 3, '1 John': 5, '2 John': 1, '3 John': 1, 'Jude': 1, 'Revelation': 22}
BOOK_NAMES = list(CHAPTER_COUNTS.keys())

RESTART_EXIT_CODE = 2


### --- helpers
def read_csv(fp):
    '''Returns list of chunks per line'''
    with open(fp, 'r') as file:
        line = file.readline()
        while line:
            yield line.split(',')
            line = file.readline()

def download_zip(url):
    # returns ZipFile of http response from download url
    response = requests.get(url)
    filelike = BytesIO(response.content)
    return ZipFile(filelike)

def unzip(_zip, _dir):
    # extract files from ZipFile
    for info in _zip.filelist:
        outpath = _dir / strip_first_folder(info.filename)    # rid that redundant folder in zip files
        # yield str(outpath)

        # try:
        if info.is_dir():
            outpath.mkdir(exist_ok=True)
        else:
            source_file = _zip.open(info.filename)
            target_file = open(outpath, 'wb')   # overwrites
            shutil.copyfileobj(source_file, target_file)
    # yield 'finished'

def strip_first_folder(path):
    p = Path(path)
    return Path(*p.parts[1:])

def parse_github_version_tag(s):
    # convention has it prefixed with 'v', like 'v0.1.2', so strip it
    return s[1:]

def version_greater_than(v1, v2):
    # compare strings
    # ('0.12.1', '0.3') -> True
    # ('0.4', '0.1.1') -> False
    for a,b in zip(split_ints(v1), split_ints(v2)):
        pass


    # temp
    # return v1 > v2
    return True

def split_ints(s, sep='.'):
    return (int(i) for i in s.split(sep))

def find_obj_where(objects, key_fn):
    for obj in objects:
        if key_fn(obj):
            return obj
