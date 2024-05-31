import re
import json
import requests
import pandas as pd
from tqdm import tqdm

from models import akshare
from models import jsonDB

SINA = {"Referer": "http://vip.stock.finance.sina.com.cn/"}


def option_expiry() -> list:
    base_name = "300ETF"
    url = (
        "http://stock.finance.sina.com.cn/futures/api/openapi.php/StockOptionService.getStockName?exchange=null&cate="
        + base_name
    )
    res = requests.get(url, headers=SINA)
    res_dict = json.loads(res.text)
    month_list = list(set(res_dict["result"]["data"]["contractMonth"]))
    expiry_list = []
    for month in month_list:
        pretty_month = month[2:4] + month[5:7]
        expiry_list.append(pretty_month)
    expiry_list.sort()
    return expiry_list


def option_str_code(sina_name, expiry) -> list:
    url = "http://hq.sinajs.cn/list=" + sina_name + expiry
    res = requests.get(url, headers=SINA, timeout=5)
    res_str = res.text
    # hq_str_op_list = re.findall('="[A-Z_0-9,]*";',res_str)
    hq_str_op_list = re.findall(r"CON_OP_\d*", res_str)
    hq_str_code_list = [item.split("_")[-1] for item in hq_str_op_list]
    return hq_str_code_list


def option_expiry_left(code_list):
    # code_list = ['CON_OP_' + item for item in OPTIONS["510300C"]]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(code_list)
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    hq_str_con_op_list = res_str.split(";\n")
    date_list = []
    deadline_list = []
    for oneline in hq_str_con_op_list:
        sub_list = oneline.split(",")
        if "var hq_str_CON_OP_" not in sub_list[0] or len(sub_list) < 41:
            continue
        sub_date = sub_list[46]
        sub_days = int(sub_list[47])
        date_list.append(sub_date)
        deadline_list.append(sub_days)
    date_list = list(set(date_list))
    date_list.sort()
    deadline = min(deadline_list)
    return deadline, date_list


def option_see_daily(
    symbol: str = "510300",
    start_date: str = "19900101",
    end_date: str = "20500101",
) -> pd.DataFrame:
    share_df = akshare.stock_zh_index_daily_em(symbol="sh000300", start_date=start_date)
    opening = share_df["date"].tolist()  # market is opening.
    op_df = []
    print("DB Spider from see")
    for night in tqdm(opening):
        arrow_list = fetch_sse(night)
        if arrow_list == []:
            continue
        op_df.extend(arrow_list)
    df = pd.DataFrame(op_df)
    df = df[df["SECURITY_CODE"] == symbol]
    df = df.set_index("TRADE_DATE")
    df["cp"] = df["CP_RATE"].replace({",": ""}).astype(float)
    return df


def fetch_sse(date) -> list:
    date = date.replace("-", "")
    url = "http://query.sse.com.cn/commonQuery.do"
    data = {
        "jsonCallBack": "jsonpCallback48914897",
        "sqlId": "COMMON_SSE_ZQPZ_YSP_QQ_SJTJ_MRTJ_CX",
        "tradeDate": date,
    }
    params = {}
    headers = {"Referer": "http://www.sse.com.cn/"}
    r = requests.post(url, data=data, headers=headers)
    res_json = convert_jsonp_to_json(r.text)["result"]
    # {"CONTRACT_VOLUME": "128",
    # "CALL_VOLUME": "528,789",
    # "LEAVES_QTY": "1,592,910",
    # "CP_RATE": "95.94",
    # "PUT_VOLUME": "507,345",
    # "TRADE_DATE": "2024-05-09",
    # "TOTAL_MONEY": "35,466",
    # "TOTAL_VOLUME": "1,036,134",
    # "SECURITY_CODE": "510050",
    # "LEAVES_CALL_QTY": "766,855",
    # "LEAVES_PUT_QTY": "826,055",
    # "SECURITY_ABBR": "上证50ETF"},
    return res_json


def convert_jsonp_to_json(jsonp_data):
    # 提取有效数据部分
    json_data = jsonp_data.split("(", 1)[1].rsplit(")", 1)[0]
    # 转换为 JSON 对象
    return json.loads(json_data)


def option_vol_sum(code_list):
    codeplus_list = ["CON_OP_" + item for item in code_list]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(codeplus_list)
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    # hq_str_con_op_list = re.findall('="[\w,. -:购沽月]*',res_str)
    hq_str_con_op_list = res_str.split(";\n")
    vol_sum = 0
    # print(hq_str_con_op_list)
    for oneline in hq_str_con_op_list:
        op_detail = oneline.split(",")
        if op_detail == [""]:
            continue
        if "var hq_str_CON_OP_" not in op_detail[0] or len(op_detail) < 10:
            print(op_detail)
            continue
        # var hq_str_CON_SO_10007234="
        # '500ETF沽12月6500', '', '', '', '13', '-0.6462', '0.272', '-0.2126', '1.6678', '0.2753', '0.9775', '0.9504',
        # '510500P2412M06500', '6.5000', '0.9612', '1.0097', 'M
        # 0期权合约简称，，，,4成交量,5Delta,6Gamma,7Theta,8vega,9隐含波动率,10最高价,11最低价,
        # 12交易代码,13行权价,14最新价,15理论价值
        # vol_sum += abs(int(op_detail[4])*float(op_detail[5]))
        # vol_sum += int(op_detail[4])
        vol_sum += int(op_detail[41])
    return vol_sum


def option_vol_delta_sum(code_list):
    codeplus_list = ["CON_SO_" + item for item in code_list]
    detail_url = "http://hq.sinajs.cn/list=" + ",".join(codeplus_list)
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    # hq_str_con_op_list = re.findall('="[\w,. -:购沽月]*',res_str)
    hq_str_con_op_list = res_str.split(";\n")
    vol_sum = 0
    # print(hq_str_con_op_list)
    for oneline in hq_str_con_op_list:
        op_detail = oneline.split(",")
        if op_detail == [""]:
            continue
        if "var hq_str_CON_SO_" not in op_detail[0] or len(op_detail) < 10:
            print(op_detail)
            continue
        if "C" in op_detail[12]:
            sign = 1
        else:
            sign = -1
        vol_sum += int(op_detail[4]) * (sign * float(op_detail[5]))
        # var hq_str_CON_SO_10007234="
        # '500ETF沽12月6500', '', '', '', '13', '-0.6462', '0.272', '-0.2126', '1.6678', '0.2753', '0.9775', '0.9504',
        # '510500P2412M06500', '6.5000', '0.9612', '1.0097', 'M
        # 0期权合约简称，，，,4成交量,5Delta,6Gamma,7Theta,8vega,9隐含波动率,10最高价,11最低价,
        # 12交易代码,13行权价,14最新价,15理论价值
        # vol_sum += abs(int(op_detail[4])*float(op_detail[5]))
        # vol_sum += int(op_detail[4])
    return vol_sum


def fetch_time():
    detail_url = "http://hq.sinajs.cn/list=" + "sh000300"
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    res_tmp_list = res_str.split('="')[-1]
    res_list = res_tmp_list.split(",")
    res_now = res_list[30] + " " + res_list[31]
    return res_now


def stock_basic(code):
    detail_url = "http://hq.sinajs.cn/list=" + code
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    res_tmp_list = res_str.split('="')[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[0]
    res_open = float(res_list[1])
    res_yest = float(res_list[2])
    res_price = float(res_list[3])
    res_chg = (res_price - res_yest) / res_yest * 100
    res_inc = res_price - res_yest
    res_now = res_list[30] + " " + res_list[31]
    return res_chg, res_inc


def future_basic(code):
    detail_url = "http://hq.sinajs.cn/list=" + code
    res = requests.get(detail_url, headers=SINA, timeout=5)
    res_str = res.text
    res_tmp_list = res_str.split('="')[-1]
    res_list = res_tmp_list.split(",")
    res_name = res_list[-1]
    res_open = float(res_list[0])
    res_yest = float(res_list[14])
    res_price = float(res_list[3])
    res_chg = (res_price - res_open) / res_open * 100
    res_inc = res_price - res_open
    res_now = res_list[36] + " " + res_list[37]
    return res_chg, res_inc
