'''
app.py

update_url = updating.check_for_update():
if update_url:
    subprocess('updating.py', update_url)   # downloads content and starts app
    app.close()
'''

from pathlib import Path
import subprocess
import sys

from PyQt5.QtCore import QProcess


# def stop_app():
#     pass

def check_for_update():
    pass
    if self.version < tag_name:
        return download_url
    else:
        return False

def download_update(url):
    print('hello world')
    print(url)



if __name__ == '__main__':
    # if check_for_update():
    # download_update(sys.argv[1])
    download_update('https://something')
    start_app()
