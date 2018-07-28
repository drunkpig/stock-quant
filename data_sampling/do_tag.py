import logging

import os
from configparser import ConfigParser

import psycopg2

from utils.deviation_scaner import is_hi_deviation, is_low_deviation
from utils.line_process import find_hi_point, find_low_point
from utils.rsi import compute_history_rsi

logger = logging.getLogger()
this_dir, this_file = os.path.split(__file__)

cfg = ConfigParser()
cfg.read('%s/sampling.ini' % this_dir)
my_symbols = str(cfg.get('default', 'my_symbols'))
short_time_bar = str(cfg.get('default', 'short_time'))
long_time_bar = str(cfg.get('default', 'long_time'))
short_rsi_peroid = int(cfg.get('default', 'short_rsi_period'))
long_rsi_period = int(cfg.get("default", 'long_rsi_period'))
data_window = int(cfg.get("default", 'data_window'))

LONG_RSI_BUY_THRESHOLD = int(cfg.get("default", 'long_rsi_buy_threshold'))
SHORT_RSI_BUY_THRESHOLD = int(cfg.get("default", 'short_rsi_buy_threshold'))
SHORT_RSI_SELL_THRESHOLD = int(cfg.get("default", 'short_rsi_sell_threshold'))
MA_PRICE_PERIOD = int(cfg.get("default", 'ma_price_period'))
PRICE_MA_THRESHOLD = float(cfg.get("default", 'price_ma_threshold'))
RISK_PERIOD = int(cfg.get("default", 'risk_period'))

EFFECTIVE_DEVIATION_DISTANCE = int(cfg.get("default", 'effective_deviation_distance'))  # 一个背离管多远
VALID_HI_PRICE_INTERVAL = int(cfg.get("default", 'valid_hi_price_interval'))  # 左右两侧价格必须低于这个价格才算高点
PRICE_EQ_ENDURANCE = float(cfg.get("default", 'price_eq_endurance'))
RSI_EQ_ENDURANCE = float(cfg.get("default", 'rsi_eq_endurance'))
HI_PRICE_2_POINT_DISTANCE = int(cfg.get("default", 'hi_price_2_point_distance'))
STOCK_INDEX = {"SH": "SHSE.000001", "SZ": "SZSE.399001"}.get(my_symbols[0:2])

db = psycopg2.connect(database='lstm_sampling', user='postgres', password='',
                      host='dev.jscrapy.org', port='5432')


def get_stock_bar(stock_code):
    bars = []
    sql = """
        select open_price,close_price,low_price, hi_price, end_of_bar as ts, id from stock_sampling where symbol='%s' order by id asc 
    """ % stock_code
    cursor = db.cursor()
    cursor.execute(sql)
    row = cursor.fetchall()
    cursor.close()
    if row is not None:
        for r in row:
            bars.append({"open_price": r[0], "close_price": r[1], "low_price": r[2], "hi_price": r[3], "ts": r[4], "id":r[5]})

    return bars


def __scan_hi_deviation(hi_point, close_price, history_rsi, valid_2_point_distance, price_eq_endurance,
                        rsi_eq_endurance, date_arr):
    deviation_point = []
    for i in range(1, len(hi_point)):
        i_l, i_r = hi_point[i - 1], hi_point[i]
        price_l, price_r = close_price[i_l], close_price[i_r]
        rsi_l, rsi_r = history_rsi[i_l], history_rsi[i_r]

        is_hi_devited = is_hi_deviation(i_l, i_r, price_l, price_r, rsi_l, rsi_r, valid_2_point_distance,
                                        price_eq_endurance,
                                        rsi_eq_endurance)
        if is_hi_devited:
            print("顶背离点(%s,%s,%s)\t(%s,%s,%s)" % (
                date_arr[i_l], close_price[i_l], history_rsi[i_l], date_arr[i_r], close_price[i_r], history_rsi[i_r]))
            deviation_point.append(i_r)

    return deviation_point


def __scan_low_deviation(low_point, close_price, history_rsi, valid_2_point_distance, price_eq_endurance,
                         rsi_eq_endurance, date_arr):
    deviation_point = []
    for i in range(1, len(low_point)):
        i_l, i_r = low_point[i - 1], low_point[i]
        price_l, price_r = close_price[i_l], close_price[i_r]
        rsi_l, rsi_r = history_rsi[i_l], history_rsi[i_r]

        is_low_devited = is_low_deviation(i_l, i_r, price_l, price_r, rsi_l, rsi_r, valid_2_point_distance,
                                          price_eq_endurance,
                                          rsi_eq_endurance)
        if is_low_devited:
            print("底背离点(%s,%s,%s)\t(%s,%s,%s)" % (
                date_arr[i_l], close_price[i_l], history_rsi[i_l], date_arr[i_r], close_price[i_r], history_rsi[i_r]))
            deviation_point.append(i_r)

    return deviation_point


def __print_deviation_point(point, date_arr, history_rsi, close_price):
    for i in point:
        dt = date_arr[i]
        close_p = close_price[i]
        rsi = history_rsi[i]
        print("%s\t%s\t%s" % (dt, close_p, rsi))

def __update(id, field, value):
    sql = """
        update stock_sampling set %s=%s where id = %s
    """%(field, value, id)
    cursor = db.cursor()
    cursor.execute(sql)
    cursor.close()
    db.commit()


def scan(symbol):
    """
    总体思路也比较简单，一个15分钟的线从16年1月到18年也只有不足1万个点。
    在计算的时候就全部加载到内存来进行了。
    先扫描出来符合条件的峰谷点和峰顶点。
    然后对峰谷的点和峰顶的点分别进行顶背离和底背离计算。计算结果更新到数据库
    :return:
    """
    bars_info = get_stock_bar(symbol)
    close_price = list(map(lambda x: x['close_price'], bars_info))
    low_price = list(map(lambda x: x['low_price'], bars_info))
    hi_price = list(map(lambda x: x['hi_price'], bars_info))
    date_arr = list(map(lambda x: x['ts'], bars_info))
    ids = list(map(lambda x:x['id'], bars_info))

    history_rsi = [50] + compute_history_rsi(close_price, long_rsi_period)
    hi_point = find_hi_point(hi_price, low_price, VALID_HI_PRICE_INTERVAL, history_rsi)
    del hi_point[0]

    print("顶背离====================================================================================")
    hi_deviation_point = __scan_hi_deviation(hi_point, close_price, history_rsi, HI_PRICE_2_POINT_DISTANCE,
                                             PRICE_EQ_ENDURANCE,
                                             RSI_EQ_ENDURANCE, date_arr)

    low_point = find_low_point(low_price, hi_price, VALID_HI_PRICE_INTERVAL, history_rsi)
    del low_point[0]

    print("底背离====================================================================================")
    low_deviation_point = __scan_low_deviation(low_point, close_price, history_rsi, HI_PRICE_2_POINT_DISTANCE,
                                               PRICE_EQ_ENDURANCE,
                                               RSI_EQ_ENDURANCE, date_arr)


    #__print_deviation_point(hi_deviation_point, date_arr, history_rsi, close_price)

    #__print_deviation_point(low_deviation_point, date_arr, history_rsi, close_price)

    for i in hi_point:
        id = ids[i]
        __update(id, 'is_peak', 1)

    for i in hi_deviation_point:
        id = ids[i]
        __update(id, 'y', 1)

    for i in low_point:
        id = ids[i]
        __update(id, 'is_valley', 1)

    for i in low_deviation_point:
        id = ids[i]
        __update(id, 'y', -1)


if __name__ == "__main__":
    scan("SHSE.600125")
