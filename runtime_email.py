import os
import sys
import time
import json
import tomlkit
import pendulum
from pathlib import Path
from flask import Flask
# from envelopes import Envelope, GMailSMTP
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import base64


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
    qq = OWNER["login"]  # 替换为你的 QQ 邮箱
    email = OWNER["from"]  # 替换为你的 QQ 邮箱
    sender_password = OWNER["password"]  # 替换为你的 SMTP 授权码（非邮箱登录密码）
    auth_code = sender_password
    recipient = addr

    subject = msg
    body = msg
    msg = MIMEText(body, "plain", "utf-8")  # 正文，纯文本，UTF-8 编码
    msg["Subject"] = Header(subject, "utf-8")  # 主题
    msg["From"] = encode_from(qq, email)
    msg["To"] = Header(addr, "utf-8")     # 收件人
    
    
    # 登录并发送邮件
    try:
        # 连接 SMTP 服务器
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # 启用 TLS 加密
        server.login(email, auth_code)  # 使用授权码登录
        server.sendmail(email, recipient, msg.as_string())  # 发送邮件
        print("邮件发送成功！")
    except smtplib.SMTPAuthenticationError as e:
        print(f"认证失败，请检查邮箱或授权码: {e}")
    except Exception as e:
        print(f"发送失败: {e}")
    finally:
        server.quit()  # 关闭连接

def encode_from(display_name, email_address, charset="utf-8"):
    """
    使用 Base64 编码 From 字段。

    Args:
        display_name: 发件人显示名称。
        email_address: 发件人邮箱地址。
        charset: 字符集。

    Returns:
        编码后的 From 字段字符串。
    """
    encoded_display_name = base64.b64encode(display_name.encode(charset)).decode(charset)
    return f"=?{charset}?B?{encoded_display_name}?= <{email_address}>"

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
