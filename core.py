import re
import os
import requests
import time
import json
import pendulum
import redis
from flask import Flask
from flask import redirect, url_for
from flask import render_template

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
json_path = os.path.join("data", "sina_option_data.json")

app = Flask(__name__)


@app.route("/")
def index(name=None):
    return redirect("/op/IM")


@app.route("/lite")
def lite(name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    if not os.path.exists(json_path):
        mk_alpha = pendulum.today("Asia/Shanghai").add(hours=9,minutes=30)
        remain = (mk_alpha - now).total_seconds()+10
        return render_template('pedding.html',name=name, remain = str(remain))
    # get sum of vol from sina_option_data
    with open(json_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    last_time = option_dict['now']
    now_list = option_dict['now_list']
    pcr_300_list = option_dict['pcr_300']
    berry_300_list = option_dict['berry_300']


    readme =  "30 -50- 70  ==   70 -90- 110"
    context = { 'now': now_str,
            'last_time': last_time,
            'now_list': now_list,
            'pcr_300': pcr_300_list[-1],
            'berry_300': berry_300_list[-1],
            'pcr_300_list': pcr_300_list,
            'berry_300_list': berry_300_list,
            'readme': readme,
        }
    return render_template('lite.html', name=name, **context)
    #return "<p>"+ str(now) +"    ==> "+ pretty_output + " % </p>"

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


@app.route("/api/lite")
def api_lite(name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    # get sum of vol from sina_option_data
    with open(json_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    last_time = option_dict['now']
    now_list = option_dict['now_list'][-600:]
    pcr_300_list = option_dict['pcr_300'][-600:]
    berry_300_list = option_dict['berry_300'][-600:]

    # print(now, " %.2f"% (output*100)," %")
    readme =  "30 -50- 70  ==   70 -90- 110"
    context = { 'now': now_str,
            'last_time': last_time,
            'now_list': now_list,
            'pcr_300': round(pcr_300_list[-1],2),
            'berry_300': round(berry_300_list[-1],2),
            'pcr_300_list': pcr_300_list,
            'berry_300_list': berry_300_list,
            'readme': readme,
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
    # bracket_50 = max(berry_50_list[-66:-6]), min(berry_50_list[-66:-6])
    pcr_300_list = option_dict['pcr_300']
    berry_300_list = option_dict['berry_300']
    pcr_500_list = option_dict['pcr_500']
    berry_500_list = option_dict['berry_500']


    # print(now, " %.2f"% (output*100)," %")
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
            'readme': readme,
        }
    return json.dumps(context)

@app.route("/op/<code>")
def oppage(code = "IF", name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    if not os.path.exists(json_path):
        mk_alpha = pendulum.today("Asia/Shanghai").add(hours=9,minutes=30,seconds=10)
        remain = (mk_alpha - now).total_seconds()
        return render_template('pedding.html',name=name, remain = str(remain))
    return render_template('op_'+code+'.html', name=name)

def fetch_sum(op_list):
    names_url = "http://hq.sinajs.cn/list=" + ",".join(op_list)
    res = requests.get(names_url, headers=SINA)
    res_str = res.text
    #hq_str_op_list = re.findall('="[A-Z_0-9,]*";',res_str)
    hq_str_op_list = re.findall('CON_OP_\d*',res_str)
    #print(hq_str_op_list)

    detail_url = "http://hq.sinajs.cn/list=" + ",".join(hq_str_op_list)
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    #print(res_str)
    hq_str_con_op_list = re.findall('="[\w,. -:购沽月]*',res_str)
    #print("========")
    vol_sum = 0
    for oneline in hq_str_con_op_list:
        tmp_list = oneline.split(",")
        print(tmp_list)
        vol_sum += int(tmp_list[41])
    return vol_sum

def fetch_lite(op_name):
    # get sum of vol from one op_name
    with open("sina_option.json", 'r', encoding='utf-8') as file:
        sina_option_dict = json.load(file)
    # sina_option_dict = json.loads(db.get("sina_option.json"))
    hq_str_op_list = sina_option_dict[op_name]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(hq_str_op_list)
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    print(res_str)
    hq_str_con_op_list = re.findall('="[\w,. -:购沽月]*',res_str)
    print("========")
    vol_sum = 0
    for oneline in hq_str_con_op_list:
        tmp_list = oneline.split(",")
        if len(tmp_list) < 41:
            continue
        print(tmp_list)
        vol_sum += int(tmp_list[41])
    return vol_sum
if __name__ == '__main__':
    app.run(debug=True,port=8009)
#

