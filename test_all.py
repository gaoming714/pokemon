import os
import time
import json
import pytest
import pendulum
import requests

from freezegun import freeze_time
from util import online, lumos
from loguru import logger

from runtime_sina import fetch_op_sum
from runtime_sina import fetch_time
from runtime_sina import launch as sina_launch

from runtime_chat import launch as chat_launch
from runtime_chat import clean as chat_clean

from init import launch as init_launch
from init import fetch_settle as init_fetch_settle
from init import create_op_list as init_create_op_list
from init import fetch_op as init_fetch_op
from init import clean as init_clean
from init import option_dict as init_option_dict


### unit test
def test_unit_init_fetch_settle():
    settle_list = init_fetch_settle()
    assert len(settle_list) == 4
    for month in settle_list:
        assert len(month) == 4

def test_unit_init_fetch_op():
    settle_list = init_fetch_settle()
    op_up_50_list = init_create_op_list('OP_UP_510050', settle_list)
    op_down_50_list = init_create_op_list('OP_DOWN_510050', settle_list)
    assert init_option_dict == {}
    init_fetch_op("A",op_up_50_list)
    init_fetch_op("B",op_down_50_list)
    assert "A" in init_option_dict
    assert "B" in init_option_dict
    assert len(init_option_dict["A"]) == 54
    assert len(init_option_dict["B"]) == 54
    init_clean()

def test_unit_fetch_op_sum():
    vol_up_50 = fetch_op_sum('op_up_50')
    vol_down_50 = fetch_op_sum('op_down_50')
    vol_up_300 = fetch_op_sum('op_up_300')
    vol_down_300 = fetch_op_sum('op_down_300')
    vol_up_500 = fetch_op_sum('op_up_500')
    vol_down_500 = fetch_op_sum('op_down_500')

    assert vol_up_50 != 0
    assert vol_down_50 != 0
    assert vol_up_300 != 0
    assert vol_down_300 != 0
    assert vol_up_500 != 0
    assert vol_down_500 != 0

@freeze_time(online(), tz_offset=+8)
def test_unit_fetch_time():
    time.sleep(3)
    now_local = pendulum.now("UTC")
    now_online = pendulum.parse(fetch_time())
    diff_minutes = abs(now_local.diff(now_online).in_minutes())
    assert diff_minutes < 1


### config test
def test_config_smoke_exists():
    mixin_list = [
        [os.path.join("data", "chat_config.json"),"email","handle","addr_list","user_list","chatroom_list"],
        [os.path.join("data", "nightly_data.json"),"time","chg_300","pcr_300","berry_300","shuffle"],
        [os.path.join("data", "sina_op_config.json"),"op_up_300"],
        [os.path.join("data", "sina_option_data.json"),"chg_300"],
    ]
    for mixin in mixin_list:
        json_path = None
        for item in mixin:
            if json_path == None:
                assert os.path.exists(item)
                json_path = item
                with open(json_path, 'r', encoding='utf-8') as file:
                    json_dict = json.load(file)
            else:
                assert item in json_dict



### function test

### function test
def test_func_init(env_full):
    lumos("rm data/*")
    file_list = ["chat_config.json", "nightly_data.json", "sina_op_config.json", "sina_option_data.json"]
    for file in file_list:
        file_path = os.path.join("data",file)
        assert os.path.exists(file_path) == False

    init_launch()

    with open(os.path.join("data","sina_op_config.json"), 'r', encoding='utf-8') as file:
        json_dict = json.load(file)

    assert len(json_dict["op_up_50"]) == len(json_dict["op_down_50"])
    assert len(json_dict["op_up_300"]) == len(json_dict["op_down_300"])
    assert len(json_dict["op_up_500"]) == len(json_dict["op_down_500"])
    assert len(json_dict["op_up_50"]) == 54
    assert len(json_dict["op_up_300"]) == 47
    assert len(json_dict["op_up_500"]) == 44

    with open(os.path.join("data","sina_option_data.json"), 'r', encoding='utf-8') as file:
        json_dict = json.load(file)
    assert "now" not in json_dict

    mixin_list = [
        [os.path.join("data", "chat_config.json"),"email","handle","addr_list","user_list","chatroom_list"],
        [os.path.join("data", "nightly_data.json"),"time","chg_300","pcr_300","berry_300","shuffle"],
        [os.path.join("data", "sina_op_config.json"),"op_up_50", "op_down_50", "op_up_300", "op_down_300", "op_up_500", "op_down_500"],
        [os.path.join("data", "sina_option_data.json"),"chg_50","pcr_50","berry_50","inc_t0","std_300","now_list"],
    ]
    for mixin in mixin_list:
        json_path = None
        for item in mixin:
            if json_path == None:
                assert os.path.exists(item)
                json_path = item
                with open(json_path, 'r', encoding='utf-8') as file:
                    json_dict = json.load(file)
            else:
                assert item in json_dict

def test_func_chat_send_up(env_func_chat_send_up):
    err = ""
    chat_clean()
    try:
        chat_launch()
    except Exception as e:
        err = str(e)
    assert "127.0.0.1" in err
    assert "8010" in err
    assert "up" in err

def test_func_chat_send_down(env_func_chat_send_down):
    err = ""
    chat_clean()
    try:
        chat_launch()
    except Exception as e:
        err = str(e)
    assert "127.0.0.1" in err
    assert "8010" in err
    assert "down" in err


@freeze_time(online(), tz_offset=+8)
def test_func_sina(env_full):
    data_path = os.path.join("data","sina_option_data.json")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    with open(data_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    length = len(option_dict["now_list"])

    sina_launch()
    with open(data_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    for key, value in option_dict.items():
        if key == "now":
            assert value.split()[0] == now_str.split()[0]
        else:
            assert len(value) == length + 1

@freeze_time(online(), tz_offset=+8)
def test_func_sina_first(env_full):
    data_path = os.path.join("data","sina_option_data.json")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    init_dict = {
                'chg_50':[],
                'pcr_50':[],
                'berry_50':[],
                'chg_300':[],
                'pcr_300':[],
                'berry_300':[],
                'chg_500':[],
                'pcr_500':[],
                'berry_500':[],
                'inc_t0':[],
                'burger':[],
                'std_300':[],
                'now_list':[]
            }
    with open(data_path, 'w', encoding='utf-8') as file:
        json.dump(init_dict, file, ensure_ascii=False)
    # empty sina_option_data.json

    length = len(init_dict["now_list"]) # 0
    sina_launch()
    with open(data_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    for key, value in option_dict.items():
        if key == "now":
            assert value.split()[0] == now_str.split()[0]
        else:
            assert len(value) == length + 1

@freeze_time(online().add(days=1), tz_offset=+8)
def test_func_sina_nightly(env_full):
    data_path = os.path.join("data","sina_option_data.json")
    with open(data_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    date_online = online().to_datetime_string().split()[0]
    hist_path = os.path.join("data", date_online + ".json")
    assert os.path.exists(hist_path) == False

    sina_launch()
    assert os.path.exists(hist_path) == True

    with open(hist_path, 'r', encoding='utf-8') as file:
        hist_dict = json.load(file)
    assert option_dict["now_list"] == hist_dict["now_list"]

    with open(data_path, 'r', encoding='utf-8') as file:
        option_dict = json.load(file)
    assert "now" not in option_dict




# function test fixture
@pytest.fixture
def env_func_chat_send_up(env_full):
    # prepare option_data.json
    # wait for sending signal
    lumos("cp test/chat/send_up.json data/sina_option_data.json")
    logger.debug("send up")
    yield

@pytest.fixture
def env_func_chat_send_down(env_full):
    #prepare option_data.json
    # it will send signal
    lumos("cp test/chat/send_down.json data/sina_option_data.json")
    logger.debug("send down")
    yield

@pytest.fixture
def env_full():
    # use data folder as tmp dir
    # stash
    lumos("mv data data.bac")
    # create env
    lumos("mkdir data")
    lumos("cp test/material/* data/")
    logger.debug("on yield")
    yield
    # clean env
    lumos("rm -r data")
    # stash pop
    lumos("mv data.bac data")
