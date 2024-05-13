import requests
import pandas as pd

from models import demjson


def stock_zh_index_daily_em(
        symbol: str = "csi931151",
        start_date: str = "19900101",
        end_date: str = "20500101",
) -> pd.DataFrame:
    """
    东方财富网-股票指数数据
    https://quote.eastmoney.com/center/hszs.html
    :param symbol: 带市场标识的指数代码; sz: 深交所, sh: 上交所, csi: 中信指数 + id(000905)
    :type symbol: str
    :param start_date: 开始时间
    :type start_date: str
    :param end_date: 结束时间
    :type end_date: str
    :return: 指数数据
    :rtype: pandas.DataFrame
    """
    market_map = {"sz": "0", "sh": "1", "csi": "2"}
    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    if symbol.find("sz") != -1:
        secid = "{}.{}".format(market_map["sz"], symbol.replace("sz", ""))
    elif symbol.find("sh") != -1:
        secid = "{}.{}".format(market_map["sh"], symbol.replace("sh", ""))
    elif symbol.find("csi") != -1:
        secid = "{}.{}".format(market_map["csi"], symbol.replace("csi", ""))
    else:
        return pd.DataFrame()
    params = {
        "cb": "jQuery1124033485574041163946_1596700547000",
        "secid": secid,
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "fields1": "f1,f2,f3,f4,f5",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "klt": "101",  # 日频率
        "fqt": "0",
        "beg": start_date,
        "end": end_date,
        "_": "1596700547039",
    }
    r = requests.get(url, params=params)
    data_text = r.text
    data_json = demjson.decode(data_text[data_text.find("{"): -2])
    temp_df = pd.DataFrame([item.split(",") for item in data_json["data"]["klines"]])
    # check temp_df data availability before further transformations which may raise errors
    if temp_df.empty:
        return pd.DataFrame()
    temp_df.columns = ["date", "open", "close", "high", "low", "volume", "amount", "_"]
    temp_df = temp_df[["date", "open", "close", "high", "low", "volume", "amount"]]
    temp_df["open"] = pd.to_numeric(temp_df["open"], errors="coerce")
    temp_df["close"] = pd.to_numeric(temp_df["close"], errors="coerce")
    temp_df["high"] = pd.to_numeric(temp_df["high"], errors="coerce")
    temp_df["low"] = pd.to_numeric(temp_df["low"], errors="coerce")
    temp_df["volume"] = pd.to_numeric(temp_df["volume"], errors="coerce")
    temp_df["amount"] = pd.to_numeric(temp_df["amount"], errors="coerce")
    return temp_df