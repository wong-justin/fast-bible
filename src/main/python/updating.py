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

def start_app():
    script = Path.cwd() / 'src/main/python/main.py'
    print(sys.executable)
    p = subprocess.Popen([sys.executable, str(script)], shell=True)#, close_fds=True)
    exit_code = p.wait()
    sys.exit(exit_code)


if __name__ == '__main__':
    # if check_for_update():
    download_update(sys.argv[1])
    start_app()
