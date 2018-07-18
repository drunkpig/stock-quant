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

from logging.config import fileConfig

from gm.api import *
import os
from configparser import ConfigParser
import logging
import numpy as np

from utils.HiDeviationFinder import HiDeviationFinder
from utils.ths_rsi import THS_RSI

logger = logging.getLogger()
this_dir, this_file = os.path.split(__file__)

cfg = ConfigParser()
cfg.read('%s/ls_rsi.ini' % this_dir)
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


def init(context):
    context.SYMBOLS = my_symbols
    context.SHORT_RSI_PERIOD = short_rsi_peroid
    context.LONG_RSI_PERIOD = long_rsi_period
    context.SHORT_FREQUENCY = short_time_bar
    context.LONG_FREQUENCY = long_time_bar
    context.WINDOW = data_window
    context.long_rsi_compute = None
    context.short_rsi_compute = None
    context.risk_rsi_compute = None  # 使用长周期作为风控
    context.watch_buy = False
    context.debug_data = False

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
        heigest_price = np.array(
            context.data(context.SYMBOLS, frquency, context.WINDOW, fields='high').values.reshape(context.WINDOW))

        if context.long_rsi_compute == None:
            heigest_price_dt = np.array(
                context.data(context.SYMBOLS, frquency, context.WINDOW, fields='eob').values.reshape(context.WINDOW))
            heigest_price_dt = list(map(lambda x: str(x), heigest_price_dt))
            sma_diff_gt0, sma_diff_abs, rsi = THS_RSI.init_parames(close_price_arr.values.reshape(context.WINDOW),
                                                                   time_peroid=context.LONG_RSI_PERIOD)
            context.long_rsi_compute = THS_RSI(context.LONG_RSI_PERIOD, sma_diff_gt0, sma_diff_abs, rsi)

            history_rsi = HiDeviationFinder.compute_history_rsi(close_price_arr, context.LONG_RSI_PERIOD)
            hi_deviation_finder = HiDeviationFinder(RISK_PERIOD, VALID_HI_PRICE_INTERVAL, PRICE_EQ_ENDURANCE,
                                                    RSI_EQ_ENDURANCE,EFFECTIVE_DEVIATION_DISTANCE)
            hi_deviation_finder.add(heigest_price.tolist(), history_rsi, heigest_price_dt)
            context.hi_deviation_finder = hi_deviation_finder
        else:
            # date = '2018-06-15'
            # watch_date = str(bars[0]['eob']).split(' ')[0]
            # if date==watch_date:
            #     context.debug_data=True
            #
            # dt2 = '2018-06-07 10:15:00'
            # if str(bars[0]['eob'])==dt2:
            #     print(bars[0]['high'])
            #     exit(-1)
            close_price_2 = close_price_arr[-2:].values.reshape(2)
            heigest_price_1 = bars[0]['high']
            rsi = context.long_rsi_compute.ths_rsi(close_price_2)
            context.hi_deviation_finder.add([heigest_price_1], [rsi], [str(bars[0]['eob'])])
            if rsi < LONG_RSI_BUY_THRESHOLD:
                context.watch_buy = True
            else:
                context.watch_buy = False

    elif frquency == context.SHORT_FREQUENCY:
        close_price_arr = context.data(context.SYMBOLS, frquency, context.WINDOW, fields='close')
        if context.short_rsi_compute is None:
            sma_diff_gt0, sma_diff_abs, rsi = THS_RSI.init_parames(close_price_arr.values.reshape(context.WINDOW),
                                                                   time_peroid=context.SHORT_RSI_PERIOD)
            context.short_rsi_compute = THS_RSI(context.SHORT_RSI_PERIOD, sma_diff_gt0, sma_diff_abs, rsi)
        else:
            close_price_2 = close_price_arr[-2:].values.reshape(2)
            rsi = context.short_rsi_compute.ths_rsi(close_price_2)
            ma_price = round(np.mean(close_price_arr[-MA_PRICE_PERIOD:].values.reshape(MA_PRICE_PERIOD)), 2)
            close_price = round(close_price_2[1], 2)
            if rsi <= SHORT_RSI_BUY_THRESHOLD and context.watch_buy == True:  # 短期rsi小于阈值而且长周期发出买入信号
                if close_price < ma_price * (1 - PRICE_MA_THRESHOLD):
                    if not context.hi_deviation_finder.is_hi_deviation(context.debug_data):
                        print("%s买入\t%s\t%s\t%s" % (bars[0]['eob'], close_price, ma_price, rsi))
                    else:
                        print("%s顶背离拒绝买入\t%s\t%s\t%s" % (bars[0]['eob'], close_price, ma_price, rsi))
                elif not context.hi_deviation_finder.is_hi_deviation():
                    print("%s*买入\t%s\t%s\t%s" % (bars[0]['eob'], close_price, ma_price, rsi))

            elif rsi > SHORT_RSI_SELL_THRESHOLD:
                print("%s卖出\t%s\t%s\t%s" % (bars[0]['eob'], close_price, ma_price, rsi))


if __name__ == '__main__':
    print(__file__)
    fileConfig('../logging.ini')
    run(strategy_id='eceb04b5-8732-11e8-9ab6-68f72885d744',
        filename=this_file,
        mode=MODE_BACKTEST,
        token='5e18d749d600b7caa519c7caa4f09853aaa9deb2',
        backtest_start_time='2018-06-01 09:30:00',
        backtest_end_time='2018-07-14 15:00:00',
        backtest_adjust=ADJUST_NONE,
        backtest_initial_cash=100000,
        backtest_commission_ratio=0.0002,
        backtest_slippage_ratio=0.0001,
        serv_addr='localhost:7001'
        )
