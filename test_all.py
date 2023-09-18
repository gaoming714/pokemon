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

### unit test
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

@freeze_time(online())
def test_unit_fetch_time():
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    res = fetch_time()
    assert now_str == res



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


@freeze_time(online())
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

@freeze_time(online())
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

@freeze_time(online().add(days=1))
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
