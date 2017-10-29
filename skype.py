import os
import subprocess

import config

base_dir = os.path.dirname(os.path.realpath(__file__))


class Skype:
    def __init__(self, skype_contacts):
        self.skype_contacts = skype_contacts

    def start_call(self, name):
        skypeId = config.skype_contacts[name.lower()]
        with open(os.path.join(base_dir, 'scripts', 'start_skype.scpt')) as f:
            template = f.read()
            replaced = template % skypeId
            subprocess.check_call(['osascript', '-e', replaced])


def main():
    skype = Skype(config.skype_contacts)
    skype.start_call('enno')


if __name__ == '__main__':
    main()
