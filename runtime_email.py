import os
import sys
import time
import json
import tomlkit
import pendulum
from pathlib import Path
from flask import Flask
from envelopes import Envelope, GMailSMTP
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


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


def send_bac(addr, msg):
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
def send(addr, msg):
    smtp_server = OWNER["smtp"]  # QQ 邮箱的 SMTP 服务器地址
    smtp_port = OWNER["port"]  # SSL 端口
    sender_email = OWNER["login"]  # 替换为你的 QQ 邮箱
    sender_password = OWNER["password"]  # 替换为你的 SMTP 授权码（非邮箱登录密码）

    # 配置收件人信息
    recipient_email = addr

    # 创建邮件内容
    subject = "Hi Jack"  # 邮件主题
    body = msg  # 邮件正文

    # 创建 MIME 邮件对象
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # 添加邮件正文
    msg.attach(MIMEText(body, "plain"))

    try:
        # 连接到 QQ 邮箱 SMTP 服务器
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            # server.set_debuglevel(1)  # 开启调试模式
            server.login(sender_email, sender_password)  # 登录邮箱
            server.sendmail(sender_email, recipient_email, msg.as_string())  # 发送邮件
            print("邮件发送成功！")
    except smtplib.SMTPException as e:
        pass
        # print(f"SMTP 错误：{e}")
    # except Exception as e:
    #     print(f"邮件发送失败：{e}")

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
