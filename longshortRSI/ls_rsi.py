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

if __name__ == '__main__':
    print(__file__)
    _, this_file = os.path.split(__file__)


    run(strategy_id='eceb04b5-8732-11e8-9ab6-68f72885d744',
        filename=this_file,
        mode=1,
        token='5e18d749d600b7caa519c7caa4f09853aaa9deb2',
        backtest_start_time='2017-06-17 13:00:00',
        backtest_end_time='2017-08-21 15:00:00')