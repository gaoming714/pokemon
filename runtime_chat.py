

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

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}

EMAIL = {}
ADDR = []
BOX = []


def launch():
    global BOX
    global ADDR
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
    std_arr = option_dict["std_300"][-1:-181:-1]
    if std_arr[0] == 0 or std_arr[120] == 0:
        return
    count = 0
    fail_count = 0
    for item in std_arr:
        if item < 1:
            count = count + 1
        elif fail_count < 4 and count < 8:
            fail_count = fail_count + 1
        else:
            break
    print([count,std_arr[-1]])

    if count >= 120:
        if fail_count != 0:
            BOX.append(now)
            berry_arr = option_dict["berry_300"][-1:-181:-1]
            berry_mean = sum(berry_arr) / len(berry_arr)
            margin = round(-1.5 * pd.Series(option_dict["pct_300"][-481:-1]).std(), 2)
            if berry_arr[0] >= berry_mean and berry_mean >= -10:
                msg = now_str + "\tup\t" + "🍓" + "\nStop-loss\t" + str(margin*100)
                for user in ADDR:
                    email(user,msg)
            elif berry_arr[0] < berry_mean and berry_mean < 10:
                msg = now_str + "\tdown\t" + "🍏" + "\nStop-loss\t" + str(margin*100)
                for user in ADDR:
                    email(user,msg)


now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=35)
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
            print(["remain (s) ",(mk_alpha - now).total_seconds()])
            time.sleep((mk_alpha - now).total_seconds())
        elif now <= mk_beta:
            return
        elif now < mk_gamma:
            print(["remain (s) ",(mk_gamma - now).total_seconds()])
            time.sleep((mk_gamma - now).total_seconds())
        elif now <= mk_delta:
            return
        else:
            print("Market Closed")
            print(["remain to end (s) ",(mk_zeta - now).total_seconds()])
            time.sleep((mk_zeta - now).total_seconds() + 3600)
            # sleep @ 1:00
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
        print("chat_config.json is not ready")
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
    print("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res

if __name__ == '__main__':
    get_mixin()
    while True:
        launch()
        hold_period()
        print(pendulum.now("Asia/Shanghai"))
        now = pendulum.now("Asia/Shanghai").add(seconds = -3)
        time.sleep(5 - now.second % 5)