

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



def launch():
    '''
    now_str is local
    now_online is the online time
    '''
    json_path = os.path.join("data", "sina_option_data.json")
    pickle_path = os.path.join("data", "sina_option_data.pickle")

    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()

    # now_online, pct_300 = fetch_stock("sh000300")
    now_online = fetch_time()
    pct_50 = fetch_future("nf_IH0")
    pct_300 = fetch_future("nf_IF0")
    pct_500 = fetch_future("nf_IC0")
    # pct_50 = fetch_stock("sh000016")
    # pct_300 = fetch_stock("sh000300")
    # pct_500 = fetch_future("nf_IF0")
    # pct_500 = fetch_stock("sh000905")
    # https://hq.sinajs.cn/list=nf_IC0,nf_IF0
    vol_up_50 = fetch_op_sum('op_up_50')
    vol_down_50 = fetch_op_sum('op_down_50')
    vol_up_300 = fetch_op_sum('op_up_300')
    vol_down_300 = fetch_op_sum('op_down_300')
    vol_up_500 = fetch_op_sum('op_up_300')
    vol_down_500 = fetch_op_sum('op_down_300')

    if vol_up_300 == 0:
        return

    # try:
    #     with open(json_path, 'r', encoding='utf-8') as file:
    #         option_dict = json.load(file)
    # except:
    #         option_dict = {
    #                         'pct_50':[],
    #                         'pcr_50':[],
    #                         'berry_50':[],
    #                         'pct_300':[],
    #                         'pcr_300':[],
    #                         'berry_300':[],
    #                         'pct_500':[],
    #                         'pcr_500':[],
    #                         'berry_500':[],
    #                         'now_list':[]
    #                     }
    if pendulum.today("Asia/Shanghai") == pendulum.parse(now_online,tz="Asia/Shanghai").at(0,0,0):
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                option_dict = json.load(file)
        except:
            option_dict = {
                            'pct_50':[],
                            'pcr_50':[],
                            'berry_50':[],
                            'pct_300':[],
                            'pcr_300':[],
                            'berry_300':[],
                            'pct_500':[],
                            'pcr_500':[],
                            'berry_500':[],
                            'now_list':[]
                        }
    else:
        backup_path = "data/" + now_online.split()[0] + ".json"
        if os.path.exists(json_path) and not os.path.exists(backup_path):
            backup_json(json_path, backup_path)
        return

    option_dict['now'] = now_str
    option_dict['now_list'].append(now_online)

    # option_dict['op_up_50'].append(vol_up_50)
    # option_dict['op_down_50'].append(vol_down_50)
    option_dict['pct_50'].append(pct_50)
    pcr_50 = vol_down_50 / vol_up_50 * 100
    mid_50 = vol_down_50 / vol_up_50 * 100 - 40
    berry_50 = (pct_50 * 5) + mid_50
    option_dict['pcr_50'].append(pcr_50)
    option_dict['berry_50'].append(berry_50)

    # option_dict['op_up_300'].append(vol_up_300)
    # option_dict['op_down_300'].append(vol_down_300)
    option_dict['pct_300'].append(pct_300)
    pcr_300 = vol_down_300 / vol_up_300 * 100
    mid_300 = vol_down_300 / vol_up_300 * 100 - 40
    berry_300 = (pct_300 * 10) + mid_300
    option_dict['pcr_300'].append(pcr_300)
    option_dict['berry_300'].append(berry_300)

    # option_dict['op_up_500'].append(vol_up_500)
    # option_dict['op_down_500'].append(vol_down_500)
    option_dict['pct_500'].append(pct_500)
    pcr_500 = vol_down_500 / vol_up_500 * 100
    mid_500 = vol_down_500 / vol_up_500 * 100 - 0
    berry_500 = (pct_500 * 50) + mid_500
    option_dict['pcr_500'].append(pcr_500)
    option_dict['berry_500'].append(berry_500)


    # print(option_dict)
    if now.hour <= 9 and now.minute <= 33:
        option_dict['berry_50'][-1] = 50
        option_dict['berry_300'][-1] = 50
        option_dict['berry_500'][-1] = 50

    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(option_dict, file, ensure_ascii=False)

    df = pd.DataFrame(option_dict,index=option_dict["now_list"])
    df = df.drop("now_list",axis=1)
    print(df)
    with open(pickle_path, 'wb') as f:
        pickle.dump(df, f)




def fetch_op_sum(op_name):
    # get sum of vol from one op_name
    with open("data/sina_op_config.json", 'r', encoding='utf-8') as file:
        sina_option_dict = json.load(file)
    # sina_option_dict = json.loads(db.get("data/sina_op_config.json"))
    hq_str_op_list = sina_option_dict[op_name]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(hq_str_op_list)
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    # print(res_str)
    hq_str_con_op_list = re.findall('="[\w,. -:购沽月]*',res_str)
    # print("========")
    vol_sum = 0
    for oneline in hq_str_con_op_list:
        tmp_list = oneline.split(",")
        if len(tmp_list) < 41:
            continue
        # print(tmp_list)
        vol_sum += int(tmp_list[41])
    return vol_sum


def fetch_stock(code):
    detail_url = "http://hq.sinajs.cn/list=" + code
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    res_tmp_list = res_str.split("=\"")[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[0]
    res_open = float(res_list[1])
    res_yest = float(res_list[2])
    res_price = float(res_list[3])
    res_pct = (res_price - res_yest) / res_yest * 100
    res_now = res_list[30] + " " + res_list[31]
    return res_pct

def fetch_time():
    detail_url = "http://hq.sinajs.cn/list=" + "sh000300"
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    res_tmp_list = res_str.split("=\"")[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[0]
    res_open = float(res_list[1])
    res_yest = float(res_list[2])
    res_price = float(res_list[3])
    res_pct = (res_price - res_yest) / res_yest * 100
    res_now = res_list[30] + " " + res_list[31]
    return res_now

def fetch_future(code):
    detail_url = "http://hq.sinajs.cn/list=" + code
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    res_tmp_list = res_str.split("=\"")[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[-1]
    res_open = float(res_list[0])
    res_yest = float(res_list[14])
    res_price = float(res_list[3])
    res_pct = (res_price - res_yest) / res_yest * 100
    res_now = res_list[36] + " " + res_list[37]
    return res_pct


#var hq_str_sh510300="沪深300ETF,4.103,4.103,4.030,4.106,4.024,4.031,4.032,683648627,2776624903.000,136700,4.031,35200,4.030,306800,4.029,1011700,4.028,161900,4.027,461200,4.032,221400,4.033,103900,4.034,117800,4.035,111800,4.036,2023-04-21,15:00:01,00,";
#var hq_str_sh000300="沪深300,3827.1634,3837.7531,3801.3870,3827.1634,3781.4034,0,0,105929375,202331293564,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2023-05-31,14:40:11,00,";
#var hq_str_nf_IH0="2663.000,2666.000,2637.000,2644.400,19752,52338702.000,38880.000,0.000,0.000,2932.000,2399.200,0.000,0.000,2661.400,2665.600,42815.000,2644.400,3,0.000,0,0.000,0,0.000,0,0.000,0,2644.600,2,0.000,0,0.000,0,0.000,0,0.000,0,2023-04-24,11:25:59,0,1,,,,,,,,,2649.793,上证50指数期货连续";


now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=30)
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



def backup_json(source,target):
    cmd = "mv " + source + " " + target
    lumos(cmd)


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
        time.sleep(5 - now.second % 5)