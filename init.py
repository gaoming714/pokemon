import re
import os
import requests
import time
import json
import pendulum
import redis

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
option_dict = {}


def launch():
    settle_list = fetch_settle()
    op_up_50_list = create_op_list('OP_UP_510050', settle_list)
    op_down_50_list = create_op_list('OP_DOWN_510050', settle_list)
    op_up_300_list = create_op_list('OP_UP_510300', settle_list)
    op_down_300_list = create_op_list('OP_DOWN_510300', settle_list)
    op_up_500_list = create_op_list('OP_UP_510500', settle_list)
    op_down_500_list = create_op_list('OP_DOWN_510500', settle_list)
    fetch_op("op_up_50",op_up_50_list)
    fetch_op("op_down_50",op_down_50_list)
    fetch_op("op_up_300",op_up_300_list)
    fetch_op("op_down_300",op_down_300_list)
    fetch_op("op_up_500",op_up_500_list)
    fetch_op("op_down_500",op_down_500_list)
    create_data()
    add_settle()
    # save_redis()
    save_json()

def fetch_settle():
    settle_list = []
    base_name = "300ETF"
    url = "http://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getStockName?exchange=null&cate=" + base_name
    res = requests.get(url, headers = SINA)
    res_dict = json.loads(res.text)
    month_list = list(set(res_dict["result"]["data"]["contractMonth"]))
    for month in month_list:
        pretty_month = month[2:4] + month[5:7]
        settle_list.append(pretty_month)
    settle_list.sort()
    return settle_list

def create_op_list(pre_name, settle_list):
    # opdata_list = ['2304','2306','2309','2209']
    op_str_list = []
    for item in settle_list:
        op_str_list.append(pre_name+item)
    print(op_str_list)
    return op_str_list

def fetch_op(name, op_list):
    names_url = "http://hq.sinajs.cn/list=" + ",".join(op_list)
    res = requests.get(names_url, headers = SINA, timeout=5)
    res_str = res.text
    #hq_str_op_list = re.findall('="[A-Z_0-9,]*";',res_str)
    hq_str_op_list = re.findall(r'CON_OP_\d*',res_str)
    option_dict[name] = hq_str_op_list

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
#     option_json = json.dumps(option_dict)
#     db.set("data/sina_op_config.json",option_json)
#     print(db.get("data/sina_op_config.json"))

def add_settle():
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(option_dict["op_up_300"])
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
    option_dict["settle"] = date_list
    print([str(deadline) + " days left.", *date_list])

def save_json():
    with open("data/fox_op_config.json", 'w', encoding='utf-8') as file:
        json.dump(option_dict, file, ensure_ascii=False)

def clean():
    # for pytest
    global option_dict
    option_dict = {}
    print(option_dict)

# op_up_50_list = ["OP_UP_5100502201","OP_UP_5100502202","OP_UP_5100502203","OP_UP_5100502206"]
# op_down_50_list = ["OP_DOWN_5100502201","OP_DOWN_5100502202","OP_DOWN_5100502203","OP_DOWN_5100502206"]
# op_up_300_list = ["OP_UP_5103002201","OP_UP_5103002202","OP_UP_5103002203","OP_UP_5103002206"]
# op_down_300_list = ["OP_DOWN_5103002201","OP_DOWN_5103002202","OP_DOWN_5103002203","OP_DOWN_5103002206"]

if __name__ == '__main__':
    launch()
