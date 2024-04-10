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
logger.add("log/chat.log")

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

    if now < now.at(0,0,0).add(hours = 9,minutes = 55):
        return
    if skipbox(BOX, now_str, minutes = 30):
        return
    horizon = 9 * pd.Series(op_df["chg_300"][12:280]).std()

    # send one day signal
    if len(op_df.index) > 280:
        zero = op_df["berry_300"].iloc[280]
    else:
        logger.warning("op_df.index is not enough => " + len(op_df.index))
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
        logger.info("online => " + now_str)
        owl(msg)
        send_db(arrow, "up")
    if arrow["berry_300"] < berry_bottom and arrow["std_300"] <= std_horizon:
        BOX.append(now_str)
        # DIRECT.append("down")
        msg = now_str + "\n 🍏 down" + "\nStop-loss\t" + str(margin)
        logger.info("online => " + now_str)
        owl(msg)
        send_db(arrow, "down")
    else:
        logger.debug("No Hands Up.")

def dump():
    if len(op_df.index) > 280:
        zero = op_df["berry_300"].iloc[280]
    else:
        logger.warning("op_df.index is not enough => " + len(op_df.index))
        zero = 0
    if ONCE and now.hour == 9:
        msg = now_str + "\nHorizon🍌\t" + str(round(horizon,4))
        if zero >= 10:
            msg = msg + " 🍓 "
        elif zero <= -10:
            msg = msg + " 🍏 "
        r = requests.get('http://127.0.0.1:8010/msg/' + msg)
        ONCE = False
    std_arr = op_df["std_300"][-1:-181:-1]
    if std_arr.iloc[0] == 0 or std_arr.iloc[120] == 0:
        return
    count = 0
    fail_count = 0
    for item in std_arr:
        if item < horizon ** 0.5:
            count = count + 1
        elif fail_count < 4 and count < 8:
            fail_count = fail_count + 1
        else:
            break

    if count >= 120:
        if fail_count != 0:
            berry_arr = op_df["berry_300"][-1:-181:-1]
            berry_it = berry_arr.iloc[0]
            berry_long = sum(berry_arr) / len(berry_arr)
            berry_short = sum(berry_arr[0:20]) / len(berry_arr[0:20])
            # margin = round(-1.8 * pd.Series(op_df["chg_300"][-481:-1]).std() * 100, 2)
            margin = - round(horizon * 12, 2)
            logger.debug([now_str, berry_it, berry_long, berry_short])
            if berry_it >= berry_long and berry_it >= berry_short:
                BOX.append(now)
                msg = now_str + "\n 🍓 up" + "\nStop-loss\t" + str(margin)
                logger.info("online => " + now_str)
                owl(msg)
                send_db(arrow, "up")
            elif berry_it <= berry_long and berry_it <= berry_short:
                BOX.append(now)
                msg = now_str + "\n 🍏 down" + "\nStop-loss\t" + str(margin)
                logger.info("online => " + now_str)
                owl(msg)
                send_db(arrow, "down")
            else:
                logger.debug("No Hands Up.")

now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=55)
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

# def save_symbol(arrow):
#     try:
#         symbol_path("data", "fox_symbol.json")
#         with open(symbol_path, 'r', encoding='utf-8') as file:
#             symbol_dict = json.load(file)
#         symbol_dict["data"].append(arrow)
#     except:
#         logger.warning("Symbol Fail Chat => " + arrow["dt"])

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

def skipbox(box_list, now_str, minutes = 15):
    now = pendulum.parse(now_str,tz="Asia/Shanghai")
    if box_list != []:
        btime = pendulum.parse(BOX[-1],tz="Asia/Shanghai")
        dtime = btime.add(minutes = minutes)
        if dtime > btime.at(0,0,0).add(hours = 11,minutes = 30) and dtime < btime.at(0,0,0).add(hours = 13):
            dtime = dtime.add(hours = 1, minutes = 30)
        if dtime > now:
            return True
    return False

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