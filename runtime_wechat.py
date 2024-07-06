import os
import sys
import time
import json
import tomlkit
import pendulum
from pathlib import Path
from flask import Flask
import itchat
from envelopes import Envelope, GMailSMTP

from mars import jsonDB
from mars import util

from mars.util import logConfig, logger

logConfig("logs/wechat.log", rotation="10 MB")

# send logout msg
OWNER = {}
ME = ""

USERS = []
CHATROOMS = []

app = Flask(__name__)


def login_wechat():
    itchat.auto_login(enableCmdQR=2, exitCallback=callbackEC)
    payload = ""
    str_list = [
        "🍓 🍏 🍌 ",
        "\n",
        "Login in Successful.",
        "\n",
        (pendulum.now("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S"),
    ]
    payload = payload.join(str_list)
    itchat.send(payload, toUserName="filehelper")


@app.route("/msg/<msg>", methods=["GET", "POST"])
def send_message(msg):
    itchat.send(msg, toUserName="filehelper")
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
        from_addr=(OWNER["from"], "PokeScript"),
        to_addr=(addr, "Hi Jack"),
        subject="Logout wechat",
        text_body=msg,
    )

    # Send the envelope using an ad-hoc connection...
    envelope.send(
        OWNER["smtp"],
        port=OWNER["port"],
        login=OWNER["login"],
        password=OWNER["password"],
        tls=True,
    )

def boot():
    global OWNER
    global ME
    global USERS
    global CHATROOMS

    config_path = Path() / "data" / "chat_config.toml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = tomlkit.parse(f.read())
    try:
        # skip
        if not config.get("active", False) or config.get("active") == 0:
            logger.info("Inactive Boot")
            return
        logger.success("Active Boot")
        OWNER = config["owner"]
        for client in config["client"]:
            if client.get("skip"):
                continue
            if client.get("channel") == "wechat":
                USERS.append(client["symbol"])
            if client.get("channel") == "chatroom":
                CHATROOMS.append(client["symbol"])
            if client.get("channel") == "email" and ME == "":
                ME = client["symbol"]
        logger.debug(OWNER)
        logger.debug(ME)
        logger.debug(USERS)
        logger.debug(CHATROOMS)
    except:
        logger.warning("chat_config.json is not ready")
        raise

if __name__ == "__main__":
    boot()
    login_wechat()
    app.run(port=8010)
