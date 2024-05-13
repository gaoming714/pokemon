import re
import os
import requests
import time
import json
import pendulum

from models import webDB
from models import jsonDB


from loguru import logger
logger.add("log/init.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
OPTIONS = {}


def launch():
    OPTIONS["expiry"] = webDB.option_expiry()
    # logger.info(OPTIONS["expiry"])
    for expiry in OPTIONS["expiry"]:
        fetch_op("510050C", 'OP_UP_510050', expiry)
        fetch_op("510050P", 'OP_DOWN_510050', expiry)
        fetch_op("510300C", 'OP_UP_510300', expiry)
        fetch_op("510300P", 'OP_DOWN_510300', expiry)
        fetch_op("510500C", 'OP_UP_510500', expiry)
        fetch_op("510500P", 'OP_DOWN_510500', expiry)
    jsonDB.create_init_data()
    add_expiry()
    json_path = os.path.join("data", "fox_op_config.json")
    jsonDB.save_it(json_path, OPTIONS)

def fetch_op(symbol, sina_symbol, expiry):
    hq_str_code_list = webDB.option_str_code(sina_symbol, expiry)
    OPTIONS[symbol+expiry] = hq_str_code_list

def add_expiry():
    code_list = jsonDB.option_codes("510300C")
    codeplus_list = ['CON_OP_' + item for item in code_list]
    deadline, left_list = webDB.option_expiry_left(codeplus_list)
    OPTIONS["expiry_day"] = left_list
    logger.info([str(deadline) + " days left.", *left_list])


def clean():
    # for pytest
    global OPTIONS
    OPTIONS = {}
    print(OPTIONS)


if __name__ == '__main__':
    launch()
