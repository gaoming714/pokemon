import os
import sys
import time
import json
import tomlkit
import pendulum
from pathlib import Path
from flask import Flask
from envelopes import Envelope, GMailSMTP


from loguru import logger

logger.add("logs/email.log")

OWNER = {}
ADDR = []

app = Flask(__name__)


@app.route("/emit/<msg>", methods=["GET", "POST"])
def emit_message(msg):
    global ADDR
    logger.info("emit => " + msg)
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


def boot():
    global OWNER
    global ADDR
    config_path = Path() / "data" / "chat_config.toml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = tomlkit.parse(f.read())
    try:
        # skip
        if not config.get("active", False) or config.get("active") == 0:
            logger.info("Inactive Boot")
            return
        logger.success("Active Boot")
        OWNER = config["owner"]
        for client in config["client"]:
            if client.get("skip"):
                continue
            if client.get("channel") == "email":
                ADDR.append(client["symbol"])
        logger.debug(OWNER)
        logger.debug(ADDR)
    except:
        logger.warning("chat_config.toml is not ready")
        raise


if __name__ == "__main__":
    boot()
    app.run(port=8011)
