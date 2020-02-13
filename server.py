import os
import socket
import threading
import platform
import logging
from config import *
from common import *
from inout  import InOutException
from netapi import NetAPI, save_file

### change save directory here ###
save_dir = {'Windows': 'C:\\temp',
            'Linux':   '/tmp', }
##################################

### change banner here ###
# BANNER = ''
raise NotImplementedError('Set parameters before execution. You can refer to the latest version in appendix')

### Thread functions #####

def receive_thread(conn, addr, path):
    handler     = NetAPI(conn)
    while True:
        try:
            filename = 'Unknown'
            logging.debug('start recv_file()')
            data    = handler.recv_file()
            logging.debug('return from recv_file()')
            if not data:
                logging.debug('receive_thread: no data, break')
                break
            logging.debug('verify data')
            data    = handler.recv_verify(data)
            if not data:
                logging.debug('data imcomplete')
                continue
            filename = os.path.join(path, addr[0])
            logging.debug('save to %s', filename)
            save_file(data, filename)
        except InOutException as e:
            logging.debug('receive_thread: got exception %s', e.args)
        except socket.error as e:
            logging.error('receive_thread: got socket exception %s when receive %s, break', e.args, filename)
            break
        except Exception as e:
            logging.error('receive_thread: got exception: %s when receive %s, break', str(e), filename)
            break
    logging.debug('close connection')
    conn.close()

################
# server start #
################

print(BANNER.decode('utf-8'))
thread_flag  = True  # False if debugging
threads      = []
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(('localhost', 1234, ))
serverSocket.listen(5)

while True:
    conn, addr  = serverSocket.accept()
    logging.debug('send banner')
    conn.send(BANNER + b'\0')
    if thread_flag:
        # thread
        threads = thread_refresh(threads)
        if len(threads) < MAX_CONN:
            thread = threading.Thread(target=receive_thread, \
                                      args=(conn, addr, target_dir,))
            thread.start()
            threads.append(thread)
        else:
            conn.close()
    else:
        receive_thread(conn, addr, target_dir)

serverSocket.close()
