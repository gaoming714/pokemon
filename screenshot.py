

import re
import os
import sys
import requests
import time
import json
import pendulum
import pickle
import numpy as np
import pandas as pd
import plotly.express as px

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}


BOX = []
DIRECT = []
BERRY = []
PANEL = []

def launch():

    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()

    nightly_path = os.path.join("data", "nightly_data.json")

    with open(nightly_path, 'r', encoding='utf-8') as file:
        nightly_data = json.load(file)
    nightly_list = nightly_data["time"]

    with open(os.path.join("data", "sina_option_data.json"), 'r', encoding='utf-8') as file:
        sina_option_data = json.load(file)
        if "now" in sina_option_data:
            nightly_list.append("sina_option_data")
    print(nightly_list)
    for night in nightly_list:
        intraday_path = os.path.join("data", night + ".json")
        if os.path.exists(intraday_path):
            with open(intraday_path, 'r', encoding='utf-8') as file:
                intraday = json.load(file)
            analyse(intraday)

    show_df(len(nightly_list))

def show_df(days):
    global PANEL
    df = pd.DataFrame(PANEL)
    print(df)
    print(df.describe())
    print(df.sort_values("output"))
    # print(df["output"].cumsum())
    print(df["output"].sum()/days)
    # print(df[df["berry"]<-10][df["direct"]=="up"].sort_values("output"))
    # print(df[df["berry"]>10][df["direct"]=="down"].sort_values("output"))
    # print(df.sort_values("ave"))
    # print(df[df["berry"]>-10][df["direct"]=="up"].sort_values("ave"))
    # print(df[df["berry"]<10][df["direct"]=="down"].sort_values("ave"))
    # print(df[df["berry"]>-10][df["direct"]=="up"].sort_values("ave").describe())
    # print(df[df["berry"]<10][df["direct"]=="down"].sort_values("ave").describe())

    # print(df[df["ave"]>0])
def launch_solo(night):
    intraday_path = os.path.join("data", night + ".json")
    if os.path.exists(intraday_path):
        with open(intraday_path, 'r', encoding='utf-8') as file:
            intraday = json.load(file)
        df = analyse(intraday)


    df["edge_up"] = UPPER(df["chg_500"], N = 12 * 5, R = -8*0.01)
    df["edge_down"] = LOWER(df["chg_500"], N = 12 * 5, R = -8*0.01)
    fig = px.line(df, x=df.index, y=["chg_500","edge_up","edge_down"], title='')
    fig.show()
    show_df()

def analyse(option_dict):

    df = pd.DataFrame(option_dict,index=option_dict["now_list"])
    df.drop_duplicates(subset='now_list',inplace=True)
    df = df.drop("now_list",axis=1)
    # df = df.round({"berry_300":1})
    df["high_300"],df["mid_300"],df["low_300"] = BOLL(df["berry_300"], N = 180, P = 3 )
    if "std_300" not in df:
        df["std_300"] = STD(df["berry_300"], 240)
    # df = df.round({"std":4})

    # print("Origin Signal")
    pd.Series(df["std_300"]).rolling(180).agg(lambda x:fix(x))
    # print("Unique Signal")
    # print("Time\t-\t\tberry_300\t-\tmean_300")
    # clean_sign()
    get_direct(df)

    # print("\n时间\t\t\t 方向\t最大利润 平均利润 最大亏损")
    play(df["chg_500"],df["chg_300"])

    # df["high_300"] = df["high_300"].shift(24)
    # df["low_300"] = df["low_300"].shift(24)
    # se = df["berry_300"] < df["low_300"]
    # print(se)
    # fig = px.line(df, x=df.index, y=["berry_300","burger","high_300","low_300","std_300"], title='Life expectancy in Canada')
    # fig.show()
    return df


def get_direct(df):
    global BOX
    global DIRECT
    global BERRY
    out_box = []

    for index, item in enumerate(BOX):
        if index > 0:
            ltime = pendulum.parse(BOX[index-1], tz="Asia/Shanghai")
            rtime = pendulum.parse(BOX[index], tz="Asia/Shanghai")
            if ltime.add(minutes=5) > rtime:
                continue
        # print(item, df["berry_300"][item], df["mid_300"][item], df["berry_300"][item] - df["mid_300"][item])
        # if df["mid_300"][item] > 12 or df["mid_300"][item] > 12:
        #     print(item, df["berry_300"][item], df["mid_300"][item], "Attention")
        if df["berry_300"][item] >= df["mid_300"][item]:
            out_box.append(item)
            DIRECT.append("up")
        elif df["berry_300"][item] < df["mid_300"][item]:
            out_box.append(item)
            DIRECT.append("down")
        else:
            pass
        BERRY.append(df["mid_300"][item])
    BOX = out_box
    # print("Real Signal")
    # print(BOX)
    # print(DIRECT)

def play(chg_se,margin_se):
    global BOX
    global DIRECT
    global BERRY
    global PANEL

    for index, btime in enumerate(BOX):
        btime = pendulum.parse(BOX[index], tz="Asia/Shanghai")
        dtime = pendulum.parse(BOX[index], tz="Asia/Shanghai").add(minutes = 40)
        atime = pendulum.parse(BOX[index], tz="Asia/Shanghai").add(minutes = -40)
        if dtime > btime.at(0,0,0).add(hours = 11,minutes = 30) and dtime < btime.at(0,0,0).add(hours = 13):
            dtime = dtime.add(hours = 1, minutes = 30)
        if dtime >= btime.at(0,0,0).add(hours = 15):
            dtime = btime.at(0,0,0).add(hours = 15)
        if atime > btime.at(0,0,0).add(hours = 11,minutes = 30) and atime < btime.at(0,0,0).add(hours = 13):
            atime = dtime.add(hours = -1, minutes = -30)
        # cal cache
        cache = []
        for seindex,subvalue in chg_se[BOX[index]:].items():
            ctime = pendulum.parse(seindex, tz="Asia/Shanghai")
            cache.append(subvalue * 100)
            if ctime >= dtime:
                break

        # cal std(pre_cahce)
        pre_cache = []
        for seindex,subvalue in margin_se[:BOX[index]].items():
            ctime = pendulum.parse(seindex, tz="Asia/Shanghai")
            if ctime < atime:
                continue
            pre_cache.append(subvalue * 100)
        edgeMargin = -1.5 * np.std(pre_cache)
        # edgeMargin = -8
        # ana direct
        if DIRECT[index] == "up":
            for subindex, subchg in enumerate(cache):
                if subindex==0:continue
                edge = max(cache[0:subindex]) + edgeMargin
                if subchg <= edge or subindex == len(cache) -1:
                    PANEL.append({"time":BOX[index],"direct":DIRECT[index],"berry":BERRY[index],
                    "stoploss":edgeMargin,"duration":subindex*5/60,"output":round(subchg - cache[0],2)})
                    break
        if DIRECT[index] == "down":
            for subindex, subchg in enumerate(cache):
                if subindex==0:continue
                edge = min(cache[0:subindex]) - edgeMargin
                if subchg >= edge or subindex == len(cache) -1:
                    PANEL.append({"time":BOX[index],"direct":DIRECT[index],"berry":BERRY[index],
                    "stoploss":edgeMargin,"duration":subindex*5/60,"output":round(-(subchg - cache[0]),2)})
                    break
    BOX = []
    DIRECT = []
    BERRY = []






def fix(S):
    std_arr = S[::-1]
    if std_arr[0] == 0 or std_arr[120] == 0:
        return 0
    count = 0
    fail_count = 0
    for item in std_arr:
        if item < 1:
            count = count + 1
        elif fail_count < 4 and count < 8:
            fail_count = fail_count + 1
        else:
            break
    if count > 120:
        if fail_count != 0:
            # print(std_arr.index[0])
            BOX.append(std_arr.index[0])
    return 0

def UPPER(S,N,R):
    return pd.Series(S).rolling(N).max().values+R
def LOWER(S,N,R):
    return pd.Series(S).rolling(N).min().values-R

def MA(S,N):
    return pd.Series(S).rolling(N).mean().values

def STD(S,N):
    return  pd.Series(S).rolling(N).std().values

def BOLL(CLOSE,N=20, P=2):
    MID = MA(CLOSE, N);
    UPPER = MID + STD(CLOSE, N) * P
    LOWER = MID - STD(CLOSE, N) * P
    return UPPER, MID, LOWER


if __name__ == '__main__':
    if len(sys.argv) == 2:
        night = sys.argv[-1]
        launch_solo(night)
    else:
        launch()
