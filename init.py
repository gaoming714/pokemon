import re
import os
import requests
import time
import json
import pendulum
from pathlib import Path

from mars import webDB
from mars import jsonDB

from mars.util import logConfig, logger

logConfig("logs/init.log", rotation="10 MB")

OPTIONS = {}


def launch():
    OPTIONS["expiry"] = webDB.option_expiry()
    # logger.info(OPTIONS["expiry"])
    for expiry in OPTIONS["expiry"]:
        fetch_op("510050C", "OP_UP_510050", expiry)
        fetch_op("510050P", "OP_DOWN_510050", expiry)
        fetch_op("510300C", "OP_UP_510300", expiry)
        fetch_op("510300P", "OP_DOWN_510300", expiry)
        fetch_op("510500C", "OP_UP_510500", expiry)
        fetch_op("510500P", "OP_DOWN_510500", expiry)
    jsonDB.create_init_data()
    add_expiry()
    json_path = Path() / "data" / "fox_op_config.json"
    jsonDB.save_it(json_path, OPTIONS)


def fetch_op(symbol, sina_symbol, expiry):
    hq_str_code_list = webDB.option_str_code(sina_symbol, expiry)
    OPTIONS[symbol + expiry] = hq_str_code_list


def add_expiry():
    code_list = jsonDB.option_codes("510300C")
    codeplus_list = ["CON_OP_" + item for item in code_list]
    deadline, left_list = webDB.option_expiry_left(codeplus_list)
    OPTIONS["expiry_day"] = left_list
    logger.info(["{} days left.".format(deadline), *left_list])


def clean():
    # for pytest
    global OPTIONS
    OPTIONS = {}
    print(OPTIONS)


if __name__ == "__main__":
    launch()
