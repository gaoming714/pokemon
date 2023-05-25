import re
import requests
import time
import json
import pendulum
import redis

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
option_dict = {}
op_data_list = []

def fetch_date():
    base_name = "300ETF"
    url = "http://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getStockName?exchange=null&cate=" + base_name
    res = requests.get(url, headers = SINA)
    res_dict = json.loads(res.text)
    month_list = list(set(res_dict["result"]["data"]["contractMonth"]))
    for month in month_list:
        pretty_month = month[2:4] + month[5:7]
        op_data_list.append(pretty_month)
    op_data_list.sort()
    # print(op_data_list)

def create_op_list(pre_name):
    # opdata_list = ['2304','2306','2309','2209']
    op_str_list = []
    for item in op_data_list:
        op_str_list.append(pre_name+item)
    print(op_str_list)
    return op_str_list

def fetch_op(name, op_list):
    names_url = "http://hq.sinajs.cn/list=" + ",".join(op_list)
    res = requests.get(names_url, headers = SINA)
    res_str = res.text
    #hq_str_op_list = re.findall('="[A-Z_0-9,]*";',res_str)
    hq_str_op_list = re.findall('CON_OP_\d*',res_str)
    option_dict[name] = hq_str_op_list
    # print(hq_str_op_list)

# def save_redis():
#     option_json = json.dumps(option_dict)
#     db.set("data/sina_op_config.json",option_json)
#     print(db.get("data/sina_op_config.json"))

def save_json():
    with open("data/sina_op_config.json", 'w', encoding='utf-8') as file:
        json.dump(option_dict, file, ensure_ascii=False)

# op_up_50_list = ["OP_UP_5100502201","OP_UP_5100502202","OP_UP_5100502203","OP_UP_5100502206"]
# op_down_50_list = ["OP_DOWN_5100502201","OP_DOWN_5100502202","OP_DOWN_5100502203","OP_DOWN_5100502206"]
# op_up_300_list = ["OP_UP_5103002201","OP_UP_5103002202","OP_UP_5103002203","OP_UP_5103002206"]
# op_down_300_list = ["OP_DOWN_5103002201","OP_DOWN_5103002202","OP_DOWN_5103002203","OP_DOWN_5103002206"]

if __name__ == '__main__':
    fetch_date()
    op_up_50_list = create_op_list('OP_UP_510050')
    op_down_50_list = create_op_list('OP_DOWN_510050')
    op_up_300_list = create_op_list('OP_UP_510300')
    op_down_300_list = create_op_list('OP_DOWN_510300')
    op_up_500_list = create_op_list('OP_UP_510500')
    op_down_500_list = create_op_list('OP_DOWN_510500')
    fetch_op("op_up_50",op_up_50_list)
    fetch_op("op_down_50",op_down_50_list)
    fetch_op("op_up_300",op_up_300_list)
    fetch_op("op_down_300",op_down_300_list)
    fetch_op("op_up_500",op_up_500_list)
    fetch_op("op_down_500",op_down_500_list)
    # save_redis()
    save_json()
