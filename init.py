import re
import os
import requests
import time
import json
import pendulum
import redis

from loguru import logger
logger.add("log/init.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
OPTIONS = {}


def launch():
    fetch_expiry()
    logger.info(OPTIONS["expiry"])
    fetch_op("510050C", 'OP_UP_510050')
    fetch_op("510050P", 'OP_DOWN_510050')
    fetch_op("510300C", 'OP_UP_510300')
    fetch_op("510300P", 'OP_DOWN_510300')
    fetch_op("510500C", 'OP_UP_510500')
    fetch_op("510500P", 'OP_DOWN_510500')
    create_data()
    add_expiry()
    # save_redis()
    save_json()
#var hq_str_CON_SO_10007040="50ETF购5月2500,,,,132800,0.7981,4.965,-0.3219,0.1298,0.1241,0.0590,0.0397,510050C2405M02500,2.5000,0.0529,0.0528,M";

def fetch_expiry():
    base_name = "300ETF"
    url = "http://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getStockName?exchange=null&cate=" + base_name
    res = requests.get(url, headers = SINA)
    res_dict = json.loads(res.text)
    month_list = list(set(res_dict["result"]["data"]["contractMonth"]))
    expiry_list = []
    for month in month_list:
        pretty_month = month[2:4] + month[5:7]
        expiry_list.append(pretty_month)
    expiry_list.sort()
    OPTIONS["expiry"] = expiry_list

def fetch_op(name, sina_name):
    # op_list = [sina_name + x for x in OPTIONS["expiry"]]
    # print(op_list)
    # names_url = "http://hq.sinajs.cn/list=" + ",".join(op_list)
    # res = requests.get(names_url, headers = SINA, timeout=5)
    # res_str = res.text
    # #hq_str_op_list = re.findall('="[A-Z_0-9,]*";',res_str)
    # hq_str_op_list = re.findall(r'CON_OP_\d*',res_str)
    # hq_str_code_list = [item.split("_")[-1] for item in hq_str_op_list]
    # # print(hq_str_code_list)
    # OPTIONS[name] = hq_str_code_list
    for expiry in OPTIONS["expiry"]:
        url = "http://hq.sinajs.cn/list=" + sina_name + expiry
        res = requests.get(url, headers = SINA, timeout=5)
        res_str = res.text
        #hq_str_op_list = re.findall('="[A-Z_0-9,]*";',res_str)
        hq_str_op_list = re.findall(r'CON_OP_\d*',res_str)
        hq_str_code_list = [item.split("_")[-1] for item in hq_str_op_list]
        OPTIONS[name+expiry] = hq_str_code_list
        # print(hq_str_code_list)



def create_data():
    intraday_data_json = os.path.join("data", "fox_data.json")
    nightly_data_json = os.path.join("data", "fox_nightly.json")
    chat_config_json = os.path.join("data", "chat_config.json")
    if not os.path.exists(intraday_data_json):
        init_intraday = { "data":[] }
        with open(intraday_data_json, 'w', encoding='utf-8') as file:
            json.dump(init_intraday, file, ensure_ascii=False)
        print("create sina_option_data.json")
    if not os.path.exists(nightly_data_json):
        init_nightly = {"data": [], "records":["1970-01-01"]}
        with open(nightly_data_json, 'w', encoding='utf-8') as file:
            json.dump(init_nightly, file, ensure_ascii=False)
        print("create nightly_data.json")
    if not os.path.exists(chat_config_json):
        init_chat = {"email":{"smtp":"","port":"","login":"","password":"","from":""},"handle":1,"addr_list":[""],"user_list":[""],"chatroom_list":[""]}
        with open(chat_config_json, 'w', encoding='utf-8') as file:
            json.dump(init_chat, file, ensure_ascii=False)
        print("create chat_config.json")

# def save_redis():
#     option_json = json.dumps(OPTIONS)
#     db.set("data/sina_op_config.json",option_json)
#     print(db.get("data/sina_op_config.json"))

def add_expiry():
    expiry_list = OPTIONS["expiry"]
    code_list = []
    for expiry in expiry_list:
        one_list = ['CON_OP_' + item for item in OPTIONS["510300C"+expiry]]
        code_list.extend(one_list)
    # code_list = ['CON_OP_' + item for item in OPTIONS["510300C"]]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(code_list)
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    hq_str_con_op_list = res_str.split(";\n")
    date_list = []
    deadline_list = []
    for oneline in hq_str_con_op_list:
        sub_list = oneline.split(",")
        if "var hq_str_CON_OP_" not in sub_list[0] or len(sub_list) < 41:
            continue
        sub_date = sub_list[46]
        sub_days = int(sub_list[47])
        date_list.append(sub_date)
        deadline_list.append(sub_days)
    date_list = list(set(date_list))
    date_list.sort()
    deadline = min(deadline_list)
    OPTIONS["expiry_day"] = date_list
    logger.info([str(deadline) + " days left.", *date_list])

def save_json():
    with open("data/fox_op_config.json", 'w', encoding='utf-8') as file:
        json.dump(OPTIONS, file, ensure_ascii=False)

def clean():
    # for pytest
    global OPTIONS
    OPTIONS = {}
    print(OPTIONS)



if __name__ == '__main__':
    launch()
