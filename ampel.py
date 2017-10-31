import subprocess
import threading
import time
import traceback

import common
import config


class Ampel:
    def __init__(self, base_command):
        self.base_command = base_command

    def signal(self, order, switchto):
        switch = '1' if switchto else '0'
        cmd = self.base_command + ['-as', str(order), switch]
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)

    def flash(self, duration):
        def do_flash():
            try:
                started = time.time()
                while True:
                    elapsed = time.time() - started
                    if elapsed > duration:
                        [self.signal(x, 0) for x in range(3)]
                        return
                    else:
                        [self.signal(x, 1) for x in range(3)]
                        time.sleep(1)
                        [self.signal(x, 0) for x in range(3)]
            except:
                tb = traceback.format_exc()
                common.error(tb)

        flash_thread = threading.Thread(target=do_flash)
        flash_thread.start()
        return flash_thread

    def check_status(self):
        try:
            out = subprocess.check_output(self.base_command + ['-l'], stderr=subprocess.STDOUT)
            return 0, out
        except subprocess.CalledProcessError as e:
            return e.returncode, e.output



if __name__ == '__main__':
    ampel = Ampel(config.cleware_exec)
    ret, out = ampel.signal(0, 1)
