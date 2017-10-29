import time

from slackclient import SlackClient

import config


class SlackConn:
    def __init__(self, slack_token):
        self.slack_token = slack_token
        self.sc = SlackClient(slack_token)

    def post_msg(self, msg, channel=config.general_channel):
        ret = self.sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=msg,
            as_user=True
        )
        if not ret['ok']:
            raise ValueError(ret)
        else:
            return ret

    def listen(self, on_message):
        if self.sc.rtm_connect():
            while True:
                time.sleep(1)
                msgs = self.sc.rtm_read()
                for msg in msgs:
                    if msg['type'] == 'error':
                        raise ValueError(msg)
                    elif msg['type'] == 'message':
                        on_message(msg)
        else:
            raise ValueError('Connection Failed')


if __name__ == '__main__':
    conn = SlackConn(config.slack_token)

