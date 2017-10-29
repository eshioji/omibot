import os
import subprocess

base_dir = os.path.dirname(os.path.realpath(__file__))


def restart():
    with open(os.path.join(base_dir, 'scripts', 'restart.scpt')) as f:
        script = f.read()
        subprocess.check_call(['osascript', '-e', script])


if __name__ == '__main__':
    pass
