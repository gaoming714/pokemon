

import re
import os
import sys
import requests
import sqlite3
import time
import json
import pendulum
import pickle
import numpy as np
import math
import pandas as pd
import plotly.express as px
from rich.progress import track

from loguru import logger
logger.add("log/predict_op.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}


BOX = []
DIRECT = []
BERRY = []
PANEL = []

def launch():

    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()

    nightly_path = os.path.join("data", "fox_nightly.json")

    with open(nightly_path, 'r', encoding='utf-8') as file:
        nightly_data = json.load(file)
    nightly_list = nightly_data["records"]

    with open(os.path.join("data", "fox_data.json"), 'r', encoding='utf-8') as file:
        sina_option_data = json.load(file)
        if "now" in sina_option_data:
            nightly_list.append("fox_data")

    print(np.array(nightly_list))
    for night in track(nightly_list):
        intraday_path = os.path.join("data", night + ".json")
        if os.path.exists(intraday_path):
            with open(intraday_path, 'r', encoding='utf-8') as file:
                op_dict = json.load(file)
            if "now" in op_dict and op_dict["now"] != "":
                op_df = pd.DataFrame(op_dict["data"])
                op_df.set_index("dt", inplace = True)
                # print(op_df)
                analyse2(op_df)
                play_day(op_df)

    show_df()


def launch_solo(night):
    intraday_path = os.path.join("data", night + ".json")
    if not os.path.exists(intraday_path):
        return
    with open(intraday_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace = True)
        analyse2(op_df)
        play_day(op_df)

    show_df()

def show_df():
    global PANEL
    df = pd.DataFrame(PANEL)
    pd.set_option('display.max_rows',900)
    # pd.set_option('display.max_columns',500)
    # pd.set_option('display.width',1000)
    df["cumsum"] = df["diff_chg"].cumsum()
    print(df)
    print(df.describe())
    # print(df.sort_values("prod"))

    # t_format = pd.to_datetime(df["time"])
    # new_df = df.set_index(t_format)
    # print(new_df["output"].resample('W').sum())

    # print(df["output"].cumsum())
    # print("AVE   ", df["prod"].sum()/days)
    fig = px.line(df, x=df.index, y=["cumsum"], title='')
    fig.show()

def analyse1(op_df):
    # traditional
    global BOX
    global DIRECT
    horizon = op_df["chg_300"][12:280].std() * 9
    print(horizon)
    if horizon > 1:
        std_horizon = 1
    else:
        std_horizon = horizon ** 0.5
    for length in range(280, len(op_df.index)):
        sub_df = op_df.iloc[:length]
        now_str = sub_df.index[-1]
        now = pendulum.parse(now_str,tz="Asia/Shanghai")
        if skipbox(BOX, now_str):
            continue
        std_arr = sub_df["std_300"][-1:-181:-1]
        if std_arr.iloc[0] == 0 or std_arr.iloc[120] == 0:
            continue
        count = 0
        fail_count = 0
        for item in std_arr:
            if item < std_horizon:
                count = count + 1
            elif fail_count < 4 and count < 8:
                fail_count = fail_count + 1
            else:
                break

        if count >= 120:
            if fail_count != 0:
                berry_arr = sub_df["berry_300"][-1:-181:-1]
                berry_it = berry_arr.iloc[0]
                berry_long = sum(berry_arr) / len(berry_arr)
                berry_short = sum(berry_arr[0:20]) / len(berry_arr[0:20])
                margin = - round(horizon * 12, 2)
                # logger.debug([now_str, berry_it, berry_long, berry_short])
                if berry_it >= berry_long and berry_it >= berry_short:
                    BOX.append(now_str)
                    DIRECT.append("up")
                    msg = now_str + "\n 🍓 up" + "\nStop-loss\t" + str(margin)
                    # logger.info(msg)
                elif berry_it <= berry_long and berry_it <= berry_short:
                    BOX.append(now_str)
                    DIRECT.append("down")
                    msg = now_str + "\n 🍏 down" + "\nStop-loss\t" + str(margin)
                    # logger.info(msg)
                else:
                    pass
                    # logger.debug("No Hands Up.")

def analyse2(op_df):
    # new low std
    global BOX
    global DIRECT
    horizon = op_df["chg_300"][12:280].std() * 9
    if horizon > 1:
        std_horizon = 1
    else:
        std_horizon = horizon
    berry_300_ma = op_df['berry_300'].rolling(120, min_periods = 1).mean()
    for pointer, index in enumerate(op_df.index):
        now_str = op_df.index[pointer]
        now = pendulum.parse(now_str,tz="Asia/Shanghai")
        if now < now.at(0,0,0).add(hours = 9,minutes = 55):
            continue
        if now > now.at(0,0,0).add(hours = 14,minutes = 45):
            continue
        if skipbox(BOX, now_str, minutes = 30):
            continue
        arrow = op_df.loc[index]
        margin = - round(horizon * 12, 2)
        berry_top = op_df["berry_300"].iloc[360:pointer].iloc[-480:].max()
        berry_bottom = op_df["berry_300"].iloc[360:pointer].iloc[-480:].min()
        if arrow["berry_300"] > berry_top and arrow["std_300"] <= std_horizon:
            BOX.append(now_str)
            DIRECT.append("up")
            msg = now_str + "\n 🍓 up" + "\nStop-loss\t" + str(margin)
            # send_db(arrow, "up")
        if arrow["berry_300"] < berry_bottom and arrow["std_300"] <= std_horizon:
            BOX.append(now_str)
            DIRECT.append("down")
            msg = now_str + "\n 🍏 down" + "\nStop-loss\t" + str(margin)
            # send_db(arrow, "down")

def analyse3(op_df):
    # test 9:50
    global BOX
    global DIRECT
    horizon = op_df["chg_300"][12:280].std() * 9
    for pointer, index in enumerate(op_df.index):
        now_str = op_df.index[pointer]
        now = pendulum.parse(now_str,tz="Asia/Shanghai")
        if now < now.at(0,0,0).add(hours = 9,minutes = 50):
            continue
        arrow = op_df.loc[index]
        margin = - round(horizon * 12, 2)
        if arrow["berry_300"] > 10:
            BOX.append(now_str)
            DIRECT.append("up")
            # send_db(arrow, "up")
        if arrow["berry_300"] < -10:
            BOX.append(now_str)
            DIRECT.append("down")
            # send_db(arrow, "down")
        return

def play_day(op_df):
    global BOX
    global DIRECT
    global PANEL
    horizon = op_df["chg_300"][12:280].std() * 9
    # print(["horizon", horizon])
    berry_300_ma = op_df['berry_300'].rolling(120, min_periods = 1).mean()
    for pointer, btime in enumerate(BOX):
        if PANEL != []:
            last_dt = pendulum.parse(PANEL[-1]["close_dt"],tz="Asia/Shanghai")
            new_dt = pendulum.parse(BOX[pointer],tz="Asia/Shanghai")
            if last_dt > new_dt:
                continue
        play_core(op_df.loc[btime:], DIRECT[pointer], berry_300_ma, horizon)


    BOX = []
    DIRECT = []
    BERRY = []

def play_core(op_df, direct, berry_300_ma, horizon):
    global PANEL
    edgeMargin = - horizon * 0.16
    if edgeMargin < -0.3:
        edgeMargin = -0.3
    # print(["edgeMargin", edgeMargin])
    origin = op_df.iloc[0]
    el = {"open_dt": origin.name, "direct": direct}
    for index in op_df.index:
        arrow = op_df.loc[index]
        # print([index, op_df["berry_300"][index],berry_300_ma[index] - 0.2])
        if direct == "up":
            edge = op_df["chg_300"][:index].max() + edgeMargin
            if op_df["chg_300"][index] < edge:
                el["close_dt"] = arrow.name
                el["open_chg"] = origin["chg_300"]
                el["close_chg"] = arrow["chg_300"]
                el["diff_chg"] = arrow["chg_300"] - origin["chg_300"]
                el["gap"] = gap(origin.name,arrow.name)
                el["res"] = "stop-ss-up"
                break
            if op_df["berry_300"][index] < berry_300_ma[index] - 0.3:
                el["close_dt"] = arrow.name
                el["open_chg"] = origin["chg_300"]
                el["close_chg"] = arrow["chg_300"]
                el["diff_chg"] = arrow["chg_300"] - origin["chg_300"]
                el["gap"] = gap(origin.name,arrow.name)
                el["res"] = "stop-ma-up"
                break
        elif direct == "down":
            edge = op_df["chg_300"][:index].min() - edgeMargin
            if op_df["chg_300"][index] > edge:
                el["close_dt"] = arrow.name
                el["open_chg"] = origin["chg_300"]
                el["close_chg"] = arrow["chg_300"]
                el["diff_chg"] = - arrow["chg_300"] + origin["chg_300"]
                el["gap"] = gap(origin.name,arrow.name)
                el["res"] = "stop-ss-dw"
                break
            if op_df["berry_300"][index] > berry_300_ma[index]  + 0.3:
                el["close_dt"] = arrow.name
                el["open_chg"] = origin["chg_300"]
                el["close_chg"] = arrow["chg_300"]
                el["diff_chg"] = - arrow["chg_300"] + origin["chg_300"]
                el["gap"] = gap(origin.name,arrow.name)
                el["res"] = "stop-ma-dw"
                break

    if "res" not in el:
        arrow = op_df.iloc[-1]
        el["close_dt"] = arrow.name
        el["open_chg"] = origin["chg_300"]
        el["close_chg"] = arrow["chg_300"]
        el["diff_chg"] = arrow["chg_300"] - origin["chg_300"]
        el["gap"] = gap(origin.name,arrow.name)
        el["res"] = "no-stop"
    PANEL.append(el)
    # print(el)



def gap(open_dt, close_dt):
    open_ts = pendulum.parse(open_dt,tz="Asia/Shanghai")
    close_ts = pendulum.parse(close_dt,tz="Asia/Shanghai")
    left_ts = pendulum.parse(open_dt,tz="Asia/Shanghai").add(hours = 11,minutes = 30)
    right_ts = pendulum.parse(open_dt,tz="Asia/Shanghai").add(hours = 11,minutes = 30)
    if open_ts <= left_ts and close_ts >= right_ts:
        duration = close_ts.diff(open_ts.add(hours=2)).in_seconds()
    else:
        duration = close_ts.diff(open_ts).in_seconds()
    return duration

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



if __name__ == '__main__':
    if len(sys.argv) == 2:
        night = sys.argv[-1]
        launch_solo(night)
    else:
        launch()
