import re
import os
import requests
import sqlite3
import time
import json
import pendulum
import pandas as pd
from pathlib import Path
from flask import Flask
from flask import request
from flask import Response
from flask import redirect, url_for
from flask import render_template
from flask import render_template_string
import flask_login

from loguru import logger
logger.add("log/atom.log")

# db = redis.Redis(host='localhost', port=6379, db=0)
SINA = {'Referer':'http://vip.stock.finance.sina.com.cn/'}
json_path = os.path.join("data", "fox_data.json")
nightly_path = os.path.join("data", "fox_nightly.json")

app = Flask(__name__)
app.secret_key = "super secret string"  # Change this!
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@app.route("/")
def index(name=None):
    return render_template('home.html', name=name)

@app.route("/op/<code>")
def oppage(code = "IF", name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    with open(json_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)
    if 'now' not in op_dict:
        mk_margin = pendulum.today("Asia/Shanghai").add(hours=9,minutes=30,seconds=15)
        remain = (mk_margin - now).total_seconds()
        return render_template('pedding.html',name=name, remain = str(remain))
    return render_template('op_'+code+'.html', name=name)

@app.route("/hist")
def histpage(name=None):
    now = pendulum.now("Asia/Shanghai")
    now_str = now.to_datetime_string()
    nightly_path = os.path.join("data","fox_nightly.json")
    with open(nightly_path, 'r', encoding='utf-8') as file:
        json_dict = json.load(file)
    night_list = json_dict["records"][-60:]
    night_list.sort(reverse=True)
    night_list.insert(0,"Today")
    return render_template('hist.html', name=name, night_list=night_list)

@app.errorhandler(404)
def show_404_page(e):
    return render_template('404.html'), 404

@app.route("/api/remain")
def api_remain(name=None):
    now = pendulum.now("Asia/Shanghai")
    dawn = pendulum.today("Asia/Shanghai")
    mk_mu = dawn.add(hours=9,minutes=20)
    mk_nu = dawn.add(hours=9,minutes=25)
    mk_alpha = dawn.add(hours=9,minutes=30)
    mk_beta = dawn.add(hours=11,minutes=30)
    mk_gamma = dawn.add(hours=13,minutes=0)
    mk_delta = dawn.add(hours=15,minutes=1)
    mk_zeta = pendulum.tomorrow("Asia/Shanghai")
    remain = 0

    """
        mu nu  9:30  alpha beta  12  gamma  delta  16 zeta
    """
    now = pendulum.now("Asia/Shanghai")

    if now < mk_alpha:
        # print(["remain (s) ",(mk_alpha - now).total_seconds()])
        remain = (mk_alpha - now).total_seconds()
    elif now < mk_beta:
        pass
    elif now < mk_gamma:
        # print(["remain (s) ",(mk_gamma - now).total_seconds()])
        remain = (mk_gamma - now).total_seconds()
    elif now < mk_delta:
        pass
    else:
        # print("Market Closed")
        # print(["remain to end (s) ",(mk_zeta - now).total_seconds()])
        remain = (mk_zeta - now).total_seconds()
        # print("update to tomorrow")
    return str(int(remain))


@app.route("/api/op")
def api_op(name=None):
    # get info from sina_option_data
    with open(json_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)

    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace = True)
        now = op_dict['now']
    else:
        return json.dumps({})

    arrow = op_df.iloc[-1]
    now_list = list(op_df.index)

    ma_300_se = op_df['berry_300'].rolling(120, min_periods = 1).mean().values
    vol_mean_se = op_df["vol_300"].rolling(13, min_periods = 1).mean().values
    vol_diff_se = (op_df["vol_300"] - vol_mean_se) / 1000
    # vol_diff_se.fillna(0, inplace=True)
    vol_diff = vol_diff_se.iloc[-1]

    margin = -1.5 * op_df["chg_300"][-481:-1].std()
    if len(now_list) >= 300:
        horizon = 9 * op_df["chg_300"][12:280].std()
    else:
        horizon = 0

    if len(now_list) > 300:
        if arrow["berry_300"] > ma_300_se[-1] + 1.0:
            xbox_shuffle = 1
        elif arrow["berry_300"] < ma_300_se[-1] - 1.0:
            xbox_shuffle = -1
        else:
            xbox_shuffle = 0
        if ma_300_se[-1] > pd.Series(ma_300_se[-47:]).mean() + 0.47:
            apple_shuffle = 1
        elif ma_300_se[-1] < pd.Series(ma_300_se[-47:]).mean() - 0.47:
            apple_shuffle = -1
        else:
            apple_shuffle = 0
    else:
        xbox_shuffle = 0
        apple_shuffle = 0

    readme =  "Watch the fork and progress"
    context = {
            'now': now,
            'now_list': now_list,

            'chg_50': round(arrow["chg_50"],4),
            'chg_300': round(arrow["chg_300"],4),
            'chg_500': round(arrow["chg_500"],4),

            'pcr_300': round(arrow["pcr_300"],2),
            'berry_300': round(arrow["berry_300"],2),
            'pcr_300_list': list(op_df["pcr_300"]),
            'berry_300_list': list(op_df["berry_300"]),
            'ma_300_list': list(ma_300_se),
            'chg_300_list': list(op_df["chg_300"]),
            'vol_diff': round(vol_diff, 2),
            'vol_list' : list(vol_diff_se),
            'margin': round(margin,4),
            'horizon': round(horizon,4),
            'std': round(arrow["std_300"],4),
            'std_list': list(op_df["std_300"]),

            'burger': round(arrow["burger"],2),
            'burger_list': list(op_df["burger"]),

            'xbox_shuffle': xbox_shuffle,
            'apple_shuffle': apple_shuffle,

            'readme': readme,
        }
    return json.dumps(context)


@app.route("/api/stock/<date>")
def api_stock(name = None, date = None):
    # get info from sina_option_data
    if date == "Today":
        now = pendulum.now("Asia/Shanghai")
        date = now.to_datetime_string()[:10]
    if os.path.exists("db.sqlite3"):
        # connect
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
    else:
        return json.dumps({})
    # select
    query = '''SELECT * FROM stock WHERE dt LIKE "{}%";'''.format(date)
    op_df = pd.read_sql_query(query, conn)
    # op_df = pd.read_sql_query("SELECT * FROM stock;", conn)
    # op_df = op_df[op_df["dt"].str.contains(date)]
    op_df.set_index("dt", inplace = True)
    if len(op_df.index) == 0:
         return json.dumps({})

    # op_df = pd.DataFrame(op_dict)
    # op_df.set_index("dt", inplace = True)

    symbol_list = []
    position_list = []
    color_list = []
    for row_index, row in op_df.iterrows():
        if row["symbol"] == "up":
            symbol_list.append("arrow-up")
            position_list.append(row["chg_300"])
            color_list.append("red")
        elif row["symbol"] == "down":
            symbol_list.append("arrow-down")
            position_list.append(row["chg_300"])
            color_list.append("green")
        elif row["symbol"] == "turn":
            symbol_list.append("star-square-dot")
            position_list.append(row["chg_300"])
            color_list.append("purple")
    readme =  ""
    context = {

            'dt': list(op_df.index),
            'symbol': symbol_list,
            'position': position_list,
            'color': color_list

        }
    return json.dumps(context)

@app.route("/api/hist/<date>")
def api_hist(name = None, date = None):
    # get info from sina_option_data
    if date == "Today":
        date = "fox_data"
    hist_path = os.path.join("data", date + ".json")
    if not os.path.exists(hist_path):
        return json.dumps({})
    with open(hist_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)

    if "now" in op_dict and op_dict["now"] != "":
        op_df = pd.DataFrame(op_dict["data"])
        op_df.set_index("dt", inplace = True)
        now = op_dict['now']
    else:
        return json.dumps({})

    arrow = op_df.iloc[-1]
    now_list = list(op_df.index)

    ma_300_se = op_df['berry_300'].rolling(120, min_periods = 1).mean().values
    vol_mean_se = op_df["vol_300"].rolling(13, min_periods = 1).mean().values
    vol_diff_se = (op_df["vol_300"] - vol_mean_se) / 1000
    # vol_diff_se.fillna(0, inplace=True)
    vol_diff = vol_diff_se.iloc[-1]

    margin = -1.5 * op_df["chg_300"][-481:-1].std()
    if len(now_list) >= 300:
        horizon = 9 * op_df["chg_300"][12:280].std()
    else:
        horizon = 0

    if len(now_list) > 300:
        if arrow["berry_300"] > ma_300_se[-1] + 1.0:
            xbox_shuffle = 1
        elif arrow["berry_300"] < ma_300_se[-1] - 1.0:
            xbox_shuffle = -1
        else:
            xbox_shuffle = 0
        if ma_300_se[-1] > pd.Series(ma_300_se[-47:]).mean() + 0.47:
            apple_shuffle = 1
        elif ma_300_se[-1] < pd.Series(ma_300_se[-47:]).mean() - 0.47:
            apple_shuffle = -1
        else:
            apple_shuffle = 0
    else:
        xbox_shuffle = 0
        apple_shuffle = 0


    readme =  "Watch the fork and progress"
    context = {
            'now': now,
            'now_list': now_list,

            'chg_50': round(arrow["chg_50"],4),
            'chg_300': round(arrow["chg_300"],4),
            'chg_500': round(arrow["chg_500"],4),

            'pcr_300': round(arrow["pcr_300"],2),
            'berry_300': round(arrow["berry_300"],2),
            'pcr_300_list': list(op_df["pcr_300"]),
            'berry_300_list': list(op_df["berry_300"]),
            'ma_300_list': list(ma_300_se),
            'chg_300_list': list(op_df["chg_300"]),
            'vol_diff': round(vol_diff, 2),
            'vol_list' : list(vol_diff_se),
            'margin': round(margin,4),
            'horizon': round(horizon,4),
            'std': round(arrow["std_300"],4),
            'std_list': list(op_df["std_300"]),

            'burger': round(arrow["burger"],2),
            'burger_list': list(op_df["burger"]),

            'xbox_shuffle': xbox_shuffle,
            'apple_shuffle': apple_shuffle,

            'readme': readme,
        }
    return json.dumps(context)

@app.route("/api/symbol/<date>")
def api_symbol(name = None, date = None):
    # get info from sina_option_data
    if date == "Today":
        date = "fox_data"
    json_path = os.path.join("data", "fox_symbol.json")
    if not os.path.exists(json_path):
        return json.dumps({})
    with open(json_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)


    op_df = pd.DataFrame(op_dict["data"])
    op_df.set_index("dt", inplace = True)

    symbol_list = []
    position_list = []
    color_list = []
    for row_index, row in op_df.iterrows():
        if row["symbol"] == "up":
            symbol_list.append("arrow-up")
            position_list.append(row["chg_300"])
            color_list.append("red")
        elif row["symbol"] == "down":
            symbol_list.append("arrow-down")
            position_list.append(row["chg_300"])
            color_list.append("green")
        elif row["symbol"] == "turn":
            symbol_list.append("diamond")
            position_list.append(row["chg_300"])
            color_list.append("orange")

    readme =  ""
    context = {

            'dt': list(op_df.index),
            'symbol': symbol_list,
            'position': position_list,
            'color': color_list

        }
    return json.dumps(context)

@app.route('/welogin',methods=['GET','POST'])
def test_wechat():
    qr_path = Path("QR.png")
    if not qr_path.exists():
        return render_template('404.html')
    with open(qr_path, 'rb') as f:
        image = f.read()
    return Response(image, mimetype='image/jpeg')

class User(flask_login.UserMixin):
    def __init__(self, email, password):
        self.id = email
        self.password = password

users = {"leafstorm@126.com": User("leafstorm@126.com", "secret")}

@login_manager.user_loader
def user_loader(id):
    return users.get(id)


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == "GET":
        return render_template('we_login.html', guest="guest")
    else:
        user = users.get(request.form["email"])

        if user is None or user.password != request.form["password"]:
            return redirect(url_for("login"))

        flask_login.login_user(user)
        return redirect(url_for("protected"))

@app.route("/protected")
@flask_login.login_required
def protected():
    return render_template_string(
        "Logged in as: {{ user.id }}",
        user=flask_login.current_user
    )

@app.route("/logout")
def logout():
    flask_login.logout_user()
    return "Logged out"



#upload
from flask import flash
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from werkzeug.utils import secure_filename

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'GET':
            return render_template('upload.html')
        # return '''
        #             <!doctype html>
        #             <title>Upload new File</title>
        #             <h1>Upload new File</h1>
        #             <form method=post enctype=multipart/form-data>
        #             <input type=file name=file>
        #             <input type=submit value=Upload>
        #             </form>
        #             '''

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            now = pendulum.now("Asia/Shanghai")
            filename = str(now.timestamp()) + "__" + secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return "<p>OK</p>"
            # return redirect(url_for('show_file', name=filename))

from flask import send_from_directory

@app.route('/show_file/<name>')
def show_file(name):
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


if __name__ == '__main__':
    app.run(debug=True,port=8009)
