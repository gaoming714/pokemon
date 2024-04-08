import os
import time
import json
import pytest
import pendulum
import requests

from freezegun import freeze_time
from util import online, lumos
from loguru import logger

import runtime_fox
import runtime_chat
import init

clock = pendulum.now("Asia/Shanghai")
clock_str = clock.to_datetime_string()

### unit test
def test_unit_init_fetch_settle():
    settle_list = init.fetch_settle()
    assert len(settle_list) == 4
    for month in settle_list:
        assert len(month) == 4

def test_unit_init_fetch_op():
    settle_list = init.fetch_settle()
    op_up_50_list = init.create_op_list('OP_UP_510050', settle_list)
    op_down_50_list = init.create_op_list('OP_DOWN_510050', settle_list)
    assert init.option_dict == {}
    init.fetch_op("A",op_up_50_list)
    init.fetch_op("B",op_down_50_list)
    assert "A" in init.option_dict
    assert "B" in init.option_dict
    assert len(init.option_dict["A"]) > 10
    assert len(init.option_dict["B"]) > 10
    init.clean()

def test_unit_fox_fetch_op_sum(init_ready):
    vol_up_50 = runtime_fox.fetch_op_sum('op_up_50')
    vol_down_50 = runtime_fox.fetch_op_sum('op_down_50')
    vol_up_300 = runtime_fox.fetch_op_sum('op_up_300')
    vol_down_300 = runtime_fox.fetch_op_sum('op_down_300')
    vol_up_500 = runtime_fox.fetch_op_sum('op_up_500')
    vol_down_500 = runtime_fox.fetch_op_sum('op_down_500')

    assert type(vol_up_50) == type(0)
    assert type(vol_down_50) == type(0)
    assert type(vol_up_300) == type(0)
    assert type(vol_down_300) == type(0)
    assert type(vol_up_500) == type(0)
    assert type(vol_down_500) == type(0)

    assert vol_up_50 != 0
    assert vol_down_50 != 0
    assert vol_up_300 != 0
    assert vol_down_300 != 0
    assert vol_up_500 != 0
    assert vol_down_500 != 0

@freeze_time(online(), tz_offset=+8)
def test_unit_fetch_time():
    "test freeze works, now_local ~= now_online"
    time.sleep(2)
    now_local = pendulum.now("UTC")
    print(now_local)
    now_online = pendulum.parse(runtime_fox.fetch_time())
    print(now_online)
    diff_minutes = abs(now_local.diff(now_online).in_minutes())
    assert diff_minutes < 1

def test_unit_init_create_data(init_create_fixture):
    intraday_data_json = os.path.join("data", "fox_data.json")
    nightly_data_json = os.path.join("data", "fox_nightly.json")
    chat_config_json = os.path.join("data", "chat_config.json")
    assert not os.path.exists(intraday_data_json)
    assert not os.path.exists(nightly_data_json)
    assert not os.path.exists(chat_config_json)
    init.create_data()
    assert os.path.exists(intraday_data_json)
    with open(intraday_data_json, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
        assert "data" in op_dict
    assert os.path.exists(nightly_data_json)
    with open(nightly_data_json, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
        assert "data" in op_dict
        assert "records" in op_dict
    assert os.path.exists(chat_config_json)
    with open(chat_config_json, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
        assert "email" in op_dict
    # raise ValueError("Fixture failed for some reason")


### config test
def test_config_smoke_exists(init_ready):
    mixin_list = [
        [os.path.join("data", "chat_config.json"),"email","handle","addr_list","user_list","chatroom_list"],
        [os.path.join("data", "fox_data.json"),"data"],
        [os.path.join("data", "fox_nightly.json"),"data","records"],
        [os.path.join("data", "fox_op_config.json"),"op_up_50"],
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
def test_func_init(env_basic):
    file_list = ["chat_config.json", "fox_data.json", "fox_op_config.json", "fox_nightly.json"]
    for file in file_list:
        file_path = os.path.join("data",file)
        assert os.path.exists(file_path) == False

    init.launch()

    with open(os.path.join("data","fox_op_config.json"), 'r', encoding='utf-8') as file:
        json_dict = json.load(file)

    assert len(json_dict["op_up_50"]) == len(json_dict["op_down_50"])
    assert len(json_dict["op_up_300"]) == len(json_dict["op_down_300"])
    assert len(json_dict["op_up_500"]) == len(json_dict["op_down_500"])
    assert len(json_dict["op_up_50"]) > 10
    assert len(json_dict["op_up_300"]) > 10
    assert len(json_dict["op_up_500"]) > 10

    with open(os.path.join("data","fox_data.json"), 'r', encoding='utf-8') as file:
        json_dict = json.load(file)
    assert "now" not in json_dict

    mixin_list = [
        [os.path.join("data", "chat_config.json"),"email","handle","addr_list","user_list","chatroom_list"],
        [os.path.join("data", "fox_data.json"),"data"],
        [os.path.join("data", "fox_nightly.json"),"data","records"],
        [os.path.join("data", "fox_op_config.json"),"op_up_50"],
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

### function test chat
@freeze_time(clock.at(9,40,0))
def test_func_chat_Tesla_not_open(chat_ready, mocker):
    try:
        lumos("cp test/chat/Tesla_up.json data/fox_data.json")
    except Exception as e:
        print(f"Copy failed with error: {e}")
        raise ValueError("Copy failed, File conflict => fox_data.json")
    runtime_chat.launch()
    assert runtime_chat.owl.call_count == 0
    assert runtime_chat.send_db.call_count == 0

@freeze_time(clock.at(10,0,0))
def test_func_chat_Tesla_normal(chat_ready, mocker):
    try:
        lumos("cp test/chat/Tesla_normal.json data/fox_data.json")
    except Exception as e:
        print(f"Copy failed with error: {e}")
        raise ValueError("Copy failed, File conflict => fox_data.json")
    runtime_chat.launch()
    assert runtime_chat.owl.call_count == 0
    assert runtime_chat.send_db.call_count == 0

@freeze_time(clock.at(10,0,0))
def test_func_chat_Tesla_up(chat_ready, mocker):
    try:
        lumos("cp test/chat/Tesla_up.json data/fox_data.json")
    except Exception as e:
        print(f"Copy failed with error: {e}")
        raise ValueError("Copy failed, File conflict => fox_data.json")
    runtime_chat.launch()
    assert runtime_chat.owl.call_count == 1
    assert runtime_chat.send_db.call_count == 1


@freeze_time(clock.at(10,0,0))
def test_func_chat_Tesla_down(chat_ready, mocker):
    try:
        lumos("cp test/chat/Tesla_down.json data/fox_data.json")
    except Exception as e:
        print(f"Copy failed with error: {e}")
        raise ValueError("Copy failed, File conflict => fox_data.json")
    runtime_chat.launch()
    assert runtime_chat.owl.call_count == 1
    assert runtime_chat.send_db.call_count == 1



@freeze_time(online(), tz_offset=+8)
def test_func_fox(market_opening):
    data_path = os.path.join("data","fox_data.json")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    with open(data_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    old_length = len(op_dict["data"])

    runtime_fox.launch()
    with open(data_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    new_length = len(op_dict["data"])
    assert new_length == old_length + 1
    assert op_dict["now"] == now_str


@freeze_time(online(), tz_offset=+8)
def test_func_fox_first(init_ready):
    data_path = os.path.join("data","fox_data.json")
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    with open(data_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    assert "now" not in op_dict
    old_length = len(op_dict["data"])

    runtime_fox.launch()
    with open(data_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    new_length = len(op_dict["data"])
    assert new_length == old_length + 1
    assert op_dict["now"] == now_str


@freeze_time(online().add(days=1), tz_offset=+8)
def test_func_fox_nightly(market_opening):
    data_path = os.path.join("data","fox_data.json")
    nightly_path = os.path.join("data","fox_nightly.json")
    with open(data_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    date_online = online().to_datetime_string().split()[0]
    hist_path = os.path.join("data", date_online + ".json")
    assert os.path.exists(hist_path) == False

    runtime_fox.launch()
    assert os.path.exists(hist_path) == True

    with open(hist_path, 'r', encoding='utf-8') as file:
        hist_dict = json.load(file)
    assert op_dict == hist_dict

    with open(nightly_path, 'r', encoding='utf-8') as file:
        nightly_dict = json.load(file)
    assert date_online in nightly_dict["records"]

    with open(data_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    assert "now" not in op_dict




# function test fixture
# @pytest.fixture
# def env_func_chat_send_up(env_basic):
#     # prepare option_data.json
#     # wait for sending signal
#     lumos("cp test/chat/send_up.json data/fox_data.json")
#     logger.debug("send up")
#     yield

# @pytest.fixture
# def env_func_chat_send_down(env_basic):
#     #prepare option_data.json
#     # it will send signal
#     lumos("cp test/chat/send_down.json data/fox_data.json")
#     logger.debug("send down")
#     yield

@pytest.fixture
def env_basic():
    if os.path.exists("data.bac"):
        raise ValueError("Fixture failed, Folder conflict => data.bac")
    try:
        lumos("mv data data.bac")
        # create env
        lumos("mkdir data")
        # lumos("cp test/material/* data/")
        # logger.debug("on yield")
        yield
    except Exception as e:
        print(f"Fixture failed with error: {e}")
    finally:
        print("Cleaning up in finally block")
        lumos("rm -r data")
        lumos("mv data.bac data")

@pytest.fixture
def init_ready(env_basic):
    try:
        init.launch()
        yield
    except Exception as e:
        print(f"Fixture failed with error: {e}")
        pass
    finally:
        print("Cleaning up in init_ready")
        pass

@pytest.fixture
def market_opening(env_basic):
    try:
        init.launch()
        lumos("cp test/opening/* data")
        yield
    except Exception as e:
        print(f"Fixture failed with error: {e}")
        pass
    finally:
        print("Cleaning up in init_ready")
        pass


@pytest.fixture
def chat_ready(init_ready, mocker):
    mocker.patch("runtime_chat.owl")
    mocker.patch("runtime_chat.send_db")
    yield
    runtime_chat.clean()
    # mocker.resetall()


@pytest.fixture()
def init_create_fixture():
    intraday_data_json = os.path.join("data", "fox_data.json")
    nightly_data_json = os.path.join("data", "fox_nightly.json")
    chat_config_json = os.path.join("data", "chat_config.json")
    try:
        if os.path.exists(intraday_data_json):
            lumos("mv " + intraday_data_json + " " + intraday_data_json + ".bac")
        if os.path.exists(nightly_data_json):
            lumos("mv " + nightly_data_json + " " + nightly_data_json + ".bac")
        if os.path.exists(chat_config_json):
            lumos("mv " + chat_config_json + " " + chat_config_json + ".bac")
        yield
    except Exception as e:
        print(f"Fixture failed with error: {e}")
    finally:
        print("Cleaning up in finally block")
        if os.path.exists(intraday_data_json + ".bac"):
            lumos("mv " + intraday_data_json + ".bac " + intraday_data_json)
        if os.path.exists(nightly_data_json + ".bac"):
            lumos("mv " + nightly_data_json + ".bac " + nightly_data_json)
        if os.path.exists(chat_config_json + ".bac"):
            lumos("mv " + chat_config_json + ".bac " + chat_config_json)



# import run

# from unittest import mock

# def test_unittest_mock():
#     mock_get_sum = mock.patch('run.get_sum', return_value=20)
#     mock_get_sum.start()
#     result = run.get_sum()
#     mock_get_sum.stop()
#     print(result)

# def test_pytest_mock(mocker):
#     mocker.patch("run.get_sum", return_value=20)
#     # run.get_sum("a")
#     result = run.get_sum("a")
#     print(result)
#     run.get_sum.assert_called_once()
#     # run.assert_called_once_with('file')