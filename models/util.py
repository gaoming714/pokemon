import os
import sys
import time
import hashlib
import pendulum
from loguru import logger

def lumos(cmd):
    # res = 0
    logger.debug("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res


now = pendulum.now("Asia/Shanghai")
dawn = pendulum.today("Asia/Shanghai")
mk_mu = dawn.add(hours=9,minutes=20)
mk_nu = dawn.add(hours=9,minutes=25)
mk_alpha = dawn.add(hours=9,minutes=30)
mk_beta = dawn.add(hours=11,minutes=30,seconds=5)
mk_gamma = dawn.add(hours=13,minutes=0)
mk_delta = dawn.add(hours=15,minutes=0,seconds=5)
mk_epsilon = dawn.add(hours=20,minutes=0)
mk_zeta = pendulum.tomorrow("Asia/Shanghai") # actually tomorrow 1:00

def fetch_opening(market = "stockCN") -> (bool, dict):
    """
    market is opening or not
    payload : delay
            status
    """
    payload = {}
    now = pendulum.now("Asia/Shanghai")
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
        payload["delay"] = (mk_zeta - now).total_seconds() + 3600
        payload["status"] = "night"
        payload["dtime"] = now
    else:
        # error
        logger.error([])
        payload["delay"] = 0
        payload["status"] = "error"
        payload["dtime"] = now

    # logger.debug(payload)
    return payload["delay"] == 0, payload



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


def make_hash(file_path) -> (str, str, str):
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
            "<green> ➲ </green>" +\
            "<level>{message}</level>"
    logger.configure(patcher=set_datetime)
    logger.add(sys.stdout, colorize=True, format=style)
    logger.add(log_file, rotation=rotation, colorize=False, format=style)
    logger.add(log_file+".rich", rotation=rotation, colorize=True, format=style)
