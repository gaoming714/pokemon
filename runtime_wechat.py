import os
import sys
import json
import pendulum
from flask import Flask, request, jsonify, Response
import itchat

from loguru import logger
logger.add("log/wechat.log")

## wechat profile
chat_path = os.path.join("data", "chat_config.json")
with open(chat_path, 'r', encoding='utf-8') as f:
    chat_list = json.load(f)

user_list = chat_list["user_list"]
chatroom_list = chat_list["chatroom_list"]

app = Flask(__name__)

def login_wechat_auto():
    # itchat.auto_login(enableCmdQR=2)
    # itchat.auto_login(hotReload=True)
    itchat.auto_login()
    payload = ""
    str_list = ["🍒 => 买  Buy ", "\n",
                "🍏 => 卖  Sell", "\n",
                "🍌 => 量  amount", "\n",
                "🔵 => 开  open", "\n",
                "🔷 => 平  close", "\n",
                "🍍 => 阈  area", "\n",
                (pendulum.now("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
                ]
    payload = payload.join(str_list)
    itchat.send(payload, toUserName='filehelper')

# @app.route('/login',methods=['GET','POST'])
def login_wechat():
    itchat.auto_login(enableCmdQR=2)
    payload = ""
    str_list = ["🍓 🍏 🍌 ", "\n",
                "Login in Successful.", "\n",
                (pendulum.now("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
                ]
    payload = payload.join(str_list)
    itchat.send(payload, toUserName='filehelper')
    return 0

# @app.route('/login',methods=['GET','POST'])
# def test_wechat():
#     with open(Path("QR.png"), 'rb') as f:
#         image = f.read()
#     return Response(image, mimetype='image/jpeg')


@app.route('/msg/<msg>',methods=['GET','POST'])
def send_message(msg):
    itchat.send(msg, toUserName='filehelper')
    for user in user_list:
        name = itchat.search_friends(name=user)
        itchat.send(msg, toUserName=name[0]["UserName"])
    for user in chatroom_list:
        name = itchat.search_chatrooms(name=user)
        itchat.send(msg, toUserName=name[0]["UserName"])
    # return jsonify(args=args, form=form)
    return json.dumps(msg)

if __name__ == '__main__':
    login_wechat()
    app.run(port=8010)
