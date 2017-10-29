import os
import subprocess
import threading
import time

import ampel
import config


def ring(duration):
    def do_beep():
        started = time.time()
        while True:
            elapsed = time.time() - started
            if elapsed > duration:
                return
            else:
                subprocess.check_call(['afplay', config.ring_tone])

    flash_thread = threading.Thread(target=do_beep)
    flash_thread.start()


def say(text):
    os.system('say "%s"' % text)


def main():
    ring(30)
    a = ampel.Ampel(config.cleware_exec)
    a.flash(30)


if __name__ == '__main__':
    main()
