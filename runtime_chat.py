

import re
import os
import sys
import requests
import time
import json
import pendulum
import pickle
import pandas as pd


# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}

SIGN_list = []
# (time, signal, value)


def launch():
    '''
    now_str is local
    now_online is the online time
    '''
    json_path = os.path.join("data", "sina_option_data.json")

    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()

    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            option_dict = json.load(file)
    except:
        return

    analyse(option_dict)
    # emit()

def analyse(option_dict):

    df = pd.DataFrame(option_dict,index=option_dict["now_list"])
    df = df.drop("now_list",axis=1)

    if len(df.index) < 240:
        return
    stamp = df["now"][-1]
    ave = df["berry_300"][-240:].mean()
    last = df["berry_300"][-1]
    print([ave, last - ave])
    if last > ave + 1 and last > 50:
        add_sign(df["now"][-1], "open_buy", last)

    if last < ave - 1 and last < 50:
        add_sign(df["now"][-1], "open_sell", last)


def add_sign(stamp, sign, value):
    if SIGN_list == []:
        SIGN_list.append((stamp, sign, value))
        emit()
    else:
        last_stamp = SIGN_list[-1][0]
        if pendulum.parse(last_stamp).add(minutes=5) < pendulum.parse(stamp):
            SIGN_list.append((stamp, sign, value))
            emit()


def emit():

    msg = SIGN_list[-1][0] + " " + SIGN_list[-1][1] + " " + str(SIGN_list[-1][2])
    print(msg)
    r = requests.get('http://127.0.0.1:8008/msg/'+ msg)



now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=31)
mk_beta = dawn.add(hours=11,minutes=30)
mk_gamma = dawn.add(hours=13,minutes=0)
mk_delta = dawn.add(hours=15,minutes=0)
mk_zeta = pendulum.tomorrow("Asia/Shanghai")


def hold_period():
    """
        mu nu  9:30  alpha beta  12  gamma  delta  15 zeta
    """
    while True:
        now = pendulum.now("Asia/Shanghai")
        # refresh remain per half-hour
        # heart beat
        # if now.minute % 30 == 0:
        #     print(("JQData Remains => ",personal.jq_remains()))

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





def lumos(cmd):
    # res = 0
    print("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res

if __name__ == '__main__':
    while True:
        launch()
        if sys.argv[-1] == 'test':
            pass
        else:
            hold_period()
        print(pendulum.now("Asia/Shanghai"))
        now = pendulum.now("Asia/Shanghai")
        time.sleep(4 - now.second % 5)
        time.sleep(1)