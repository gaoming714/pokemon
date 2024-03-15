import re
import os
import requests
import time
import json
import pendulum
import redis
import pandas as pd
from pathlib import Path
from flask import Flask
from flask import Response
from flask import redirect, url_for
from flask import render_template

from loguru import logger
logger.add("log/atom.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
json_path = os.path.join("data", "sina_option_data.json")
nightly_path = os.path.join("data", "nightly_data.json")

app = Flask(__name__)


@app.route("/")
def index(name=None):
    return redirect("/op/horizon")

@app.route("/op/<code>")
def oppage(code = "IF", name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    with open(json_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    if 'now' not in option_dict:
        mk_margin = pendulum.today("Asia/Shanghai").add(hours=9,minutes=30,seconds=15)
        remain = (mk_margin - now).total_seconds()
        return render_template('pedding.html',name=name, remain = str(remain))
    return render_template('op_'+code+'.html', name=name)

@app.route("/hist")
def histpage(name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    night_path = os.path.join("data","nightly_data.json")
    with open(night_path, 'r', encoding='utf-8') as file:
        json_dict = json.load(file)
    night_list = json_dict["time"][-60:]
    night_list.sort(reverse=True)
    return render_template('hist.html', name=name, night_list=night_list)


@app.route("/api/remain")
def api_remain(name=None):
    now = pendulum.now("Asia/Shanghai")
    dawn = pendulum.today("Asia/Shanghai")
    mk_mu = dawn.add(hours=9,minutes=20)
    mk_nu = dawn.add(hours=9,minutes=25)
    mk_alpha = dawn.add(hours=9,minutes=30)
    mk_beta = dawn.add(hours=11,minutes=30)
    mk_gamma = dawn.add(hours=13,minutes=0)
    mk_delta = dawn.add(hours=15,minutes=1)
    mk_zeta = pendulum.tomorrow("Asia/Shanghai")
    remain = 0

    """
        mu nu  9:30  alpha beta  12  gamma  delta  16 zeta
    """
    now = pendulum.now("Asia/Shanghai")
    # refresh remain per half-hour
    # if now.minute % 30 == 0:
    #     print(("JQData Remains => ",personal.jq_remains()))
    # json_path = os.path.join("data", "sina_option_data.json")
    # if not os.path.exists(json_path) and now > mk_alpha:
    #     print("Market Closed. Holiday")
    #     return ""


    #check market is closed
    # store it in redis by daily run tool
    # remain = mk_zeta - now
    # need to do
    if now < mk_alpha:
        # print(["remain (s) ",(mk_alpha - now).total_seconds()])
        remain = (mk_alpha - now).total_seconds()
    elif now < mk_beta:
        pass
    elif now < mk_gamma:
        # print(["remain (s) ",(mk_gamma - now).total_seconds()])
        remain = (mk_gamma - now).total_seconds()
    elif now < mk_delta:
        pass
    else:
        # print("Market Closed")
        # print(["remain to end (s) ",(mk_zeta - now).total_seconds()])
        remain = (mk_zeta - now).total_seconds()
        # print("update to tomorrow")
    return str(int(remain))

@app.route("/api/touch")
def api_touch(name=None):
    now = pendulum.now("Asia/Shanghai")
    dawn = pendulum.today("Asia/Shanghai")
    mk_mu = dawn.add(hours=9,minutes=20)
    mk_nu = dawn.add(hours=9,minutes=25)
    mk_alpha = dawn.add(hours=9,minutes=30,seconds=20)
    # mk_margin = dawn.add(hours=9,minutes=30,seconds=10)
    mk_beta = dawn.add(hours=11,minutes=30)
    mk_gamma = dawn.add(hours=13,minutes=0)
    mk_delta = dawn.add(hours=15,minutes=0)
    mk_zeta = pendulum.tomorrow("Asia/Shanghai")
    remain = 0

    """
        mu nu  9:30  alpha beta  12  gamma  delta  16 zeta
    """
    if now.day_of_week == pendulum.SATURDAY or now.day_of_week == pendulum.SUNDAY:
        context = { 'status': '310',
                'now': now.to_datetime_string(),
                'remain': '',
        }
        return json.dumps(context)

    json_path = os.path.join("data", "sina_option_data.json")
    if not os.path.exists(json_path) and now > mk_alpha:
        context = { 'status': '310',
                'now': now.to_datetime_string(),
                'remain': 0,
        }
        return json.dumps(context)

    if now < mk_alpha:
        # print(["remain (s) ",(mk_alpha - now).total_seconds()])
        status = '301'
        remain = (mk_alpha - now).total_seconds()
    elif now < mk_beta:
        status = '200'
    elif now < mk_gamma:
        # print(["remain (s) ",(mk_gamma - now).total_seconds()])
        status = '302'
        remain = (mk_gamma - now).total_seconds()
    elif now < mk_delta:
        status = '200'
    else:
        # print("Market Closed")
        # print(["remain to end (s) ",(mk_zeta - now).total_seconds()])
        status = '303'
        remain = (mk_zeta - now).total_seconds()
        # print("update to tomorrow")
    context = { 'status': status,
                'now': now.to_datetime_string(),
                'remain': remain,
    }
    return json.dumps(context)

@app.route("/api/op")
def api_op(name=None):
    # now = pendulum.now("Asia/Shanghai")
    # now_str = now.to_datetime_string()
    # get sum of vol from sina_option_data
    with open(json_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    if 'now' not in option_dict:
        return json.dumps({})
    now = option_dict['now']
    now_list = option_dict['now_list']
    with open(nightly_path, 'r', encoding='utf-8') as file:
        nightly_dict = json.load(file)

    pcr_50_list = option_dict['pcr_50']
    chg_50_list = option_dict['chg_50']
    berry_50_list = option_dict['berry_50']
    pcr_300_list = option_dict['pcr_300']
    chg_300_list = option_dict['chg_300']
    berry_300_list = option_dict['berry_300']
    pcr_500_list = option_dict['pcr_500']
    chg_500_list = option_dict['chg_500']
    berry_500_list = option_dict['berry_500']
    burger_list = option_dict['burger']
    std_list = option_dict['std_300']
    ma_300_list = list(MA(option_dict['berry_300'], 120))
    vol_mean = pd.Series(option_dict["vol_300"][-13:]).mean()
    vol_diff = (option_dict["vol_300"][-1] - vol_mean) / 1000
    vol_diff_series = create_list(option_dict["vol_300"])
    vol_diff_list = list((vol_diff_series)/1000)

    margin = -1.5 * pd.Series(option_dict["chg_300"][-481:-1]).std()
    if len(now_list) >= 300:
        horizon = 9 * pd.Series(option_dict["chg_300"][12:280]).std()
    else:
        horizon = 0

    if len(now_list) > 300:
        open_berry = option_dict['berry_300'][299]
        if open_berry >= 10:
            xbox_shuffle = 1
        elif open_berry <= -10:
            xbox_shuffle = -1
        else:
            xbox_shuffle = 0
        if ma_300_list[-1] > pd.Series(ma_300_list[-47:]).mean() + 0.47 and berry_300_list[-1] > ma_300_list[-1] + 1.5:
            apple_shuffle = 1
        elif ma_300_list[-1] < pd.Series(ma_300_list[-47:]).mean() - 0.47 and berry_300_list[-1] < ma_300_list[-1] - 1.5:
            apple_shuffle = -1
        else:
            apple_shuffle = 0
    else:
        xbox_shuffle = 0
        apple_shuffle = 0


    readme =  "Watch the fork and progress"
    context = {
            'now': now,
            'now_list': now_list,
            # 'pcr_50': round(pcr_50_list[-1],2),
            # 'berry_50': round(berry_50_list[-1],2),
            # 'pcr_50_list': pcr_50_list,
            # 'berry_50_list': berry_50_list,
            'chg_50': round(chg_50_list[-1],4),
            'chg_300': round(chg_300_list[-1],4),
            'chg_500': round(chg_500_list[-1],4),

            'pcr_300': round(pcr_300_list[-1],2),
            'berry_300': round(berry_300_list[-1],2),
            'pcr_300_list': pcr_300_list,
            'berry_300_list': berry_300_list,
            'ma_300_list': ma_300_list,
            'vol_diff': round(vol_diff, 2),
            'vol_list' : vol_diff_list,
            'margin': round(margin,4),
            'horizon': round(horizon,4),
            'std': round(std_list[-1],4),
            'std_list': std_list,

            # 'pcr_500': round(pcr_500_list[-1],2),
            # 'berry_500': round(berry_500_list[-1],2),
            # 'pcr_500_list': pcr_500_list,
            # 'berry_500_list': berry_500_list,

            'burger': round(burger_list[-1],2),
            'burger_list': burger_list,

            'xbox_shuffle': xbox_shuffle,
            'apple_shuffle': apple_shuffle,

            'readme': readme,
        }
    return json.dumps(context)

@app.route("/api/hist/<date>")
def api_hist(name = None, date = None):
    # now = pendulum.now("Asia/Shanghai")
    # now_str = now.to_datetime_string()
    # get sum of vol from sina_option_data
    hist_path = os.path.join("data",date+".json")
    with open(hist_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    if "now" not in option_dict:
        return json.dumps({})
    now = option_dict['now']
    now_list = option_dict['now_list']
    with open(nightly_path, 'r', encoding='utf-8') as file:
        nightly_dict = json.load(file)

    pcr_50_list = option_dict['pcr_50']
    chg_50_list = option_dict['chg_50']
    berry_50_list = option_dict['berry_50']
    pcr_300_list = option_dict['pcr_300']
    chg_300_list = option_dict['chg_300']
    berry_300_list = option_dict['berry_300']
    pcr_500_list = option_dict['pcr_500']
    chg_500_list = option_dict['chg_500']
    berry_500_list = option_dict['berry_500']
    burger_list = option_dict['burger']
    std_list = option_dict['std_300']

    margin = -1.5 * pd.Series(option_dict["chg_300"][-481:-1]).std()
    if len(now_list) >= 300:
        horizon = 9 * pd.Series(option_dict["chg_300"][12:280]).std()
    else:
        horizon = 0

    xbox_shuffle = nightly_dict['shuffle'][-1]
    yest_berry = nightly_dict['berry_300'][-1]
    diff_berry = berry_300_list[-1] - yest_berry
    if diff_berry > -2 and berry_300_list[-1] > 0:
        apple_shuffle = 1
    elif diff_berry < 2 and berry_300_list[-1] < 0:
        apple_shuffle = -1
    else:
        apple_shuffle = 0


    readme =  "Watch the fork and progress"
    context = {
            'now': now,
            'now_list': now_list,
            # 'pcr_50': round(pcr_50_list[-1],2),
            # 'berry_50': round(berry_50_list[-1],2),
            # 'pcr_50_list': pcr_50_list,
            # 'berry_50_list': berry_50_list,
            'chg_50': round(chg_50_list[-1],4),
            'chg_300': round(chg_300_list[-1],4),
            'chg_500': round(chg_500_list[-1],4),

            'chg_50_list': chg_50_list,
            'chg_300_list': chg_300_list,
            'chg_500_list': chg_500_list,

            'pcr_300': round(pcr_300_list[-1],2),
            'berry_300': round(berry_300_list[-1],2),
            'pcr_300_list': pcr_300_list,
            'berry_300_list': berry_300_list,
            'margin': round(margin,4),
            'horizon': round(horizon,4),
            'std': round(std_list[-1],4),
            'std_list': std_list,

            # 'pcr_500': round(pcr_500_list[-1],2),
            # 'berry_500': round(berry_500_list[-1],2),
            # 'pcr_500_list': pcr_500_list,
            # 'berry_500_list': berry_500_list,

            'burger': round(burger_list[-1],2),
            'burger_list': burger_list,

            'xbox_shuffle': xbox_shuffle,
            'apple_shuffle': apple_shuffle,

            'readme': readme,
        }
    return json.dumps(context)

@app.route('/welogin',methods=['GET','POST'])
def test_wechat():
    qr_path = Path("QR.png")
    if not qr_path.exists():
        return "<p>No QR.png.</p>"
    with open(qr_path, 'rb') as f:
        image = f.read()
    return Response(image, mimetype='image/jpeg')

def create_list(S):
    vol_mean_list = pd.Series(S).rolling(13).mean().values
    vol_series = (pd.Series(S) - vol_mean_list)
    vol_series.fillna(0, inplace=True)
    return vol_series

def MA(S,N):
    return pd.Series(S).rolling(N,min_periods = 1).mean().values



if __name__ == '__main__':
    app.run(debug=True,port=8009)
#

