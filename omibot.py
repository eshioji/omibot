import os
import re
import threading
import time
import traceback

import common
import config
import health
import restorer
import sound
from ampel import Ampel
from sentry import Sentry
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
            ('call', self.call, "Call someone from Omi's Skype (e.g. '@omibot call enno')"),
            ('help', self.help, "Display help"),
            ('system restart skype', self.restart_skype, "Restart Omi's skype"),
            ('system recover', self.health_check, "Perform health check and try to recover functions"),
            ('system shutdownr', self.shutdownr, "Reboot Omibot's machine"),
            ('system killbot', self.kill, "Kill Omibot"),
        ]
        self.skype = skype
        self.monitoring = False
        self.monitoring_thread = None

    def is_bot_mentioned(self, msg):
        return self.bot_name in msg['text'] and msg['channel'] == self.channel_name

    def on_message(self, msg):
        if self.is_bot_mentioned(msg):
            for key, command, _desc in self.command_dict:
                if key in msg['text']:
                    common.info('Omibot executing:%s on %s' % (key, msg))
                    return command(msg)
            self.slack_conn.post_msg("Sorry I don't understand your command.")
            common.error(msg)
            self.help(msg)

    def start(self):
        startmsg = 'Omibot starting:pid=%s' % os.getpid()
        common.info(startmsg)
        self.slack_conn.post_msg(startmsg)

        self.monitoring = True

        def monitor_msgs(context):
            while context.monitoring:
                try:
                    context.slack_conn.listen(context.on_message)
                except StopIteration as e:
                    common.info('Exiting because shutdown requested')
                    context.monitoring = False
                    return
                except:
                    tb = traceback.format_exc()
                    common.error('Omibot unable to listen to commands. Error Info: %s Retrying...' % tb)
                    time.sleep(10)

        def meh():
            monitor_msgs(self)

        monitoring_thread = threading.Thread(target=meh)
        monitoring_thread.start()
        self.monitoring_thread = monitoring_thread

    def stop(self):
        self.slack_conn.post_msg('Omibot stop requested')
        self.monitoring = False
        self.monitoring_thread.join(10)

    def ring(self, msg):
        self.slack_conn.post_msg('Ringing Omi for 30 seconds')
        ring = sound.ring(30)
        flash = self.ampel.flash(30)
        ring.join(40)
        flash.join(40)
        self.slack_conn.post_msg('Ringed Omi for 30 seconds')

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
        self.slack_conn.post_msg('Calling %s from Omi' % name)
        self.skype.start_call(name)
        self.ring(msg)

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

    def is_alive(self):
        return self.monitoring_thread.is_alive()

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

    sentry = Sentry(config.sentry_upload_dir, config.sentry_channel_id, config.slack_token,
                    config.report_omi_log_every_n_minute)
    common.info('Sentry starts listening...')
    sentry.start()

    while True:
        time.sleep(10)
        if not omibot.is_alive():
            common.error('Omibot is dead')
            return


if __name__ == '__main__':
    try:
        main()
    except:
        common.error(traceback.format_exc())
