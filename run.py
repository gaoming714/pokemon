import sys
import os

import time
import pendulum
from pathlib import Path
import pandas as pd

from models import akshare
from models import pickleDB
from models import webDB

# CODE = ("510050","sh000016")
CODE = ("510300","sh000300")
# CODE = ("510500","sh000905")  # start 20221001
# REMOTE = False
REMOTE = True #download optinos
# START_DT = "20221001" # for 510500
START_DT = "20200101"


DT = []
BOX = None

def launch():
    pass

def optionMain():
    global BOX
    pkl_path = Path()/"data"/("op_" + CODE[0] + ".pkl")

    if REMOTE == False:
        # load local
        BOX = pickleDB.load_it(pkl_path)
    else:
        # download data
        df = webDB.option_see_daily(symbol=CODE[0], start_date=START_DT)
        BOX = pd.concat([BOX, df["cp"]], axis=1)
        # drop na ( maybe today  0 and -1 are None)
        if BOX.iloc[-1].isnull().any():
            BOX = BOX.dropna()
        #save
        pickleDB.save_it(pkl_path, BOX)


def stockMain():
    global DT
    global BOX
    df = akshare.stock_zh_index_daily_em(symbol=CODE[1], start_date=START_DT)
    DT = df["date"].tolist() # market is opening.
    df["chg"] = (df["close"] - df["close"].shift(1)) / df["close"].shift(1) * 100
    # day 0 chg 0
    # df.fillna(0, inplace=True)
    # remove day 0
    if df.iloc[0].isnull().any():
        df = df.drop(df.index[0])
    df = df.set_index("date")
    BOX = pd.DataFrame(df["chg"])

def magic():
    print(CODE)
    cp_mean = BOX["cp"].mean()
    cp_std = BOX["cp"].std()
    chg_std = BOX["chg"].std()
    BOX["option"] = (BOX["cp"] - cp_mean) / cp_std
    BOX["stock"]  = (BOX["chg"]) / chg_std
    BOX["mixin"]  = BOX["option"] + BOX["stock"]
    print(BOX.describe())
    print("Mean =", round(cp_mean, 3))
    print("Std  =", round(cp_std / chg_std, 3))
    print("Prod = ", round(BOX["mixin"].std(),3), "(need less than 1.2)")

    # ADF and SM
    from statsmodels.tsa.stattools import adfuller
    result = adfuller(BOX["mixin"])
    import statsmodels.api as sm
    model = sm.OLS(BOX["cp"], BOX["chg"])
    results = model.fit()
    print(results.summary())
    print('ADF statistic:%f'% result[0])
    print('p-value:%f'%result[1])

def show():
    import plotly.express as px

    fig = px.line(BOX,  y=["option", "stock", "mixin"])
    fig.show()


# Run the app
if __name__ == "__main__":
    stockMain()
    optionMain()
    magic()
    show()

