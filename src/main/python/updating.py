'''
app.py

update_url = updating.check_for_update():
if update_url:
    subprocess('updating.py', update_url)   # downloads content and starts app
    app.close()
'''

import sys
import requests
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
import shutil

def check_for_update(curr_version):
    # returns url to files zip if latest version is newer, else False

    # https://docs.github.com/en/rest/reference/repos#releases
    latest_release_url = 'https://api.github.com/repos/wong-justin/fast-bible/releases/latest'
    release_info = requests.get(latest_release_url).json()
    latest_version = release_info['tag_name']
    if not version_greater_than(latest_version[1:],     # strip 'v', like 'v0.2', from github tag
                                curr_version):
        return False

    # testing with all files
    download_url = release_info['zipball_url']

    # real way when partial files asset is uploaded
    # assets = release_info['assets']
    # updated_files_asset = find_obj_where(assets, lambda x:x['name'] == '_updated_files.zip')
    # download_url = updated_files_asset['url']
    # # download_url = updated_files_asset['browser_download_url']    # maybe it's this one?

    return download_url

def version_greater_than(v1, v2):
    print(v1, v2)
    # ('0.12.1', '0.3.1') -> True

    # temp
    # return v1 > v2
    return True

def download_update(url):
    print('hello world')
    print(url)
    return

    outdir = './misc/tmp/'
    # outdir = Path(sys.executable) - filename  # dir of frozen app
    with download_zip(download_url) as zip:
        zip_extract_all(zip, lambda path: outdir / strip_first_folder(path) )

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
