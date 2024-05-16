import re
import os
import sys
import requests
import sqlite3
import time
import json
import pendulum
import pickle
import pandas as pd

from envelopes import Envelope, GMailSMTP

from models import jsonDB
from models import sqliteDB
from models import util

from models.util import logConfig, logger
logConfig("logs/runchat.log", rotation="10 MB")

OWNER = {}
ADDR = []
BOX = []
ONCE = True

def launch():
    global BOX
    global ADDR
    global ONCE
    '''
    now_str is local
    now_online is the online time
    '''
    json_path = os.path.join("data", "fox_data.json")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    op_dict = jsonDB.load_it(json_path)

    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace = True)
    else:
        return

    start_tick = now.at(0,0,0).add(hours = 9,minutes = 55)
    if now < start_tick:
        delay = (start_tick - now).seconds
        time.sleep(delay)
        return
    if util.skipbox(BOX, now_str, minutes = 30):
        return

    horizon = 9 * pd.Series(op_df["chg_300"][12:280]).std()

    # send one day signal
    if len(op_df.index) > 280:
        zero = op_df["berry_300"].iloc[280]
    else:
        logger.warning("op_df.index is not enough => " + str(len(op_df.index)))
        zero = 0
    if ONCE and now.hour == 9:
        msg = now_str + "\nHorizon🍌\t" + str(round(horizon,4))
        if zero >= 10:
            msg = msg + " 🍓 "
        elif zero <= -10:
            msg = msg + " 🍏 "
        owl(msg)
        ONCE = False

    # send real chat
    arrow = op_df.iloc[-1]
    margin = - round(horizon * 12, 2)
    if horizon > 1:
        std_horizon = 1
    else:
        std_horizon = horizon
    berry_top = op_df["berry_300"].iloc[-480:-1].max()
    berry_bottom = op_df["berry_300"].iloc[-480:-1].min()
    print(berry_bottom)
    print(arrow["berry_300"])
    if arrow["berry_300"] > berry_top and arrow["std_300"] <= std_horizon:
        BOX.append(now_str)
        # DIRECT.append("up")
        msg = now_str + "\n 🍓 up" + "\nStop-loss\t" + str(margin)
        logger.info("Online => " + now_str)
        owl(msg)
        sqliteDB.send_pcr(arrow, "up")
    if arrow["berry_300"] < berry_bottom and arrow["std_300"] <= std_horizon:
        BOX.append(now_str)
        # DIRECT.append("down")
        msg = now_str + "\n 🍏 down" + "\nStop-loss\t" + str(margin)
        logger.info("Online => " + now_str)
        owl(msg)
        sqliteDB.send_pcr(arrow, "down")
    else:
        logger.debug("No Hands Up.")


def owl(msg):
    logger.info("Wol => " + msg)
    for user in ADDR:
        try:
            email(user,msg)
        except:
            logger.warning("Email Fail " + user)
    try:
        r = requests.get('http://127.0.0.1:8010/msg/' + msg, timeout=10)
    except:
        logger.warning("Wechat Fail " + msg)

def get_mixin():
    global OWNER
    global ADDR
    info_path = os.path.join("data", "chat_config.json")
    info_dict = jsonDB.load_it(info_path)
    try:
        OWNER = info_dict['owner']
        ADDR = info_dict['addr_list']
        handle = info_dict['handle']
        if handle == 0:
            ADDR = []
    except:
        logger.warning("chat_config.json is not ready")
        raise

def email(addr,msg):
    global OWNER
    envelope = Envelope(
        from_addr = (OWNER['from'], 'PokeScript'),
        to_addr = (addr, 'Hi Jack'),
        subject = 'PokeScript',
        text_body = msg
    )

    # Send the envelope using an ad-hoc connection...
    envelope.send(OWNER['smtp'], port=OWNER['port'], login=OWNER['login'],
                password=OWNER['password'], tls=True)

def clean():
    # clean box for pytest
    global BOX
    BOX = []


if __name__ == "__main__":
    while True:
        opening, info = util.fetch_opening()
        logger.debug(info["status"])
        if opening:
            launch()
            now = pendulum.now("Asia/Shanghai")
            delay = 6 - (now.second % 5) - (now.microsecond / 1e6)
            logger.debug("Wait " + str(delay) + " (s)")
            time.sleep(delay)
        elif info["status"] == "night":
            delay = info["delay"]
            logger.debug("Wait " + str(delay) + " (s)")
            time.sleep(delay)
            exit(0) # refresh date in util
        else:
            delay = info["delay"]
            logger.debug("Wait " + str(delay) + " (s)")
            time.sleep(delay)