import os
import sys
import requests
import time
import json
import pendulum
import pickle
import pandas as pd

from loguru import logger

logger.add("logs/sina.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {"Referer": "http://vip.stock.finance.sina.com.cn/"}


def launch():
    """
    now_str is local
    now_online is the online time
    """
    json_path = os.path.join("data", "sina_option_data.json")
    pickle_path = os.path.join("data", "sina_option_data.pickle")

    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()

    # now_online, chg_300 = fetch_stock("sh000300")
    now_online = fetch_time()
    date_online = now_online.split()[0]
    logger.debug("Online => " + now_online)
    # chg_50 = fetch_future("nf_IH0")
    # chg_300 = fetch_future("nf_IF0")
    # chg_500 = fetch_future("nf_IF0")
    # https://hq.sinajs.cn/list=nf_IC0,nf_IF0
    chg_50, inc_50 = fetch_stock("sh000016")
    chg_300, inc_300 = fetch_stock("sh000300")
    chg_500, inc_500 = fetch_stock("sh000905")
    chg_t0, inc_t0 = fetch_future("nf_T0")

    vol_up_50 = fetch_op_sum("op_up_50")
    vol_down_50 = fetch_op_sum("op_down_50")
    vol_up_300 = fetch_op_sum("op_up_300")
    vol_down_300 = fetch_op_sum("op_down_300")
    vol_up_500 = fetch_op_sum("op_up_500")
    vol_down_500 = fetch_op_sum("op_down_500")

    if vol_up_300 == 0:
        return

    if pendulum.today("Asia/Shanghai") == pendulum.parse(
        now_online, tz="Asia/Shanghai"
    ).at(0, 0, 0):
        with open(json_path, "r", encoding="utf-8") as file:
            option_dict = json.load(file)
    else:
        record_path = os.path.join("data", "sina_" + date_online + ".json")
        if not os.path.exists(record_path):
            # update_nightly(date_online)
            backup_intraday(date_online)
        elif now.hour == 9 and now.minute == 30:
            logger.debug("Market is not opened today. Sleep 6 hours.")
            time.sleep(60 * 60 * 6)
        logger.debug("after backup_intraday return")
        return

    option_dict["now"] = now_str
    # if option_dict['now_list'] != [] and option_dict['now_list'][-1] == now_online:
    #     logger.warning("Same now_online")
    #     return
    option_dict["now_list"].append(now_online)

    option_dict["chg_50"].append(round(chg_50, 4))
    pcr_50 = vol_down_50 / vol_up_50 * 100
    mid_50 = vol_down_50 / vol_up_50 * 100 - 86
    berry_50 = (chg_50 * 10) + mid_50
    option_dict["pcr_50"].append(round(pcr_50, 4))
    option_dict["berry_50"].append(round(berry_50, 4))

    option_dict["chg_300"].append(round(chg_300, 4))
    pcr_300 = vol_down_300 / vol_up_300 * 100
    mid_300 = vol_down_300 / vol_up_300 * 100 - 92
    berry_300 = (chg_300 * 10) + mid_300
    option_dict["pcr_300"].append(round(pcr_300, 4))
    option_dict["berry_300"].append(round(berry_300, 4))

    vol_300 = vol_down_300 + vol_up_300
    option_dict["vol_300"].append(round(vol_300))

    option_dict["chg_500"].append(round(chg_500, 4))
    pcr_500 = vol_down_500 / vol_up_500 * 100
    mid_500 = vol_down_500 / vol_up_500 * 100 - 114
    berry_500 = (chg_500 * 10) + mid_500
    option_dict["pcr_500"].append(round(pcr_500, 4))
    option_dict["berry_500"].append(round(berry_500, 4))

    option_dict["inc_t0"].append(round(inc_t0, 4))
    burger = (berry_50 + berry_500 + berry_300) / 3 - inc_t0 * 30
    # burger = (berry_50 + berry_500 + berry_300) / 3
    option_dict["burger"].append(round(burger, 4))

    if now < pendulum.today("Asia/Shanghai").add(hours=9, minutes=45, seconds=0):
        option_dict["std_300"].append(0)
    elif len(option_dict["now_list"]) <= 2:
        option_dict["std_300"].append(0)
    else:
        std_300 = pd.Series(option_dict["berry_300"][-240:]).std()
        option_dict["std_300"].append(round(std_300, 4))

    if now < pendulum.today("Asia/Shanghai").add(hours=9, minutes=40, seconds=0):
        scale = len(option_dict["now_list"])
        option_dict["berry_50"][-1] = round(
            option_dict["berry_50"][-1] * scale / 120, 4
        )
        option_dict["berry_300"][-1] = round(
            option_dict["berry_300"][-1] * scale / 120, 4
        )
        option_dict["berry_500"][-1] = round(
            option_dict["berry_500"][-1] * scale / 120, 4
        )
        option_dict["burger"][-1] = round(option_dict["burger"][-1] * scale / 120, 4)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(option_dict, file, ensure_ascii=False)

    # df = pd.DataFrame(option_dict,index=option_dict["now_list"])
    # df = df.drop("now_list",axis=1)
    # logger.debug(df)
    # with open(pickle_path, 'wb') as f:
    #     pickle.dump(df, f)


def fetch_op_sum(op_name):
    # get sum of vol from one op_name
    with open("data/sina_op_config.json", "r", encoding="utf-8") as file:
        sina_option_dict = json.load(file)
    # sina_option_dict = json.loads(db.get("data/sina_op_config.json"))
    hq_str_op_list = sina_option_dict[op_name]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(hq_str_op_list)
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    # hq_str_con_op_list = re.findall('="[\w,. -:购沽月]*',res_str)
    hq_str_con_op_list = res_str.split(";\n")
    vol_sum = 0
    for oneline in hq_str_con_op_list:
        tmp_list = oneline.split(",")
        if "var hq_str_CON_OP_" not in tmp_list[0] or len(tmp_list) < 41:
            continue
        vol_sum += int(tmp_list[41])
    return vol_sum


def fetch_stock(code):
    detail_url = "http://hq.sinajs.cn/list=" + code
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    res_tmp_list = res_str.split('="')[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[0]
    res_open = float(res_list[1])
    res_yest = float(res_list[2])
    res_price = float(res_list[3])
    res_chg = (res_price - res_yest) / res_yest * 100
    res_inc = res_price - res_yest
    res_now = res_list[30] + " " + res_list[31]
    return res_chg, res_inc


def fetch_time():
    detail_url = "http://hq.sinajs.cn/list=" + "sh000300"
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    res_tmp_list = res_str.split('="')[-1]
    res_list = res_tmp_list.split(",")
    res_now = res_list[30] + " " + res_list[31]
    return res_now


def fetch_future(code):
    detail_url = "http://hq.sinajs.cn/list=" + code
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    res_tmp_list = res_str.split('="')[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[-1]
    res_open = float(res_list[0])
    res_yest = float(res_list[14])
    res_price = float(res_list[3])
    res_chg = (res_price - res_open) / res_open * 100
    res_inc = res_price - res_open
    res_now = res_list[36] + " " + res_list[37]
    return res_chg, res_inc


# var hq_str_sh510300="沪深300ETF,4.103,4.103,4.030,4.106,4.024,4.031,4.032,683648627,2776624903.000,136700,4.031,35200,4.030,306800,4.029,1011700,4.028,161900,4.027,461200,4.032,221400,4.033,103900,4.034,117800,4.035,111800,4.036,2023-04-21,15:00:01,00,";
# var hq_str_sh000300="沪深300,3827.1634,3837.7531,3801.3870,3827.1634,3781.4034,0,0,105929375,202331293564,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2023-05-31,14:40:11,00,";
# var hq_str_nf_IH0="2663.000,2666.000,2637.000,2644.400,19752,52338702.000,38880.000,0.000,0.000,2932.000,2399.200,0.000,0.000,2661.400,2665.600,42815.000,2644.400,3,0.000,0,0.000,0,0.000,0,0.000,0,2644.600,2,0.000,0,0.000,0,0.000,0,0.000,0,2023-04-24,11:25:59,0,1,,,,,,,,,2649.793,上证50指数期货连续";
# var hq_str_nf_T0="101.890,101.980,101.850,101.855,34713,3537949.870,203919.000,0.000,0.000,103.930,99.860,0.000,0.000,101.890,101.895,201585.000,101.855,74,0.000,0,0.000,0,0.000,0,0.000,0,101.860,167,0.000,0,0.000,0,0.000,0,0.000,0,2023-06-12,11:29:26,100,1,,,,,,,,,101.920,10年期国债期货连续";


def fixture(input_list):
    if input_list[-1] > 15:
        input_list[-1] = 15
    elif input_list[-1] < -15:
        input_list[-1] = -15
    else:
        pass


now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9, minutes=20)
mk_nu = dawn.add(hours=9, minutes=25)
mk_alpha = dawn.add(hours=9, minutes=29, seconds=58)
mk_beta = dawn.add(hours=11, minutes=30)
mk_gamma = dawn.add(hours=13, minutes=0)
mk_delta = dawn.add(hours=15, minutes=0, seconds=20)
mk_zeta = pendulum.tomorrow("Asia/Shanghai")


def hold_period():
    """
    mu nu  9:30  alpha beta  12  gamma  delta  15:00:20 zeta
    """
    while True:
        now = pendulum.now("Asia/Shanghai")

        if now < mk_alpha:
            logger.debug(["remain (s) ", (mk_alpha - now).total_seconds()])
            time.sleep((mk_alpha - now).total_seconds())
            lumos("python init.py")
        elif now <= mk_beta:
            return
        elif now < mk_gamma:
            logger.debug(["remain (s) ", (mk_gamma - now).total_seconds()])
            time.sleep((mk_gamma - now).total_seconds())
        elif now <= mk_delta:
            return
        else:
            logger.debug("Market Closed")
            logger.debug(["remain to end (s) ", (mk_zeta - now).total_seconds()])
            time.sleep((mk_zeta - now).total_seconds() + 3600)
            # sleep @ 1:00
            exit(0)


def update_nightly(date_online):
    nightly_path = os.path.join("data", "nightly_data.json")
    json_path = os.path.join("data", "sina_option_data.json")
    with open(nightly_path, "r", encoding="utf-8") as file:
        nightly_dict = json.load(file)
    with open(json_path, "r", encoding="utf-8") as file:
        option_dict = json.load(file)

    yest_shuffle = nightly_dict["shuffle"][-1]
    yest_berry = nightly_dict["berry_300"][-1]
    berry_300 = option_dict["berry_300"][-1]
    diff_berry = berry_300 - yest_berry
    if diff_berry > -2 and berry_300 > 0:
        today_shuffle = 1
    elif diff_berry < 2 and berry_300 < 0:
        today_shuffle = -1
    else:
        today_shuffle = 0
    nightly_dict["time"].append(date_online)
    nightly_dict["chg_300"].append(option_dict["chg_300"][-1])
    nightly_dict["pcr_300"].append(option_dict["pcr_300"][-1])
    nightly_dict["berry_300"].append(option_dict["berry_300"][-1])
    nightly_dict["shuffle"].append(today_shuffle)

    with open(nightly_path, "w", encoding="utf-8") as file:
        json.dump(nightly_dict, file, ensure_ascii=False)
    logger.debug("update nightly complete!")


def backup_intraday(date_online):
    source = os.path.join("data", "sina_option_data.json")
    target = os.path.join("data", "sina_" + date_online + ".json")
    mv_cmd = "mv " + source + " " + target
    if not os.path.exists(target):
        lumos(mv_cmd)
    else:
        logger.debug("backup_intraday twice!! ERR")
        raise
    # create new sina_option_data.json
    init_dict = {
        "chg_50": [],
        "pcr_50": [],
        "berry_50": [],
        "chg_300": [],
        "pcr_300": [],
        "berry_300": [],
        "chg_500": [],
        "pcr_500": [],
        "berry_500": [],
        "inc_t0": [],
        "burger": [],
        "vol_300": [],
        "std_300": [],
        "now_list": [],
    }
    with open(source, "w", encoding="utf-8") as file:
        json.dump(init_dict, file, ensure_ascii=False)


if __name__ == "__main__":
    while True:
        logger.debug("Lanuch")
        launch()
        if sys.argv[-1] == "test":
            pass
        else:
            hold_period()
        now = pendulum.now("Asia/Shanghai")
        time.sleep(5 - now.second % 5)
        logger.debug("END")
