import os
import sys

from loguru import logger
logger.add("log/util.log")

def lumos(cmd):
    # res = 0
    logger.debug("CMD ➜ " + cmd)
    res = os.system(cmd)
    return res


