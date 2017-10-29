import logging
import os
from logging import handlers
import subprocess

import config
from slack_conn import SlackConn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
for handler in logger.handlers:
    logger.removeHandler(handler)

handler = handlers.RotatingFileHandler(config.log_file, maxBytes=1024 * 1024 * 10, backupCount=2)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def error(msg):
    try:
        slack_conn = SlackConn(config.slack_token)
        slack_conn.post_msg('[Error] %s' % msg, channel=config.log_channel)
    except Exception as e:
        logger.exception(e)
    finally:
        logger.error(msg)


def info(msg):
    slack_conn = SlackConn(config.slack_token)
    slack_conn.post_msg('[INFO] %s' % msg, channel=config.log_channel)
    logger.info(msg)


base_dir = os.path.dirname(os.path.realpath(__file__))


def run_apple_script(script_name):
    with open(os.path.join(base_dir, 'scripts', script_name)) as f:
        content = f.read()
        return subprocess.check_call(['osascript', '-e', content])
