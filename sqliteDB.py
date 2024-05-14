import os
import sys
import sqlite3


def send_pcr(arrow, symbol = ""):
    if os.path.exists("db.sqlite3"):
        # connect
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
    else:
        return
    # insert
    cursor.execute('''INSERT INTO stock (dt, symbol,
                    chg_50, pcr_50, berry_50,
                    chg_300, pcr_300, berry_300,
                    chg_500, pcr_500, berry_500,
                    inc_t0, burger, vol_300, std_300)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ''',
                    (arrow.name, symbol,
                    arrow['chg_50'], arrow['pcr_50'], arrow['berry_50'],
                    arrow['chg_300'], arrow['pcr_300'], arrow['berry_300'],
                    arrow['chg_500'], arrow['pcr_500'], arrow['berry_500'],
                    arrow['inc_t0'], arrow['burger'], arrow['vol_300'], arrow['std_300']))
    conn.commit()
    conn.close()