

import re
import os
import sys
import requests
import time
import json
import pendulum
import pandas as pd
from rich.progress import track

# conver sina_data to fox_data
INPUT_DIR = "data"
OUTPUT_DIR = "dd"


input_names = sorted(
    [
        fname
        for fname in os.listdir(INPUT_DIR)
        if (fname.endswith(".json") or fname.endswith(".json"))
    ]
)
output_names = [name.rsplit(".",1)[0] + ".json" for name in input_names]

burger = list(zip(input_names, output_names))

def launch(fname):
    json_path = os.path.join("data", fname)
    with open(json_path, 'r', encoding='utf-8') as file:
        op_dict = json.load(file)

    if "now" not in op_dict:
        return

    op_df = pd.DataFrame(op_dict)

    op_df.drop_duplicates(subset=["now_list"], keep='first', inplace=True)
    # op_df.set_index("now_list", inplace = True)
    # op_df.rename_axis("dt", inplace = True)
    op_df.rename(columns={"now_list": "dt"}, inplace=True)
    op_df.drop('now', axis=1, inplace=True)
    op_df["chg_50"] = op_df["chg_50"].round(4)
    op_df["pcr_50"] = op_df["pcr_50"].round(4)
    op_df["berry_50"] = op_df["berry_50"].round(4)
    op_df["chg_300"] = op_df["chg_300"].round(4)
    op_df["pcr_300"] = op_df["pcr_300"].round(4)
    op_df["berry_300"] = op_df["berry_300"].round(4)
    op_df["chg_500"] = op_df["chg_500"].round(4)
    op_df["pcr_500"] = op_df["pcr_500"].round(4)
    op_df["berry_500"] = op_df["berry_500"].round(4)
    op_df["inc_t0"] = op_df["inc_t0"].round(4)
    op_df["burger"] = op_df["burger"].round(4)
    if "vol_300" not in op_dict:
        op_df.insert(loc=11, column='vol_300', value=0)
    if "std_300" not in op_dict:
        op_df.insert(loc=11, column='std_300', value=0)

    now = op_dict['now']

    op_dict = op_df.to_dict(orient="index")
    op_dict = op_df.to_dict(orient="records")

    out_dict = {"data":op_dict, "now":now}

    out_path = os.path.join(OUTPUT_DIR, fname)
    with open(out_path, 'w', encoding='utf-8') as file:
        json.dump(out_dict, file, ensure_ascii=False)


if __name__ == '__main__':
    for input_name, output_name in track(burger):
        launch(input_name)
