import os
import subprocess

import config

base_dir = os.path.dirname(os.path.realpath(__file__))


class Skype:
    def __init__(self, skype_contacts):
        self.skype_contacts = skype_contacts

    def lookup(self, name):
        return config.skype_contacts[name.lower()]

    def start_call(self, name):
        skypeId = config.skype_contacts[name.lower()]
        with open(os.path.join(base_dir, 'scripts', 'start_skype_call.scpt')) as f:
            template = f.read()
            replaced = template % skypeId
            return subprocess.check_call(['osascript', '-e', replaced])

    def reset(self):
        with open(os.path.join(base_dir, 'scripts', 'reset_skype.scpt')) as f:
            script = f.read()
            return subprocess.check_call(['osascript', '-e', script])




def main():
    skype = Skype(config.skype_contacts)
    skype.start_call('enno')


if __name__ == '__main__':
    main()
