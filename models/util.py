import os
import sys
import time
import hashlib

import pendulum

from loguru import logger
logger.add("log/util.log")

def lumos(cmd):
    # res = 0
    logger.debug("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res


now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=29,seconds=58)
mk_alpha = dawn.add(hours=11,minutes=32,seconds=10)
mk_beta = dawn.add(hours=11,minutes=30)
mk_gamma = dawn.add(hours=13,minutes=0)
mk_delta = dawn.add(hours=15,minutes=0,seconds=20)
mk_zeta = pendulum.tomorrow("Asia/Shanghai")


def hold_period(init = False):
    """
        mu nu  9:30  alpha beta  12  gamma  delta  15:00:20 zeta
    """
    now = pendulum.now("Asia/Shanghai")
    if now < mk_alpha:
        logger.debug(["remain (s) ",(mk_alpha - now).total_seconds()])
        time.sleep((mk_alpha - now).total_seconds())
        exit(0)
        if init == True:
            lumos("python init.py")
    elif now <= mk_beta:
        return
    elif now < mk_gamma:
        logger.debug(["remain (s) ",(mk_gamma - now).total_seconds()])
        time.sleep((mk_gamma - now).total_seconds())
    elif now <= mk_delta:
        return
    else:
        logger.debug("Market Closed")
        logger.debug(["remain to end (s) ",(mk_zeta - now).total_seconds()])
        time.sleep((mk_zeta - now).total_seconds() + 3600)
        # sleep @ 1:00
        exit(0)


def skipbox(box_list, now_str, minutes = 15):
    now = pendulum.parse(now_str,tz="Asia/Shanghai")
    if box_list != []:
        btime = pendulum.parse(box_list[-1],tz="Asia/Shanghai")
        dtime = btime.add(minutes = minutes)
        if dtime > btime.at(0,0,0).add(hours = 11,minutes = 30) and dtime < btime.at(0,0,0).add(hours = 13):
            dtime = dtime.add(hours = 1, minutes = 30)
        if dtime > now:
            return True
    return False


def make_hash(file_path) -> str, str, str:
    md5_hash = hashlib.md5()
    sha1_hash = hashlib.sha1()
    sha256_hash = hashlib.sha256()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            md5_hash.update(data)
            sha1_hash.update(data)
            sha256_hash.update(data)

    return md5_hash.hexdigest(), sha1_hash.hexdigest(), sha256_hash.hexdigest()
