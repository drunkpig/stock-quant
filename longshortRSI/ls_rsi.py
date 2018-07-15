"""
算法使用长期RSI和短期RSI结合。
买点确认：
------------------------
首先观察长期RSI是否到达底部阈值，如果到达则立马转入
短期RSI进行观察，如果短期RSI到达阈值则检查
1，大盘当天是否下跌超过阈值
2，股票当天是否本次下跌超过阈值
3，如果1、2都成立则放弃
4，否则如果短期RSI达到买入阈值且低于短期均线阈值则进行金字塔买入

卖点确认：
-------------------------
短期 rsi值大于阈值
"""

# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import os
from configparser import ConfigParser
import logging
import talib

from utils.ths_rsi import THS_RSI

logger = logging.getLogger()
this_dir, this_file = os.path.split(__file__)

cfg = ConfigParser()
cfg.read('%s/ls_rsi.ini' % this_dir)
my_symbols = str(cfg.get('default', 'my_symbols'))
short_time_bar = str(cfg.get('default', 'short_time'))
long_time_bar = str(cfg.get('default', 'long_time'))
short_rsi = int(cfg.get('default', 'short_rsi'))
long_rsi = int(cfg.get("default", 'long_rsi'))
data_window = int(cfg.get("default", 'data_window'))


def init(context):
    context.SYMBOLS = my_symbols
    context.SHORT_RSI_PERIOD = short_rsi
    context.LONG_RSI_PERIOD = long_rsi
    context.SHORT_FREQUENCY = short_time_bar
    context.LONG_FREQUENCY = long_time_bar
    context.WINDOW = data_window
    context.long_rsi_compute = None
    context.short_rsi_compute = None

    subscribe(symbols=context.SYMBOLS, frequency=context.SHORT_FREQUENCY, count=context.WINDOW)
    subscribe(symbols=context.SYMBOLS, frequency=context.LONG_FREQUENCY, count=context.WINDOW)


def on_tick(context, tick):
    logger.error("不该运行到此处，调用的bar数据而非tick数据")
    exit(1)


def on_bar(context, bars):
    # 打印当前获取的bar信息
    frquency = bars[0]['frequency']
    if frquency == context.LONG_FREQUENCY:
        close_price_arr = context.data(context.SYMBOLS, frquency, context.WINDOW, fields='close')
        if context.long_rsi_compute == None:
            sma_diff_gt0, sma_diff_abs, rsi = THS_RSI.init_parames(close_price_arr.values.reshape(context.WINDOW),
                                                                   time_peroid=context.LONG_RSI_PERIOD)
            context.long_rsi_compute = THS_RSI(context.LONG_RSI_PERIOD, sma_diff_gt0, sma_diff_abs, rsi)
        else:
            close_price_2 = close_price_arr[-2:].values.reshape(2)
            rsi = context.long_rsi_compute.ths_rsi(close_price_2)

        print("%s\t%s" % (bars[0]['eob'], rsi))
        # if rsi <= 20:
        #     print("%s\t%s" % (bars[0]['eob'], rsi))

    elif frquency == context.SHORT_FREQUENCY:
        close_price_arr = context.data(context.SYMBOLS, frquency, context.WINDOW, fields='close')
        if context.short_rsi_compute == None:
            sma_diff_gt0, sma_diff_abs, rsi = THS_RSI.init_parames(close_price_arr.values.reshape(context.WINDOW),
                                                                   time_peroid=context.SHORT_RSI_PERIOD)
            context.short_rsi_compute = THS_RSI(context.SHORT_RSI_PERIOD, sma_diff_gt0, sma_diff_abs, rsi)


if __name__ == '__main__':
    print(__file__)
    run(strategy_id='eceb04b5-8732-11e8-9ab6-68f72885d744',
        filename=this_file,
        mode=MODE_BACKTEST,
        token='5e18d749d600b7caa519c7caa4f09853aaa9deb2',
        backtest_start_time='2018-07-01 09:30:00',
        backtest_end_time='2018-07-14 15:00:00',
        backtest_adjust=ADJUST_NONE,
        backtest_initial_cash=100000,
        backtest_commission_ratio=0.0002,
        backtest_slippage_ratio=0.0001,
        serv_addr='localhost:7001'
        )
