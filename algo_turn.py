import os
import sys
import time
import json
import pendulum
import pandas as pd
from pathlib import Path

from models import jsonDB
from models import sqliteDB
from models import util

from models.util import logConfig, logger

logConfig("logs/algo_turn.log", rotation="10 MB")

OWNER = {}
ADDR = []
BOX = []
ONCE = True


def launch():
    global BOX
    global ADDR
    global ONCE
    """
    now_str is local
    now_online is the online time
    """
    json_path = Path() / "data" / "fox_data.json"
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    op_dict = jsonDB.load_it(json_path)

    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace=True)
    else:
        mk_zeta = pendulum.tomorrow("Asia/Shanghai")
        delay = (mk_zeta - now).total_seconds()
        logger.warning("Holiday today. Sleep to 24:00. " + mk_zeta.diff_for_humans())
        time.sleep(delay)
        return

    start_tick = now.at(0, 0, 0).add(hours=9, minutes=40)
    if now < start_tick:
        delay = (start_tick - now).seconds
        time.sleep(delay)
        return
    if util.skipbox(BOX, now, minutes=2):
        return

    arrow = op_df.iloc[-1]
    vol_mean = op_df["vol_300"][-13:].mean()
    vol_diff = (arrow["vol_300"] - vol_mean) / 1000

    if vol_diff >= 10:
        BOX.append(now)
        msg = now_str + "\n 🧊 Turn " + "{:8.2f} K".format(round(vol_diff, 2))
        logger.info("online => " + now_str)
        util.owl(msg)
        sqliteDB.send_pcr(arrow, "turn")


def clean():
    # clean box for pytest
    global BOX
    BOX = []


if __name__ == "__main__":
    while True:
        opening, info = util.fetch_opening()
        logger.debug(info["status"])
        if opening:
            launch()
            now = pendulum.now("Asia/Shanghai")
            delay = 6 - (now.second % 5) - (now.microsecond / 1e6)
            logger.debug("Wait {:.2f} (s)".format(delay))
            time.sleep(delay)
        else:
            if info["status"] == "dawn":
                delay = info["delay"] + 60
                logger.debug("Wait {:.2f} (s)".format(delay))
                time.sleep(delay)
            else:
                delay = info["delay"]
                logger.debug("Wait {:.2f} (s)".format(delay))
                time.sleep(delay)
