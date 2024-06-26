import os
import sys
import requests
import time
import json
import pendulum
import pickle
import pandas as pd
from pathlib import Path

from mars import jsonDB
from mars import webDB
from mars import util

from mars.util import logConfig, logger

logConfig("logs/ranger_claw.log", rotation="10 MB")


def launch():
    """
    now_str is local
    now_online is the online time
    """
    json_path = Path() / "data" / "claw_data.json"

    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()

    # now_online, chg_300 = webDB.stock_basic("sh000300")
    now_online = webDB.fetch_time()
    date_online = now_online.split()[0]
    logger.debug("Online => " + now_online)
    chg_50, inc_50 = webDB.stock_basic("sh000016")
    chg_300, inc_300 = webDB.stock_basic("sh000300")
    chg_500, inc_500 = webDB.stock_basic("sh000905")
    chg_t0, inc_t0 = webDB.future_basic("nf_T0")

    vol_up_50 = fetch_op_sum("510050C")
    vol_down_50 = fetch_op_sum("510050P")
    vol_up_300 = fetch_op_sum("510300C")
    vol_down_300 = fetch_op_sum("510300P")
    vol_300 = vol_up_300 + vol_down_300
    vol_up_500 = fetch_op_sum("510500C")
    vol_down_500 = fetch_op_sum("510500P")
    vol_50 = vol_up_50 + vol_down_50
    vol_500 = vol_up_500 + vol_down_500

    if vol_up_300 == 0:
        return

    if pendulum.today("Asia/Shanghai") == pendulum.parse(
        date_online, tz="Asia/Shanghai"
    ):
        op_dict = jsonDB.load_it(json_path)
    else:
        mk_zeta = pendulum.tomorrow("Asia/Shanghai")
        delay = (mk_zeta - now).total_seconds()
        logger.warning("Holiday today. Sleep to 24:00. " + mk_zeta.diff_for_humans())
        time.sleep(delay)
        return

    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace=True)
    else:
        op_df = pd.DataFrame()

    if len(op_df.index) != 0 and op_df.index[-1] == now_online:
        logger.debug("Same now_online")
        return

    el = {}
    el["dt"] = now_online

    el["chg_50"] = round(chg_50, 4)
    pcr_50 = vol_down_50 / vol_up_50 * 100
    mid_50 = vol_down_50 / vol_up_50 * 100 - 86
    berry_50 = (chg_50 * 10) + mid_50
    el["pcr_50"] = round(pcr_50, 4)
    el["berry_50"] = round(berry_50, 4)

    el["chg_300"] = round(chg_300, 4)
    pcr_300 = vol_down_300 / vol_up_300 * 100
    mid_300 = vol_down_300 / vol_up_300 * 100 - 92
    berry_300 = (chg_300 * 10) + mid_300
    el["pcr_300"] = round(pcr_300, 4)
    el["berry_300"] = round(berry_300, 4)

    el["chg_500"] = round(chg_500, 4)
    pcr_500 = vol_down_500 / vol_up_500 * 100
    mid_500 = vol_down_500 / vol_up_500 * 100 - 104
    berry_500 = (chg_500 * 13) + mid_500
    el["pcr_500"] = round(pcr_500, 4)
    el["berry_500"] = round(berry_500, 4)

    el["inc_t0"] = round(inc_t0, 4)
    burger = (berry_500 + berry_300) / 2 - inc_t0 * 30
    el["burger"] = round(burger, 4)
    el["vol_300"] = round(vol_300, 4)

    if len(op_df.index) <= 2:
        el["std_300"] = 0
    else:
        std_300 = op_df["berry_300"][-240:].std()  # not new one
        el["std_300"] = round(std_300, 4)

    if now < pendulum.today("Asia/Shanghai").add(hours=9, minutes=40, seconds=0):
        scale = len(op_df.index)
        el["berry_50"] = round(el["berry_50"] * scale / 120, 4)
        el["berry_300"] = round(el["berry_300"] * scale / 120, 4)
        el["berry_500"] = round(el["berry_500"] * scale / 120, 4)
        el["burger"] = round(el["burger"] * scale / 120, 4)

    op_dict["data"].append(el)
    op_dict["now"] = now_str
    jsonDB.save_it(json_path, op_dict)


def fetch_op_sum(op_name):
    # get sum of vol from one op_name
    code_list = jsonDB.option_codes(op_name)
    op_vol_sum = webDB.option_vol_delta_sum(code_list)
    return op_vol_sum


def tape_archive():
    now_online = webDB.fetch_time()
    date_online = now_online.split()[0]
    source_path = Path() / "data" / "claw_data.json"
    archive_path = Path() / "data" / ("claw." + date_online + ".json")
    op_dict = jsonDB.load_it(source_path)
    if "now" in op_dict and not archive_path.exists():
        update_nightly(date_online)
        archive_intraday(date_online)


def update_nightly(date_online):
    nightly_path = Path() / "data" / "claw_nightly.json"
    json_path = Path() / "data" / "claw_data.json"
    nightly_dict = jsonDB.load_it(nightly_path)
    op_dict = jsonDB.load_it(json_path)

    el = {}
    el = op_dict["data"][-1]
    el["dt"] = date_online

    nightly_dict["data"].append(el)
    nightly_dict["records"].append(date_online)

    jsonDB.save_it(nightly_path, nightly_dict)
    logger.debug("update nightly complete!")


def archive_intraday(date_online):
    source = Path() / "data" / "claw_data.json"
    target = Path() / "data" / ("claw." + date_online + ".json")
    mv_cmd = "mv '{}' '{}'".format(source, target)
    if not target.exists():
        util.lumos(mv_cmd)
    else:
        logger.error("archive_intraday twice!! ERR")
        raise
    # create new fox_data.json
    init_dict = {"data": []}
    jsonDB.save_it(source, init_dict)


if __name__ == "__main__":
    while True:
        opening, info = util.fetch_opening()
        logger.debug(info["status"])
        if opening:
            launch()
            now = pendulum.now("Asia/Shanghai")
            delay = 65 - (now.second % 60) - (now.microsecond / 1e6)
            logger.debug("Wait {:.2f} (s)".format(delay))
            time.sleep(delay)
        else:
            if info["status"] == "dawn":
                delay = info["delay"] - 30
                logger.debug("Wait {:.2f} (s)".format(delay))
                time.sleep(delay)
                # run init @ 9:29:30
                # util.lumos("python init.py")
                now = pendulum.now("Asia/Shanghai")
                delay = 60 - (now.second % 60) - (now.microsecond / 1e6)
                time.sleep(delay)
            elif info["status"] == "night":
                delay = info["delay"]
                logger.debug("Wait {:.2f} (s)".format(delay))
                time.sleep(delay)
                tape_archive()
            else:
                delay = info["delay"]
                logger.debug("Wait {:.2f} (s)".format(delay))
                time.sleep(delay)
