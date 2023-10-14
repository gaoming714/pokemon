import os
import sys
import json
import time
import pendulum
from flask import Flask, request, jsonify, Response
import itchat
from envelopes import Envelope, GMailSMTP
from util import color, lumos

from loguru import logger
logger.add("log/wechat.log")

EMAIL = {}
ME = ""

USERS = []
CHATROOMS = []

## wechat profile
# chat_path = os.path.join("data", "chat_config.json")
# with open(chat_path, 'r', encoding='utf-8') as f:
#     chat_dict = json.load(f)

# USERS = chat_list["user_list"]
# CHATROOMS = chat_list["chatroom_list"]

app = Flask(__name__)

def get_mixin():
    global EMAIL
    global ME
    global USERS
    global CHATROOMS

    info_path = os.path.join("data", "chat_config.json")
    try:
        with open(info_path, 'r', encoding='utf-8') as file:
            info_dict = json.load(file)
        EMAIL = info_dict['email']
        ME = info_dict['addr_list'][0]
        USERS = info_dict["user_list"]
        CHATROOMS = info_dict["chatroom_list"]
    except:
        logger.warning("chat_config.json is not ready")
        raise

# def login_wechat_auto():
#     # itchat.auto_login(enableCmdQR=2)
#     # itchat.auto_login(hotReload=True)
#     itchat.auto_login()
#     payload = ""
#     str_list = ["🍒 => 买  Buy ", "\n",
#                 "🍏 => 卖  Sell", "\n",
#                 "🍌 => 量  amount", "\n",
#                 "🔵 => 开  open", "\n",
#                 "🔷 => 平  close", "\n",
#                 "🍍 => 阈  area", "\n",
#                 (pendulum.now("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
#                 ]
#     payload = payload.join(str_list)
#     itchat.send(payload, toUserName='filehelper')

def login_wechat():
    itchat.auto_login(enableCmdQR=2, exitCallback=callbackEC)
    payload = ""
    str_list = ["🍓 🍏 🍌 ", "\n",
                "Login in Successful.", "\n",
                (pendulum.now("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
                ]
    payload = payload.join(str_list)
    itchat.send(payload, toUserName='filehelper')
    return 0

@app.route('/msg/<msg>',methods=['GET','POST'])
def send_message(msg):
    itchat.send(msg, toUserName='filehelper')
    for user in USERS:
        name = itchat.search_friends(name=user)
        itchat.send(msg, toUserName=name[0]["UserName"])
    for user in CHATROOMS:
        name = itchat.search_chatrooms(name=user)
        itchat.send(msg, toUserName=name[0]["UserName"])
    # return jsonify(args=args, form=form)
    return json.dumps(msg)

def callbackEC():
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    email(ME, now_str)
    color('Logout wechat')
    time.sleep(5)
    lumos("pm2 reload wechat")

def email(addr,msg):
    global EMAIL
    envelope = Envelope(
        from_addr = (EMAIL['from'], 'PokeScript'),
        to_addr = (addr, 'Hi Jack'),
        subject = 'Logout wechat',
        text_body = msg
    )

    # Send the envelope using an ad-hoc connection...
    envelope.send(EMAIL['smtp'], port=EMAIL['port'], login=EMAIL['login'],
                password=EMAIL['password'], tls=True)

if __name__ == '__main__':
    get_mixin()
    login_wechat()
    app.run(port=8010)
