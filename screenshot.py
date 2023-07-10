

import re
import os
import sys
import requests
import time
import json
import pendulum
import pickle
import pandas as pd
import plotly.express as px

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}


BOX = []
DIRECT = []

def launch(json_path = os.path.join("data", "sina_option_data.json")):

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
    df.drop_duplicates(subset='now_list',inplace=True)
    df = df.drop("now_list",axis=1)
    # df = df.round({"berry_300":1})
    df["high_300"],df["mid_300"],df["low_300"] = BOLL(df["berry_300"], N = 240, P = 3 )
    df["std"] = STD(df["berry_300"], 240)
    # df = df.round({"std":4})

    print("Origin Signal")
    pd.Series(df["std"]).rolling(180).agg(lambda x:fix(x))
    print("Unique Signal")
    clean_sign()
    get_direct(df)

    print("\n时间\t\t\t 方向\t最大利润 平均利润 最大亏损")
    play(df["pct_300"])

    # df["high_300"] = df["high_300"].shift(24)
    # df["low_300"] = df["low_300"].shift(24)
    # se = df["berry_300"] < df["low_300"]
    # print(se)
    fig = px.line(df, x=df.index, y=["berry_300","burger","high_300","low_300","std"], title='Life expectancy in Canada')
    # fig.show()
    print("")

def clean_sign():
    global BOX
    out_box = []
    for index, item in enumerate(BOX):
        if index == 0:
            out_box.append(item)
            continue
        ltime = pendulum.parse(BOX[index-1], tz="Asia/Shanghai")
        rtime = pendulum.parse(BOX[index], tz="Asia/Shanghai")
        if ltime.add(minutes=5) < rtime:
            out_box.append(item)

    BOX = out_box
    print(BOX)

def get_direct(df):
    global BOX
    global DIRECT
    for item in BOX:
        if df["berry_300"][item] >= df["mid_300"][item]:
            DIRECT.append("up")
        else:
            DIRECT.append("down")
    print(DIRECT)

def play(inc_se):
    global BOX
    global DIRECT
    if BOX == []:
        return
    b_index = 0
    pct_cache = []
    for index in inc_se.index:
        value = inc_se[index]
        # print(index,value)
        btime = pendulum.parse(BOX[b_index], tz="Asia/Shanghai")
        ctime = pendulum.parse(index, tz="Asia/Shanghai")
        dtime = pendulum.parse(BOX[b_index], tz="Asia/Shanghai").add(minutes = 30)
        if dtime > btime.at(0,0,0).add(hours = 11,minutes = 30) and btime < btime.at(0,0,0).add(hours = 13):
            dtime = dtime.add(hours = 1, minutes = 30)
        if ctime > btime and ctime <= dtime:
            pct_cache.append(value)
        elif ctime > dtime:
            print("\nAction")
            best_max = max(pct_cache) - inc_se[BOX[b_index]]
            best_ave = sum(pct_cache)/len(pct_cache) - inc_se[BOX[b_index]]
            best_min = min(pct_cache) - inc_se[BOX[b_index]]
            if DIRECT[b_index] == "up":
                print([BOX[b_index], DIRECT[b_index], round(best_max * 100,2), round(best_ave * 100,2), round(best_min * 100,2)])
            else:
                print([BOX[b_index], DIRECT[b_index], -round(best_min * 100,2), -round(best_ave * 100,2), -round(best_max * 100,2),])

            pct_cache = []
            b_index = b_index + 1
            if len(BOX) <= b_index:
                break


def fix(S):
    std_mean = S[:60].mean()
    # if std_mean < 0.5:
    #     std_mean = 0.5
    # print(std_mean)
    std_arr = S[::-1]
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
            print(std_arr.index[0])
            BOX.append(std_arr.index[0])
    return 0

def UPPER(S,N):
    return pd.Series(S).rolling(N).max().values
def LOWER(S,N):
    return pd.Series(S).rolling(N).min().values

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
        json_path = os.path.join("data", sys.argv[-1])
        launch(json_path)
    else:
        launch()
