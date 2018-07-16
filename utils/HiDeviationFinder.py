import random
import logging
from logging.config import fileConfig
from functools import reduce
import numpy as np

from utils.ths_rsi import THS_RSI

logger = logging.getLogger()


class HiDeviationFinder(object):
    def __init__(self, cache_len):
        self.__cache_len = cache_len  # 保存多少个周期的数据
        self.__hi_price = []
        self.__rsi = []
        self.__valid_hi_price_interval = 4
        self.__price_equal_endurance = 0.01  # 判断高低点的误差
        self.__rsi_equal_endurance = 0.005

    @staticmethod
    def compute_history_rsi(close_price, time_period):
        close_price = np.array(close_price).reshape(len(close_price))
        history_rsi = []
        diff = list(map(lambda x, y: x - y, close_price[1:], close_price[:-1]))
        diff_gt0 = list(map(lambda x: 0 if x < 0 else x, diff))
        diff_abs = list(map(lambda x: abs(x), diff))

        init_sma_diff_gt0 = reduce(lambda x, y: ((time_period - 1) * x + 1 * y) / time_period, diff_gt0[0:time_period],
                                   diff_gt0[0])
        init_sma_diff_abs = reduce(lambda x, y: ((time_period - 1) * x + 1 * y) / time_period, diff_abs[0:time_period],
                                   diff_abs[0])
        del diff_gt0[0:time_period-1]
        del diff_abs[0:time_period-1]

        for i in range(0, len(diff_gt0)):
            sma_diff_gt0 = ((time_period - 1) * init_sma_diff_gt0 + 1 * diff_gt0[i]) / time_period
            sma_diff_abs = ((time_period - 1) * init_sma_diff_abs + 1 * diff_abs[i]) / time_period
            sma_rsi = (sma_diff_gt0 / sma_diff_abs) * 100
            history_rsi.append(sma_rsi)

        return history_rsi

    def add(self, hi_price, rsi):
        l = min(len(hi_price), len(rsi))

        self.__hi_price += hi_price[-l:]
        self.__rsi += rsi[-l:]
        len_delta = l - self.__cache_len
        if len_delta > 0:
            del self.__hi_price[0:len_delta]
            del self.__rsi[0:len_delta]

    def __arr_max(self, arr):
        # logger.debug(arr)
        mx_el = 0
        mx_i = 0
        for i in range(0, len(arr)):
            if arr[i] > mx_el:
                mx_el = arr[i]
                mx_i = i

        # logger.debug("%s, %s"%(mx_el, mx_i))
        return mx_el, mx_i

    def __is_price_equal_or_hi(self, val_l, val_r):
        """
        val_r 等于或者大于val_l
        :param val_l:
        :param val_r:
        :return:
        """
        delta = abs(val_l - val_r) / min(val_l, val_r)
        if delta < self.__price_equal_endurance:
            return True
        elif val_r > val_l:
            return True
        else:
            return False

    def __is_rsi_hi_deviation(self, val_l, val_r):
        delta = abs(val_l - val_r) / min(val_l, val_r)
        if delta < self.__rsi_equal_endurance:
            return True
        elif val_r <= val_l:
            return True
        else:
            return False

    def is_hi_deviation(self, interval):
        """
        扫描顶背离.
        最高价格，这个最高价格必须满足，左侧、右侧（如果有）4个里都是最大的。
        :param interval: 距离目前的点多少个以内发生的背离有效
        :return: 发生顶部背驰返回True，否则False
        """
        valid_price_interval = self.__valid_hi_price_interval
        len_arr = len(self.__hi_price)

        n = 0
        step = valid_price_interval * 2 + 1

        r_start = len_arr - step
        r_end = len_arr - step * n
        max_r, max_r_i = self.__arr_max(self.__hi_price[r_start:r_end])
        max_r_i += r_start
        n += 1

        l_start = len_arr - step * (n + 1)
        l_end = len_arr - step * n
        while l_start >= 0:
            max_l, max_l_i = self.__arr_max(self.__hi_price[l_start:l_end])
            max_l_i += l_start
            n += 1
            l_end = l_start
            l_start = len_arr - step * (n + 1)
            if l_start < step:
                l_start = 0

            if self.__is_price_equal_or_hi(max_l, max_r):
                if self.__is_rsi_hi_deviation(self.__rsi[max_l_i], self.__rsi[max_r_i]):
                    if len_arr - max_r_i <= interval:
                        logger.debug("顶背离发生(%s,%s), (%s,%s) (%s,%s)" % (
                            max_l, self.__rsi[max_l_i], max_r, self.__rsi[max_r_i], max_l_i, max_r_i))
                        return True
                    else:
                        logger.debug("不满足周期间隔")
                        max_r = max_l
                        max_r_i = max_l_i
                else:
                    logger.debug("(%s,%s), (%s,%s)" % (max_l, self.__rsi[max_l_i], max_r, self.__rsi[max_r_i]))
                    max_r = max_l
                    max_r_i = max_l_i
            else:
                logger.debug("(%s,%s), (%s,%s)" % (max_l, self.__rsi[max_l_i], max_r, self.__rsi[max_r_i]))
                max_r = max_l
                max_r_i = max_l_i

            if l_end <= 0:
                break

        return False


if __name__ == "__main__":
    fileConfig('../logging.ini')
    hi_price = [random.randint(1, 99) for _ in range(1, 91)]
    rsi = [random.randint(1, 99) for _ in range(1, 90)]
    logger.debug(hi_price)
    logger.debug(rsi)
    finder = HiDeviationFinder(100)
    finder.add(hi_price, rsi)
    finder.is_hi_deviation(12)
