import os
import sys
import time
import json
import pendulum
from pathlib import Path
from flask import Flask
from envelopes import Envelope, GMailSMTP

from mars import jsonDB

from loguru import logger

logger.add("log/email.log")

OWNER = {}
ME = ""
ADDR = []

app = Flask(__name__)


def get_mixin():
    global OWNER
    global ADDR
    info_path = Path() / "data" / "chat_config.json"
    info_dict = jsonDB.load_it(info_path)
    try:
        OWNER = info_dict["owner"]
        ADDR = info_dict["addr_list"]
        handle = info_dict["handle"]
        if handle == 0:
            ADDR = []
    except:
        logger.warning("chat_config.json is not ready")
        raise


@app.route("/emit/<msg>", methods=["GET", "POST"])
def emit_message(msg):
    global ADDR
    logger.info("emit => " + msg)
    print(ADDR)
    for email_addr in ADDR:
        try:
            send(email_addr, msg)
        except:
            logger.warning("Email Fail " + email_addr)
    return {"emit": msg}


def send(addr, msg):
    global OWNER
    envelope = Envelope(
        from_addr=(OWNER["from"], "PokeScript"),
        to_addr=(addr, "Hi Jack"),
        subject="PokeScript",
        text_body=msg,
    )

    # Send the envelope using an ad-hoc connection...
    envelope.send(
        OWNER["smtp"],
        port=OWNER["port"],
        login=OWNER["login"],
        password=OWNER["password"],
        tls=True,
    )


if __name__ == "__main__":
    get_mixin()
    app.run(port=8011)
