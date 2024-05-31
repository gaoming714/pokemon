import os
import json
from pathlib import Path


def create_init_data():
    intraday_data_json = Path() / "data" / "fox_data.json"
    nightly_data_json = Path() / "data" / "fox_nightly.json"
    intraday_claw_json = Path() / "data" / "claw_data.json"
    nightly_claw_json = Path() / "data" / "claw_nightly.json"
    chat_config_json = Path() / "data" / "chat_config.json"
    if not intraday_data_json.exists():
        init_intraday = {"data": []}
        with open(intraday_data_json, "w", encoding="utf-8") as file:
            json.dump(init_intraday, file, ensure_ascii=False)
        print("create fox_data.json")
    if not nightly_data_json.exists():
        init_nightly = {"data": [], "records": ["1970-01-01"]}
        with open(nightly_data_json, "w", encoding="utf-8") as file:
            json.dump(init_nightly, file, ensure_ascii=False)
        print("create nightly_data.json")
    if not intraday_claw_json.exists():
        init_intraday = {"data": []}
        with open(intraday_claw_json, "w", encoding="utf-8") as file:
            json.dump(init_intraday, file, ensure_ascii=False)
        print("create claw_data.json")
    if not nightly_claw_json.exists():
        init_nightly = {"data": [], "records": ["1970-01-01"]}
        with open(nightly_claw_json, "w", encoding="utf-8") as file:
            json.dump(init_nightly, file, ensure_ascii=False)
        print("create claw_nightly_data.json")
    if not chat_config_json.exists():
        init_chat = {
            "owner": {"smtp": "", "port": "", "login": "", "password": "", "from": ""},
            "handle": 1,
            "addr_list": [""],
            "user_list": [""],
            "chatroom_list": [""],
        }
        with open(chat_config_json, "w", encoding="utf-8") as file:
            json.dump(init_chat, file, ensure_ascii=False)
        print("create chat_config.json")


def option_codes(symbol):
    config_path = Path() / "data" / "fox_op_config.json"
    with open(config_path, "r", encoding="utf-8") as file:
        op_dict = json.load(file)
    # op_dict = json.loads(db.get("data/sina_op_config.json"))
    expiry_list = op_dict["expiry"]
    code_list = []
    for expiry in expiry_list:
        one_list = [item for item in op_dict[symbol + expiry]]
        code_list.extend(one_list)
    # code_list = [ item for expiry in expiry_list for item in op_dict[symbol+expiry]]
    # print(code_list)
    return code_list


def load_it(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def save_it(json_path, data):
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False)
