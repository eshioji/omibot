import subprocess

import config


class Ampel:
    def __init__(self, base_command):
        self.base_command = base_command

    def signal(self, order, switchto):
        switch = '1' if switchto else '0'
        cmd = [self.base_command] + ['-as', str(order), switch]
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)

if __name__ == '__main__':
    ampel = Ampel(config.cleware_exec)
    ret, out = ampel.signal(0, 1)
