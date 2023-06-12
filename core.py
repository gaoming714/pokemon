import re
import os
import requests
import time
import json
import pendulum
import redis
# import pandas as pd
from flask import Flask
from flask import redirect, url_for
from flask import render_template

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
json_path = os.path.join("data", "sina_option_data.json")

app = Flask(__name__)


@app.route("/")
def index(name=None):
    return redirect("/op/plot")

@app.route("/op/<code>")
def oppage(code = "IF", name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    if not os.path.exists(json_path):
        mk_margin = pendulum.today("Asia/Shanghai").add(hours=9,minutes=30,seconds=10)
        remain = (mk_margin - now).total_seconds()
        return render_template('pedding.html',name=name, remain = str(remain))
    return render_template('op_'+code+'.html', name=name)



@app.route("/api/remain")
def api_remain(name=None):
    now = pendulum.now("Asia/Shanghai")
    dawn = pendulum.today("Asia/Shanghai")
    mk_mu = dawn.add(hours=9,minutes=20)
    mk_nu = dawn.add(hours=9,minutes=25)
    mk_alpha = dawn.add(hours=9,minutes=30)
    mk_beta = dawn.add(hours=11,minutes=30)
    mk_gamma = dawn.add(hours=13,minutes=0)
    mk_delta = dawn.add(hours=15,minutes=0)
    mk_zeta = pendulum.tomorrow("Asia/Shanghai")
    remain = 0

    """
        mu nu  9:30  alpha beta  12  gamma  delta  16 zeta
    """
    now = pendulum.now("Asia/Shanghai")
    # refresh remain per half-hour
    # if now.minute % 30 == 0:
    #     print(("JQData Remains => ",personal.jq_remains()))
    json_path = os.path.join("data", "sina_option_data.json")
    if not os.path.exists(json_path) and now > mk_alpha:
        print("Market Closed. Holiday")
        return ""


    #check market is closed
    # store it in redis by daily run tool
    # remain = mk_zeta - now
    # need to do
    if now < mk_alpha:
        print(["remain (s) ",(mk_alpha - now).total_seconds()])
        remain = (mk_alpha - now).total_seconds()
    elif now < mk_beta:
        pass
    elif now < mk_gamma:
        print(["remain (s) ",(mk_gamma - now).total_seconds()])
        remain = (mk_gamma - now).total_seconds()
    elif now < mk_delta:
        pass
    else:
        print("Market Closed")
        print(["remain to end (s) ",(mk_zeta - now).total_seconds()])
        remain = (mk_zeta - now).total_seconds()
        print("update to tomorrow")
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
        print(["remain (s) ",(mk_alpha - now).total_seconds()])
        status = '301'
        remain = (mk_alpha - now).total_seconds()
    elif now < mk_beta:
        status = '200'
    elif now < mk_gamma:
        print(["remain (s) ",(mk_gamma - now).total_seconds()])
        status = '302'
        remain = (mk_gamma - now).total_seconds()
    elif now < mk_delta:
        status = '200'
    else:
        print("Market Closed")
        print(["remain to end (s) ",(mk_zeta - now).total_seconds()])
        status = '303'
        remain = (mk_zeta - now).total_seconds()
        print("update to tomorrow")
    context = { 'status': status,
                'now': now.to_datetime_string(),
                'remain': remain,
    }
    return json.dumps(context)

@app.route("/api/op")
def api_op(name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    # get sum of vol from sina_option_data
    with open(json_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    last_time = option_dict['now']
    now_list = option_dict['now_list']

    pcr_50_list = option_dict['pcr_50']
    berry_50_list = option_dict['berry_50']
    pcr_300_list = option_dict['pcr_300']
    berry_300_list = option_dict['berry_300']
    pcr_500_list = option_dict['pcr_500']
    berry_500_list = option_dict['berry_500']

    burger_list = option_dict['burger']

    # df = pd.DataFrame(option_dict,index=option_dict["now_list"])
    # df = df.drop("now_list",axis=1)
    # df['burger_ma'] = MA(df['burger'],20)
    # burger_list = (df["berry_50"]/2+ df["berry_500"]/2 - df["pct_t0"]*10).to_list()
    # burger_list = df['burger_ma'].to_list()

    readme =  "30 -50- 70  ==   70 -90- 110"
    context = { 'now': now_str,
            'last_time': last_time,
            'now_list': now_list,
            'pcr_50': round(pcr_50_list[-1],2),
            'berry_50': round(berry_50_list[-1],2),
            'pcr_50_list': pcr_50_list,
            'berry_50_list': berry_50_list,

            'pcr_300': round(pcr_300_list[-1],2),
            'berry_300': round(berry_300_list[-1],2),
            'pcr_300_list': pcr_300_list,
            'berry_300_list': berry_300_list,

            'pcr_500': round(pcr_500_list[-1],2),
            'berry_500': round(berry_500_list[-1],2),
            'pcr_500_list': pcr_500_list,
            'berry_500_list': berry_500_list,

            'burger': round(burger_list[-1],2),
            'burger_list': burger_list,

            'readme': readme,
        }
    return json.dumps(context)


# def MA(S,N):
#     return pd.Series(S).rolling(N,min_periods=1).mean().values
# def STD(S,N):
#     return  pd.Series(S).rolling(N).std(ddof=0).values

if __name__ == '__main__':
    app.run(debug=True,port=8009)
#

