import os
import re
import subprocess

import common

base_dir = os.path.dirname(os.path.realpath(__file__))


def battery_status():
    out = str(subprocess.check_output(['pmset', '-g', 'batt']))
    return int(re.match(r'.*\)\\t([0-9]+)%;.*', out).group(1))


def reset_volume():
    common.run_apple_script('reset_volume.scpt')


if __name__ == '__main__':
    print(battery_status())
