'''
app.py

if updating.check_for_update():
    updating.update()

# or in more steps
if updating.check_for_update():
    updating.download_update()
    for filename in extract_progress_iterator():
        pass
'''

import sys
import requests
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
import shutil

# version and download information exposed to global
info = dict()

def check_for_update(curr_version):
    # returns url to files zip if latest version is newer, else False

    # https://docs.github.com/en/rest/reference/repos#releases
    latest_release_url = 'https://api.github.com/repos/wong-justin/fast-bible/releases/latest'
    release_info = requests.get(latest_release_url).json()
    latest_version = release_info['tag_name'][1:]     # strip 'v', like 'v0.2', from github tag

    info['v_curr'] = curr_version
    info['v_latest'] = latest_version
    if not version_greater_than(latest_version,
                                curr_version):
        return False

    # testing with all files
    download_url = release_info['zipball_url']

    # real way when partial files asset is uploaded
    # assets = release_info['assets']   # list of objs
    # updated_files_asset = find_obj_where(assets, lambda x:x['name'] == '_updated_files.zip')
    # download_url = updated_files_asset['url']
    # # download_url = updated_files_asset['browser_download_url']    # maybe it's this one?

    info['download_url'] = download_url
    return True

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

def update():
    # all in one, after check_for_update() was called and set url
    url = info['download_url']
    print(f'downloading from {url}')

    outdir = './misc/tmp/'
    # outdir = Path(sys.executable) - filename  # dir of frozen app
    with download_zip(url) as zip:
        zip_extract_all(zip, lambda path: outdir / strip_first_folder(path) )

def download_update():
    # download and set result in global
    url = info['download_url']
    zip = download_zip(url)
    info['zip'] = zip
    info['num_files'] = len(zip.filelist)

def extract_progress_iterator():
    # incremental version
    # for filename in extract_progress_iterator:
    #   progress += 1

    outdir = './misc/tmp/'
    with info['zip'] as zip:
        yield from zip_extract_all_iter(zip, lambda path: outdir / strip_first_folder(path) )

def zip_extract_all_iter(zip, modify_path):
    # incrementally update caller with filename being extracted

    for info in zip.filelist:
        yield info.filename
        outpath = modify_path(info.filename)

        if info.is_dir():
            outpath.mkdir(exist_ok=True)
        else:
            source_file = zip.open(info.filename)
            target_file = open(outpath, 'wb')   # overwrites
            shutil.copyfileobj(source_file, target_file)
    yield 'finished'


def download_zip(url):
    # returns ZipFile of http response

    response = requests.get(url)
    filelike = BytesIO(response.content)
    return ZipFile(filelike)

def zip_extract_all(zip, modify_path):
    # extract each file in zip to path given by modify_path(file.path)
    # overwrites existing files
    # cusotmizable alternative to zip.extractall()

    for info in zip.filelist:

        outpath = modify_path(info.filename)

        if info.is_dir():
            outpath.mkdir(exist_ok=True)
            continue
        else:
            source_file = zip.open(info.filename)
            target_file = open(outpath, 'wb')   # overwrites
            shutil.copyfileobj(source_file, target_file)

def strip_first_folder(path):
    p = Path(path)
    return Path(*p.parts[1:])

def find_obj_where(objects, key_fn):
    for obj in objects:
        if key_fn(obj):
            return obj


# if __name__ == '__main__':
#     # if check_for_update():
#     # download_update(sys.argv[1])
#     download_update('https://something')
#     start_app()
