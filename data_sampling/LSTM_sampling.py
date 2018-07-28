# coding=utf-8
from __future__ import print_function, absolute_import

from logging.config import fileConfig

import psycopg2
from gm.api import *
import os
from configparser import ConfigParser
import logging
import numpy as np

from utils.dt_tm import now_tm
from utils.hi_deviation_finder import HiDeviationFinder
from utils.rsi import rsi_init, compute_history_rsi
from utils.tsh_rsi import Tsh_RSI
from utils.__utils import is_stock_index_down_much, is_stock_down_much

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


def init_db():
    sql = """
    create table if not exists stock_sampling(
        id SERIAL  PRIMARY KEY ,
        symbol VARCHAR(64) NOT NULL,
        frequency VARCHAR(64) NOT NULL,
        begin_of_bar TIMESTAMP NOT NULL,
        end_of_bar TIMESTAMP NOT NULL,
        open_price  float8 NOT NULL,
        close_price  float8 NOT NULL,
        low_price  float8 NOT NULL,
        hi_price  float8 NOT NULL,
        volume float8 NOT NULL,
        amount float8 NOT NULL,
        is_peak SMALLINT NOT NULL,
        is_valley SMALLINT NOT NULL,
        y SMALLINT NOT NULL,
        gmt_created TIMESTAMP NOT NULL DEFAULT (NOW()) 
    );
    ALTER DATABASE lstm_sampling SET timezone TO 'Asia/Shanghai';
    """
    cursor = db.cursor()
    cursor.execute(sql)
    db.commit()
    cursor.close()
    logger.info("创建数据库OK")


def save_to_db(bar_info):
    sql = """
        INSERT INTO stock_sampling (symbol,frequency,begin_of_bar,end_of_bar, open_price,close_price,low_price,hi_price,volume,amount,is_peak,is_valley, y)
        VALUES(%(symbol)s, %(frequency)s, to_timestamp(%(begin_of_bar)s,'yyyy-MM-dd hh24:mi:ss'), to_timestamp(%(end_of_bar)s,'yyyy-MM-dd hh24:mi:ss'), %(open_price)s, 
        %(close_price)s, %(low_price)s, %(hi_price)s, %(volume)s, %(amount)s, %(is_peak)s, %(is_valley)s, %(y)s);
    """
    cursor = db.cursor()
    cursor.execute(sql, bar_info)
    db.commit()
    cursor.close()


def init(context):
    context.SYMBOLS = my_symbols
    #context.SHORT_RSI_PERIOD = short_rsi_peroid
    context.LONG_RSI_PERIOD = long_rsi_period
    #context.SHORT_FREQUENCY = short_time_bar
    context.LONG_FREQUENCY = long_time_bar
    context.WINDOW = data_window
    context.long_rsi_compute = None
    #context.short_rsi_compute = None
    #context.risk_rsi_compute = None  # 使用长周期作为风控

    subscribe(symbols=context.SYMBOLS, frequency=context.LONG_FREQUENCY, count=context.WINDOW)


def on_tick(context, tick):
    logger.error("不该运行到此处，调用的bar数据而非tick数据")
    exit(1)


def on_bar(context, bars):
    # 打印当前获取的bar信息

    bar_info = {
        'symbol': bars[0]['symbol'],
        'frequency': bars[0]['frequency'],
        'begin_of_bar': bars[0]['bob'].strftime('%Y-%m-%d %H:%M:%S'),
        'end_of_bar': bars[0]['eob'].strftime('%Y-%m-%d %H:%M:%S'),
        'open_price': bars[0]['open'],
        'close_price': bars[0]['close'],
        'low_price': bars[0]['low'],
        'hi_price': bars[0]['high'],
        'volume': bars[0]['volume'],
        'amount': bars[0]['amount'],
        'is_peak': 0,
        'is_valley': 0,
        'y':0
    }

    save_to_db(bar_info)

if __name__ == '__main__':
    print(__file__)
    init_db()
    now_dt = now_tm()
    fileConfig('../logging.ini')
    run(strategy_id='eceb04b5-8732-11e8-9ab6-68f72885d744',
        filename=this_file,
        mode=MODE_BACKTEST,
        token='5e18d749d600b7caa519c7caa4f09853aaa9deb2',
        backtest_start_time='2016-1-1 09:30:00',
        backtest_end_time=now_dt,
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=100000,
        backtest_commission_ratio=0.0002,
        backtest_slippage_ratio=0.0001,
        serv_addr='localhost:7001'
        )
