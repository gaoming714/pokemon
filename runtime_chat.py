

import re
import os
import sys
import requests
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
    json_path = os.path.join("data", "sina_option_data.json")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    with open(json_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)

    if 'now' not in option_dict:
        return
    if option_dict["std_300"] == 0:
        return
    if BOX != []:
        btime = BOX[-1]
        dtime = BOX[-1].add(minutes = 15)
        if dtime > btime.at(0,0,0).add(hours = 11,minutes = 30) and dtime < btime.at(0,0,0).add(hours = 13):
            dtime = dtime.add(hours = 1, minutes = 30)
        if dtime > now:
            return
    horizon = round(9 * pd.Series(option_dict["chg_300"][12:280]).std(), 2)
    zero = option_dict["chg_300"][280]
    if ONCE and now.hour == 9:
        msg = now_str + "\nHorizon🍌\t" + str(horizon)
        if zero >= 10:
            msg = msg + " 🍓 "
        elif zero <= -10:
            msg = msg + " 🍏 "
        r = requests.get('http://127.0.0.1:8010/msg/' + msg)
        ONCE = False
    std_arr = option_dict["std_300"][-1:-181:-1]
    if std_arr[0] == 0 or std_arr[120] == 0:
        return
    count = 0
    fail_count = 0
    for item in std_arr:
        if item < horizon:
            count = count + 1
        elif fail_count < 4 and count < 8:
            fail_count = fail_count + 1
        else:
            break
    logger.debug([count,std_arr[0]])

    if count >= 120:
        if fail_count != 0:
            berry_arr = option_dict["berry_300"][-1:-181:-1]
            berry_it = berry_arr[0]
            berry_long = sum(berry_arr) / len(berry_arr)
            berry_short = sum(berry_arr[0:20]) / len(berry_arr[0:20])
            # margin = round(-1.8 * pd.Series(option_dict["chg_300"][-481:-1]).std() * 100, 2)
            margin = -round(horizon * 20, 2)
            if berry_it >= berry_long and berry_it >= berry_short:
                BOX.append(now)
                msg = now_str + "\n 🍓 up" + "\nStop-loss\t" + str(margin)
                for user in ADDR:
                    email(user,msg)
                r = requests.get('http://127.0.0.1:8010/msg/' + msg, timeout=5)
            elif berry_it <= berry_long and berry_it <= berry_short:
                BOX.append(now)
                msg = now_str + "\n 🍏 down" + "\nStop-loss\t" + str(margin)
                for user in ADDR:
                    email(user,msg)
                r = requests.get('http://127.0.0.1:8010/msg/' + msg, timeout=5)


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
        logger.debug("round it")
        launch()
        hold_period()
        now = pendulum.now("Asia/Shanghai").add(seconds = -3)
        time.sleep(5 - now.second % 5)