import time
import traceback
import re

import sys

import os

import common
import config
import health
import restorer
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
            ('ring', self.ring, 'Set off sound and flashing light at Omi'),
            ('call', self.call, "Call someone from Omi's Skype"),
            ('shutdownr', self.shutdownr, "Reboot Omibot's machine"),
            ('restart skype', self.restart_skype, "Restart Omi's skype"),
            ('help', self.help, "Display help"),
            ('killbot', self.kill, "Kill Omibot"),
            ('health', self.health_check, "Perform health check")
        ]
        self.skype = skype

    def is_bot_mentioned(self, msg):
        return self.bot_name in msg['text'] and msg['channel'] == self.channel_name

    def on_message(self, msg):
        if self.is_bot_mentioned(msg):
            for key, command, _desc in self.command_dict:
                if key in msg['text']:
                    common.info('Omibot executing:%s on %s' % (key, msg))
                    return command(msg)
            self.slack_conn.post_msg("Sorry I don't understand your command.")
            self.help(msg)

    def start(self):
        startmsg = 'Omibot starting:pid=%s' % os.getpid()
        common.info(startmsg)
        self.slack_conn.post_msg(startmsg)
        while True:
            try:
                self.slack_conn.listen(self.on_message)
            except StopIteration as e:
                common.info('Exiting because shutdown requested')
                return
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
            skypeid = self.skype.lookup(name)
        except Exception as e:
            self.slack_conn.post_msg(
                "Sorry, I can't tell who you want me to call." +
                " Try something like '@omibot call enno'" +
                " Known contacts:%s" % self.skype.skype_contacts
            )
            return
        self.ring(msg)
        self.slack_conn.post_msg('Calling %s from Omi in 15sec' % name)
        self.skype.start_call(name)

    def shutdownr(self, msg):
        self.slack_conn.post_msg('Restarting Omibot Machine')
        restorer.restart()

    def restart_skype(self, msg):
        self.slack_conn.post_msg('Restarting skype')
        self.skype.reset()

    def help(self, msg):
        msg = "Commands:"
        for key, _command, desc in self.command_dict:
            msg += '\n%s:\t%s' % (key, desc)

        self.slack_conn.post_msg("HELP:\n" + msg)

    def kill(self, msg):
        self.slack_conn.post_msg("Exiting because shutdown requested")
        raise StopIteration('EXITING')

    def health_check(self, msg):
        def batt():
            try:
                pct = health.battery_status()
                self.slack_conn.post_msg('Battery status: %s%%' % pct)
                return pct
            except Exception as e:
                tb = traceback.format_exc()
                common.error(tb)

        def reset_vol():
            health.reset_volume()
            self.slack_conn.post_msg('Reset volume to 100%')

        def ampel_check():
            try:
                code, out = self.ampel.check_status()
                ampel_num = int(re.match('.*Number of Cleware devices found: ([0-9]+).*', str(out)).group(1))
                self.slack_conn.post_msg('%s ampels found' % ampel_num)
            except:
                tb = traceback.format_exc()
                common.error(tb)

        batt_pct = batt()
        reset_vol()
        ampel_num = ampel_check()

        self.restart_skype(msg)








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
