import time
import traceback
import re

import common
import config
import sound
from ampel import Ampel
from skype import Skype
from slack_conn import SlackConn

def extract_destination(msg):
    return re.match(r'.+ call ([A-z]+)$', msg['text']).group(1)


class Omibot:
    def __init__(self, channel_name, bot_name, slack_conn, ampel, skype):
        self.channel_name = channel_name
        self.bot_name = bot_name
        self.slack_conn = slack_conn
        self.ampel = ampel
        self.command_dict = [
            ('ring', self.ring),
            ('call', self.call),
        ]
        self.skype = skype

    def is_bot_mentioned(self, msg):
        return self.bot_name in msg['text'] and msg['channel'] == self.channel_name

    def on_message(self, msg):
        if self.is_bot_mentioned(msg):
            for key, command in self.command_dict:
                if key in msg['text']:
                    common.info('Omibot executing:%s on %s' % (key, msg))
                    return command(msg)

    def start(self):
        while True:
            try:
                self.slack_conn.listen(self.on_message)
            except:
                tb = traceback.format_exc()
                common.error('Omibot unable to listen to commands. Error Info: %s Retrying...' % tb)
                time.sleep(10)

    def ring(self, msg):
        self.slack_conn.post_msg('Ringing Omi for 30 seconds')
        sound.ring(30)
        self.ampel.flash(30)

    def call(self, msg):
        try:
            name = extract_destination(msg)
        except Exception as e:
            self.slack_conn.post_msg(
                "Sorry, I can't tell who you want me to call." +
                " Try something like '@omibot call enno'"
            )
            return
        self.ring(msg)
        self.slack_conn.post_msg('Calling enno from Omi')
        self.skype.start_call(name)



def main():
    omibot = Omibot(config.general_channel_id,
                    config.botname,
                    SlackConn(config.slack_token),
                    Ampel(config.cleware_exec),
                    Skype(config.skype_contacts))
    common.info('Omibot starts listening...')
    omibot.start()


if __name__ == '__main__':
    try:
        main()
    except:
        common.error(traceback.format_exc())
