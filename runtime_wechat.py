import os
import sys
import time
import json
import pendulum
from pathlib import Path
from flask import Flask
import itchat
from envelopes import Envelope, GMailSMTP

from models import jsonDB
from models import util

from models.util import logConfig, logger
logConfig("logs/wechat.log", rotation="10 MB")

OWNER = {}
ME = ""

USERS = []
CHATROOMS = []

app = Flask(__name__)

def get_mixin():
    global OWNER
    global ME
    global USERS
    global CHATROOMS

    info_path = Path()/"data"/"chat_config.json"
    try:
        info_dict = jsonDB.load_it(info_path)
        OWNER = info_dict['owner']
        ME = info_dict['addr_list'][0]
        USERS = info_dict["user_list"]
        CHATROOMS = info_dict["chatroom_list"]
    except:
        logger.warning("chat_config.json is not ready")
        raise


def login_wechat():
    itchat.auto_login(enableCmdQR=2, exitCallback=callbackEC)
    payload = ""
    str_list = ["🍓 🍏 🍌 ", "\n",
                "Login in Successful.", "\n",
                (pendulum.now("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
                ]
    payload = payload.join(str_list)
    itchat.send(payload, toUserName='filehelper')


@app.route('/msg/<msg>',methods=['GET','POST'])
def send_message(msg):
    itchat.send(msg, toUserName='filehelper')
    for user in USERS:
        name = itchat.search_friends(name=user)
        itchat.send(msg, toUserName=name[0]["UserName"])
    for user in CHATROOMS:
        name = itchat.search_chatrooms(name=user)
        itchat.send(msg, toUserName=name[0]["UserName"])
    return {"msg": msg}

def callbackEC():
    logger.warning("Wechat logout!")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    email(ME, now_str)
    time.sleep(5)
    util.lumos("pm2 reload wechat")

def email(addr, msg):
    global OWNER
    envelope = Envelope(
        from_addr = (OWNER['from'], 'PokeScript'),
        to_addr = (addr, 'Hi Jack'),
        subject = 'Logout wechat',
        text_body = msg
    )

    # Send the envelope using an ad-hoc connection...
    envelope.send(OWNER['smtp'], port=OWNER['port'], login=OWNER['login'],
                password=OWNER['password'], tls=True)

if __name__ == '__main__':
    get_mixin()
    login_wechat()
    app.run(port=8010)
