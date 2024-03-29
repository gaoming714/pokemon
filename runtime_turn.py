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

from loguru import logger
logger.add("log/turn.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}

EMAIL = {}
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
    with open(json_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)

    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace = True)
    else:
        return

    arrow = op_df.iloc[-1]
    if arrow["vol_300"] == 0:
        return

    if BOX != []:
        btime = BOX[-1]
        dtime = BOX[-1].add(minutes = 2)
        if dtime > btime.at(0,0,0).add(hours = 11,minutes = 30) and dtime < btime.at(0,0,0).add(hours = 13):
            dtime = dtime.add(hours = 1, minutes = 30)
        if dtime > now:
            return

    vol_mean = op_df["vol_300"][-13:].mean()
    vol_diff = (arrow["vol_300"] - vol_mean) / 1000

    if vol_diff >= 10:
        BOX.append(now)
        msg = now_str + "\n 🧊 Turn " + "{:8.2f} K".format(round(vol_diff, 2))
        logger.info("online => " + now_str)
        owl(msg)
        send_db(arrow, "turn")

now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=40)
mk_beta = dawn.add(hours=11,minutes=30)
mk_gamma = dawn.add(hours=13,minutes=0)
mk_delta = dawn.add(hours=15,minutes=0,seconds=20)
mk_zeta = pendulum.tomorrow("Asia/Shanghai")

def hold_period():
    """
        mu nu  9:35  alpha beta  12  gamma  delta  15:00:20 zeta
    """
    while True:
        now = pendulum.now("Asia/Shanghai")

        if now < mk_alpha:
            logger.debug(["remain (s) ",(mk_alpha - now).total_seconds()])
            time.sleep((mk_alpha - now).total_seconds())
        elif now <= mk_beta:
            return
        elif now < mk_gamma:
            logger.debug(["remain (s) ",(mk_gamma - now).total_seconds()])
            time.sleep((mk_gamma - now).total_seconds())
        elif now <= mk_delta:
            return
        else:
            logger.debug("Market Closed")
            logger.debug(["remain to end (s) ",(mk_zeta - now).total_seconds()])
            time.sleep((mk_zeta - now).total_seconds() + 3900)
            # sleep @ 1:05
            exit(0)

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
    global EMAIL
    global ADDR
    info_path = os.path.join("data", "chat_config.json")
    try:
        with open(info_path, 'r', encoding='utf-8') as file:
            info_dict = json.load(file)
        EMAIL = info_dict['email']
        ADDR = info_dict['addr_list']
        handle = info_dict['handle']
        if handle == 0:
            ADDR = []
    except:
        logger.warning("chat_config.json is not ready")
        raise

def send_db(arrow, symbol = ""):
    if os.path.exists("db.sqlite3"):
        # connect
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
    else:
        return
    # insert
    cursor.execute('''INSERT INTO stock (dt, symbol,
                    chg_50, pcr_50, berry_50,
                    chg_300, pcr_300, berry_300,
                    chg_500, pcr_500, berry_500,
                    inc_t0, burger, vol_300, std_300)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''',
                    (arrow.name, symbol,
                    arrow['chg_50'], arrow['pcr_50'], arrow['berry_50'],
                    arrow['chg_300'], arrow['pcr_300'], arrow['berry_300'],
                    arrow['chg_500'], arrow['pcr_500'], arrow['berry_500'],
                    arrow['inc_t0'], arrow['burger'], arrow['vol_300'], arrow['std_300']))
    conn.commit()
    conn.close()

def email(addr,msg):
    global EMAIL
    envelope = Envelope(
        from_addr = (EMAIL['from'], 'PokeScript'),
        to_addr = (addr, 'Hi Jack'),
        subject = 'PokeScript',
        text_body = msg
    )

    # Send the envelope using an ad-hoc connection...
    envelope.send(EMAIL['smtp'], port=EMAIL['port'], login=EMAIL['login'],
                password=EMAIL['password'], tls=True)

def lumos(cmd):
    # res = 0
    logger.debug("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res

def clean():
    # clean box for pytest
    global BOX
    BOX = []


if __name__ == '__main__':
    get_mixin()
    while True:
        launch()
        hold_period()
        now = pendulum.now("Asia/Shanghai").add(seconds = -3)
        time.sleep(5 - now.second % 5)