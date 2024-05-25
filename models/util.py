import os
import sys
import time
import json
import hashlib
import requests
import pendulum
from loguru import logger
from models import akshare as ak

def lumos(cmd):
    # res = 0
    logger.warning("➜  " + cmd)
    res = os.system(cmd)
    return res


now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=30)
mk_beta = dawn.add(hours=11,minutes=30,seconds=6)
mk_gamma = dawn.add(hours=13,minutes=0,seconds=1)
mk_delta = dawn.add(hours=15,minutes=0,seconds=6)
mk_epsilon = dawn.add(hours=20,minutes=0)
mk_zeta = pendulum.tomorrow("Asia/Shanghai") # actually tomorrow 1:00

def fetch_opening(market = "stockCN"):
    """
    market is opening or not
    payload : delay
            status
            dtime
    """
    payload = {}
    now = pendulum.now("Asia/Shanghai")
    # if now.day_of_week in [pendulum.FRIDAY, pendulum.SATURDAY, pendulum.SUNDAY]:
    #     # weekend
    #     payload["delay"] = (mk_zeta - now).total_seconds()
    #     payload["status"] = "weekend"
    #     payload["dtime"] = now
    #     return False, payload
    if now < mk_alpha:
        # dawn
        payload["delay"] = (mk_alpha - now).total_seconds()
        payload["status"] = "dawn"
        payload["dtime"] = now
    elif now < mk_beta:
        # morning
        payload["delay"] = 0
        payload["status"] = "morning"
        payload["dtime"] = now
    elif now < mk_gamma:
        # noon
        payload["delay"] = (mk_gamma - now).total_seconds()
        payload["status"] = "noon"
        payload["dtime"] = now
    elif now < mk_delta:
        # afternoon
        payload["delay"] = 0
        payload["status"] = "afternoon"
        payload["dtime"] = now
    elif now < mk_epsilon:
        # evening
        payload["delay"] = (mk_epsilon - now).total_seconds()
        payload["status"] = "evening"
        payload["dtime"] = now
    elif now < mk_zeta:
        # night
        payload["delay"] = (mk_zeta - now).total_seconds()
        payload["status"] = "night"
        payload["dtime"] = now
    else:
        # error
        logger.info("Clean mk_clock, exit(0)")
        exit(0)

    # logger.debug(payload)
    return payload["delay"] == 0, payload

def is_holiday():
    # only works @ 9:25 ~ 24:00
    date_online = ak.stock_zh_index_daily_em().iloc[-1]["date"]
    date_local = now.to_datetime_string()[:10]
    logger.debug([date_online, date_local])
    return  date_online != date_local

def skipbox(box_list, now_input, minutes = 15):
    if box_list != []:
        left_time = box_list[-1]
        right_time = left_time.add(minutes = minutes)
        if right_time > left_time.at(0,0,0).add(hours = 11,minutes = 30) and right_time < left_time.at(0,0,0).add(hours = 13):
            right_time = right_time.add(hours = 1, minutes = 30)
        if right_time > now_input:
            return True
    return False

def owl(msg):
    logger.info("Wol => " + msg)
    # email
    try:
        r = requests.get('http://127.0.0.1:8011/emit/' + msg, timeout=10)
    except:
        logger.warning("Email Fail " + msg)
    # wechat
    try:
        r = requests.get('http://127.0.0.1:8010/msg/' + msg, timeout=10)
    except:
        logger.warning("Wechat Fail " + msg)

def quote(path):
    path_str = str(path)
    return '"{}"'.format(path_str)

def make_hash(file_path):
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


def set_datetime(record):
    record["extra"]["datetime"] = pendulum.now("Asia/Shanghai")

def logConfig(log_file="logs/default.log", rotation="10 MB"):

    """
    配置 Loguru 日志记录
    :param log_level: 日志级别，如 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    :param log_file: 日志文件路径
    :param rotation: 日志文件轮换设置，如 "10 MB" 表示文件大小达到 10MB 时轮换
    使用方法

    # 在程序开始时配置日志
    from model.util import logConfig, logger
    logConfig(log_file="myapp.log", rotation="5 MB")
    # 使用 logger 记录日志
    logger.info("This is an info message")
    logger.debug("This is a debug message")
    """
    logger.remove()  # 移除默认的处理程序（如果有的话）
    style = "<green>{extra[datetime]}</green>" +\
            " [ <level>{level: <8}</level>] " +\
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>" +\
            "<green>♻ </green>" +\
            "<level>{message}</level>"
    # alternative ➲ ⛏ ☄ ➜ ♻
    logger.configure(patcher=set_datetime)
    logger.add(sys.stdout, colorize=True, format=style)
    logger.add(log_file, rotation=rotation, colorize=False, format=style)
    logger.add(log_file+".rich", rotation=rotation, colorize=True, format=style)
