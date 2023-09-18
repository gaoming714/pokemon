import os
import pendulum
import requests
from loguru import logger

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
    logger.debug("🧪 => " + cmd)
    res = os.system(cmd)
    return res