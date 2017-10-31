import datetime
import glob
import os
import shutil
import threading
import traceback
from pathlib import Path
import time

import common
import config
from slack_conn import SlackConn


class Sentry:
    def __init__(self,
                 upload_dir,
                 channel_id,
                 slack_token
                 ):
        self.slack = SlackConn(slack_token)
        self.channel_id = channel_id
        self.upload_dir = upload_dir
        self.monitoring = False
        self.monitoring_thread = None

    def list_uploaded(self):
        to_abs_path = lambda s: os.path.join(self.upload_dir, s)
        get_mod_time = lambda s: datetime.datetime.fromtimestamp(os.stat(to_abs_path(s)).st_mtime)

        return [(to_abs_path(x), get_mod_time(x))
                for x in os.listdir(self.upload_dir)
                if '.DS_Store' not in x
                ]

    def delete_older_than(self, days):
        now = datetime.datetime.now()
        for d, t in self.list_uploaded():
            if t < (now - datetime.timedelta(days=days)):
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
            while context.monitoring:
                time.sleep(10)
                try:
                    unreported = context.find_unreported()
                    last_img, last_time = max(unreported, key=lambda s: s[1])
                    msg = 'Somebody is in the room at %s' % last_time
                    context.slack.post_msg(msg, self.channel_id)
                    context.slack.upload_img(last_img, self.channel_id)
                except StopIteration as e:
                    common.info('Exiting because shutdown requested')
                    context.monitoring = False
                    return
                except:
                    tb = traceback.format_exc()
                    common.error('Omibot unable to listen to commands. Error Info: %s Retrying...' % tb)
                    time.sleep(10)

        monitoring_thread = threading.Thread(target=monitor_uploads(self))
        monitoring_thread.start()
        self.monitoring_thread = monitoring_thread

    def stop(self):
        self.monitoring = False
        self.monitoring_thread.join(10)


def find_newest_img(path):
    return max(glob.iglob(os.path.join(path, '*.jpeg')), key=os.path.getctime)


def main():
    sentry = Sentry(config.sentry_upload_dir, config.sentry_channel_id, config.slack_token)
    sentry.start()
    time.sleep(30)
    sentry.stop()


if __name__ == '__main__':
    main()
