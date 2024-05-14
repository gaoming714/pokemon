import os
import json
import pendulum
import requests
from loguru import logger
from rich.console import Console

logger.add("logs/loguru_util.log")

SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}


def online():
    detail_url = "http://hq.sinajs.cn/list=" + "sh000300"
    res = requests.get(detail_url, headers=SINA)
    res_str = res.text
    res_tmp_list = res_str.split("=\"")[-1]
    res_list = res_tmp_list.split(",")
    res_now = res_list[30] + " " + res_list[31]
    now_online = pendulum.parse(res_now, tz="Asia/Shanghai")
    return now_online

### lumos
def lumos(cmd):
    # res = 0
    console = Console()
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    console.print(f"[blue][{now_str}][/blue] [bold green]{cmd}[/bold green]")
    res = os.system(cmd)
    return res

def color(vegetable = "", dessert = "", status = None):
    if status != None:
        console = status
    else:
        console = Console()
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    console.print(f"[blue][{now_str}][/blue] {vegetable} [bold green]{dessert}[/bold green]")
    return

def fetch_deadline():
    with open("data/sina_op_config.json", 'r', encoding='utf-8') as file:
        sina_option_dict = json.load(file)
    # sina_option_dict = json.loads(db.get("data/sina_op_config.json"))
    hq_str_op_list = sina_option_dict["op_up_300"]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(hq_str_op_list)
    res = requests.get(detail_url, headers=SINA)
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
    print(["Left", deadline, date_list])
    return deadline