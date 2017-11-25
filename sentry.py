import datetime
import glob
import os
import shutil
import threading
import time
import traceback
from pathlib import Path

import common
import config
from slack_conn import SlackConn


class Sentry:
    def __init__(self,
                 upload_dir,
                 channel_id,
                 slack_token,
                 everym
                 ):
        self.slack = SlackConn(slack_token)
        self.channel_id = channel_id
        self.upload_dir = upload_dir
        self.monitoring = False
        self.monitoring_thread = None
        self.everym = everym

    def list_uploaded(self):
        to_abs_path = lambda s: os.path.join(self.upload_dir, s)
        get_mod_time = lambda s: datetime.datetime.fromtimestamp(os.stat(to_abs_path(s)).st_mtime)

        return [(to_abs_path(x), get_mod_time(x))
                for x in os.listdir(self.upload_dir)
                if '.DS_Store' not in x
                ]

    def delete_older_than(self, minutes):
        now = datetime.datetime.now()
        for d, t in self.list_uploaded():
            if t < (now - datetime.timedelta(minutes=minutes)):
                shutil.rmtree(d)

    def find_unreported(self):
        donefile = lambda s: os.path.join(s, 'done')
        for d, t in self.list_uploaded():
            done = donefile(d)
            if os.path.isfile(done):
                continue
            else:
                Path(done).touch()
                yield find_newest_img(d), t

    def start(self):
        common.info('Sentry starting')
        self.slack.post_msg('Sentry starting')
        self.monitoring = True

        def monitor_uploads(context):
            last_reported = datetime.datetime.now() - datetime.timedelta(days=99)
            while context.monitoring:
                time.sleep(10)
                try:
                    unreported = list(context.find_unreported())
                    if len(unreported) > 0 and datetime.datetime.now() > (
                                last_reported + datetime.timedelta(minutes=context.everym)):
                        last_img, last_time = max(unreported, key=lambda s: s[1])
                        msg = 'Somebody is in the room at %s' % last_time
                        context.slack.post_msg(msg, self.channel_id)
                        context.slack.upload_img(last_img, self.channel_id)
                        last_reported = datetime.datetime.now()
                    else:
                        context.delete_older_than(context.everym * 3)
                except:
                    tb = traceback.format_exc()
                    common.error('Sentry unable to post omi log. Error Info: %s Retrying...' % tb)
                    time.sleep(10)

        def meh():
            monitor_uploads(self)

        monitoring_thread = threading.Thread(target=meh)
        monitoring_thread.start()
        self.monitoring_thread = monitoring_thread

    def stop(self):
        self.monitoring = False
        self.monitoring_thread.join(10)


def find_newest_img(path):
    return max(glob.iglob(os.path.join(path, '*.jpeg')), key=os.path.getctime)


def main():
    sentry = Sentry(config.sentry_upload_dir, config.sentry_channel_id, config.slack_token, config.report_omi_log_every_n_minute)
    sentry.start()
    time.sleep(30)
    sentry.stop()


if __name__ == '__main__':
    main()
