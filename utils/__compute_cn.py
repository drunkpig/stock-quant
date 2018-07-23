import numpy as np
import talib as tl
from functools import reduce


# 同花顺和通达信等软件中的SMA
def SMA_CN(close, timeperiod):
    close = np.nan_to_num(close)
    return reduce(lambda x, y: ((timeperiod - 1) * x + y) / timeperiod, close)


# 同花顺和通达信等软件中的KDJ
def KDJ_CN(high, low, close, fastk_period, slowk_period, fastd_period):
    kValue, dValue = tl.STOCHF(high, low, close, fastk_period, fastd_period=1, fastd_matype=0)

    kValue = np.array(map(lambda x: SMA_CN(kValue[:x], slowk_period), range(1, len(kValue) + 1)))
    dValue = np.array(map(lambda x: SMA_CN(kValue[:x], fastd_period), range(1, len(kValue) + 1)))

    jValue = 3 * kValue - 2 * dValue

    func = lambda arr: np.array([0 if x < 0 else (100 if x > 100 else x) for x in arr])

    kValue = func(kValue)
    dValue = func(dValue)
    jValue = func(jValue)
    return kValue, dValue, jValue


# 同花顺和通达信等软件中的MACD
def MACD_CN(close, fastperiod, slowperiod, signalperiod):
    macdDIFF, macdDEA, macd = tl.MACDEXT(close, fastperiod=fastperiod, fastmatype=1, slowperiod=slowperiod,
                                         slowmatype=1, signalperiod=signalperiod, signalmatype=1)
    macd = macd * 2
    return macdDIFF, macdDEA, macd
