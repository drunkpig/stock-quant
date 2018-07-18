import random
import logging
from logging.config import fileConfig
from functools import reduce
import numpy as np

from utils.ths_rsi import THS_RSI

logger = logging.getLogger()


class HiDeviationFinder(object):
    def __init__(self, cache_len, valid_hi_price_interval, price_eq_endurance, rsi_eq_endurance, effective_deviation_distance):
        self.__cache_len = cache_len  # 保存多少个周期的数据
        self.__hi_price = []
        self.__rsi = []
        self.__dt = []
        self.__effective_deviation_distance = effective_deviation_distance
        self.__valid_hi_price_interval = valid_hi_price_interval  # 有效最高价格必须要高于左侧和右侧多少个点
        self.__price_equal_endurance = price_eq_endurance  # 判断高低点的误差
        self.__rsi_equal_endurance = rsi_eq_endurance

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
        del diff_gt0[0:time_period - 1]
        del diff_abs[0:time_period - 1]

        for i in range(0, len(diff_gt0)):
            sma_diff_gt0 = ((time_period - 1) * init_sma_diff_gt0 + 1 * diff_gt0[i]) / time_period
            sma_diff_abs = ((time_period - 1) * init_sma_diff_abs + 1 * diff_abs[i]) / time_period
            sma_rsi = (sma_diff_gt0 / sma_diff_abs) * 100
            history_rsi.append(sma_rsi)

        return history_rsi

    def add(self, hi_price, rsi, date_str):

        lmin = min(len(hi_price), len(rsi), len(date_str))
        del hi_price[0:len(hi_price) - lmin]
        del rsi[0:len(rsi) - lmin]
        del date_str[0:len(date_str) - lmin]

        l = min(len(hi_price), len(rsi))

        self.__hi_price += hi_price[-l:]
        self.__rsi += rsi[-l:]
        self.__dt += date_str
        len_delta = len(self.__hi_price) - self.__cache_len
        if len_delta > 0:
            del self.__hi_price[0:len_delta]
            del self.__rsi[0:len_delta]
            del self.__dt[0:len_delta]

    @staticmethod
    def __arr_max(arr):
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

    @staticmethod
    def __max_valid_val(val_arr, step, r_index, valid_price_interval):
        """

        :param val_arr:
        :param step:
        :param r_index:
        :param valid_price_interval:
        :return: （最大值，最大值下标，是否可以继续找下一个）
        """
        assert step < valid_price_interval

        l_index = r_index - step
        if l_index <= 0:  # 最后到头了也不用向前看了
            mx, mx_i = HiDeviationFinder.__arr_max(val_arr[0:r_index])
            return mx, mx_i, False

        mx, mx_i = HiDeviationFinder.__arr_max(val_arr[l_index:r_index])  # 找到一步之内的最大值
        mx_i = l_index + mx_i

        # 从最大值向前推进
        # r_index = l_index
        l_index = mx_i - valid_price_interval
        l_index_abs = max(0, l_index)
        mx_pre_val, mx_pre_val_i = HiDeviationFinder.__arr_max(val_arr[l_index_abs:mx_i])  # 向前检查是否是有效的最大值
        mx_pre_val_i = l_index_abs + mx_pre_val_i
        # 向前看的时候不用考虑相等的情况
        if mx >= mx_pre_val:
            return mx, mx_i, True
        else:
            return HiDeviationFinder.__max_valid_val(val_arr, step, mx_pre_val_i + 1, valid_price_interval)

    # @staticmethod
    # def __get_2_hi_price(val_arr, step, r_index, valid_price_interval):
    #     val_1, index_1, has_next_1 = HiDeviationFinder.__max_valid_val(val_arr, step, r_index, valid_price_interval)
    #     if has_next_1:
    #         val_2, index_2, has_next_2 = HiDeviationFinder.__max_valid_val(val_arr, step, index_1, valid_price_interval)
    #     else:
    #         val_2, index_2, has_next_2 = None, None, False
    #
    #     return val_1, index_1, has_next_1, val_2, index_2, has_next_2

    def is_hi_deviation(self, debug_flag=False):
        step = self.__valid_hi_price_interval-1
        len_arr = len(self.__hi_price)

        max_r, max_r_i, has_next = HiDeviationFinder.__max_valid_val(self.__hi_price, step, len_arr,
                                                                     self.__valid_hi_price_interval)

        if not has_next:  # 没办法比较，认为没有背离
            return False
        max_l_i = max(0, max_r_i - step)
        while has_next:  # 没有发现背离而且可以和下一个比较
            logger.debug("左侧点(%s, %s | %s, %s)" % (
                self.__dt[max_l_i], max_l_i, self.__hi_price[max_l_i], self.__rsi[max_l_i]))
            max_l, max_l_i, has_next = HiDeviationFinder.__max_valid_val(self.__hi_price, step, max_l_i,
                                                                         self.__valid_hi_price_interval)
            logger.debug("右侧点(%s, %s | %s, %s)" % (
                self.__dt[max_r_i], max_r_i, self.__hi_price[max_r_i], self.__rsi[max_r_i]))
            logger.debug("左侧点(%s, %s | %s, %s)" % (
                self.__dt[max_l_i], max_l_i, self.__hi_price[max_l_i], self.__rsi[max_l_i]))
            if self.__is_price_equal_or_hi(max_l, max_r):
                if self.__is_rsi_hi_deviation(self.__rsi[max_l_i], self.__rsi[max_r_i]):
                    if len_arr - max_r_i <= self.__effective_deviation_distance:
                        logger.info("顶背离发生(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                            self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                            self.__rsi[max_r_i], max_r_i))
                        logger.info("实际距离当前周期%s, 设定有效距离%s"%(len_arr - max_r_i, self.__effective_deviation_distance))
                        return True
                    else:
                        logger.debug("不满足周期间隔(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                            self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                            self.__rsi[max_r_i], max_r_i))
                        max_r = max_l
                        max_r_i = max_l_i
                else:
                    logger.debug("没有背离(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                        self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                        self.__rsi[max_r_i], max_r_i))
                    # max_r = max_l
                    # max_r_i = max_l_i
            else:
                logger.debug("价格不满足(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                    self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                    self.__rsi[max_r_i], max_r_i))
                max_r = max_l
                max_r_i = max_l_i

        return False

    def is_hi_deviation_2(self, interval, debug_flag=False):
        """
        扫描顶背离.
        最高价格，这个最高价格必须满足，左侧、右侧（如果有）4个里都是最大的。
        :param interval: 距离目前的点多少个以内发生的背离有效
        :return: 发生顶部背驰返回True，否则False
        """
        if debug_flag is True:
            print(self.__hi_price)
            print(self.__rsi)
            print(self.__dt)
            exit(0)
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
                        logger.debug("顶背离发生(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                            self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                            self.__rsi[max_r_i], max_r_i))
                        return True
                    else:
                        logger.debug("不满足周期间隔(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                            self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                            self.__rsi[max_r_i], max_r_i))
                        max_r = max_l
                        max_r_i = max_l_i
                else:
                    logger.debug("没有背离(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                        self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                        self.__rsi[max_r_i], max_r_i))
                    # max_r = max_l
                    # max_r_i = max_l_i
            else:
                logger.debug("价格不满足(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                    self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                    self.__rsi[max_r_i], max_r_i))
                max_r = max_l
                max_r_i = max_l_i

            if l_end <= 0:
                break

        return False


if __name__ == "__main__":
    fileConfig('../logging.ini')
    hi_price = [9.460000038146973, 9.4399995803833, 9.430000305175781, 9.470000267028809, 9.470000267028809,
                9.460000038146973, 9.449999809265137, 9.449999809265137, 9.460000038146973, 9.619999885559082,
                9.600000381469727, 9.600000381469727, 9.600000381469727, 9.579999923706055, 9.84000015258789,
                9.800000190734863, 9.819999694824219, 9.779999732971191, 9.770000457763672, 9.6899995803833,
                9.619999885559082, 9.649999618530273, 9.630000114440918, 9.619999885559082, 9.550000190734863,
                9.539999961853027, 9.460000038146973, 9.5, 9.529999732971191, 9.479999542236328, 9.399999618530273,
                9.270000457763672, 9.289999961853027, 9.220000267028809, 9.199999809265137, 9.300000190734863,
                9.289999961853027, 9.260000228881836, 9.3100004196167, 9.289999961853027, 9.289999961853027, 9.25, 9.25,
                9.270000457763672, 9.25, 9.329999923706055, 9.319999694824219, 9.260000228881836, 9.380000114440918,
                9.449999809265137, 9.520000457763672, 9.529999732971191, 9.600000381469727, 9.630000114440918,
                9.630000114440918, 9.600000381469727, 9.609999656677246, 9.65999984741211, 9.630000114440918,
                9.600000381469727, 9.59000015258789, 9.619999885559082, 9.640000343322754, 9.609999656677246,
                9.539999961853027, 9.75, 9.779999732971191, 9.720000267028809, 9.710000038146973, 9.699999809265137,
                9.640000343322754, 9.619999885559082, 9.609999656677246, 9.630000114440918, 9.680000305175781,
                9.649999618530273, 9.569999694824219, 9.569999694824219, 9.539999961853027, 9.6899995803833,
                9.680000305175781, 9.670000076293945, 9.619999885559082, 9.5600004196167, 9.579999923706055,
                9.539999961853027, 9.510000228881836, 9.5, 9.399999618530273, 9.399999618530273, 9.399999618530273,
                9.40999984741211, 9.430000305175781, 9.390000343322754, 9.380000114440918, 9.390000343322754,
                9.350000381469727, 9.329999923706055, 9.34000015258789, 9.289999961853027]
    rsi = [48.65, 48.65, 37.47, 57.16, 57.16, 48.38, 56.41, 56.41, 56.41, 84.13, 85.8, 68.52, 70.31, 65.82, 87.64,
           79.68, 81.06, 74.96, 55.08, 43.08, 41.53, 48.24, 44.18, 30.39, 33.17, 23.97, 19.19, 40.55, 37.88, 37.88,
           15.64, 28.98, 25.37, 25.37, 24.63, 45.52, 40.61, 40.61, 44.89, 49.28, 44.98, 37.2, 29.53, 49.51, 39.44,
           58.16, 42.43, 52.28, 64.71, 68.04, 72.68, 75.52, 80.41, 80.98, 73.3, 68.14, 73.7, 73.7, 58.89, 64.09, 61.0,
           65.04, 65.04, 38.93, 44.83, 72.23, 67.5, 69.87, 64.25, 53.85, 49.09, 46.61, 39.45, 46.08, 59.41, 38.73,
           38.73, 27.87, 25.42, 64.58, 56.15, 52.85, 41.19, 43.08, 40.0, 36.85, 36.85, 19.9, 19.9, 26.4, 23.03, 43.28,
           39.7, 26.53, 40.69, 35.26, 40.06, 34.0, 32.53, 19.4]
    dt = ['2018-06-06 14:15:00', '2018-06-06 14:30:00', '2018-06-06 14:45:00', '2018-06-06 15:00:00',
          '2018-06-07 09:45:00', '2018-06-07 10:00:00', '2018-06-07 10:15:00', '2018-06-07 10:30:00',
          '2018-06-07 10:45:00', '2018-06-07 11:00:00', '2018-06-07 11:15:00', '2018-06-07 11:30:00',
          '2018-06-07 13:15:00', '2018-06-07 13:30:00', '2018-06-07 13:45:00', '2018-06-07 14:00:00',
          '2018-06-07 14:15:00', '2018-06-07 14:30:00', '2018-06-07 14:45:00', '2018-06-07 15:00:00',
          '2018-06-08 09:45:00', '2018-06-08 10:00:00', '2018-06-08 10:15:00', '2018-06-08 10:30:00',
          '2018-06-08 10:45:00', '2018-06-08 11:00:00', '2018-06-08 11:15:00', '2018-06-08 11:30:00',
          '2018-06-08 13:15:00', '2018-06-08 13:30:00', '2018-06-08 13:45:00', '2018-06-08 14:00:00',
          '2018-06-08 14:15:00', '2018-06-08 14:30:00', '2018-06-08 14:45:00', '2018-06-08 15:00:00',
          '2018-06-11 09:45:00', '2018-06-11 10:00:00', '2018-06-11 10:15:00', '2018-06-11 10:30:00',
          '2018-06-11 10:45:00', '2018-06-11 11:00:00', '2018-06-11 11:15:00', '2018-06-11 11:30:00',
          '2018-06-11 13:15:00', '2018-06-11 13:30:00', '2018-06-11 13:45:00', '2018-06-11 14:00:00',
          '2018-06-11 14:15:00', '2018-06-11 14:30:00', '2018-06-11 14:45:00', '2018-06-11 15:00:00',
          '2018-06-12 09:45:00', '2018-06-12 10:00:00', '2018-06-12 10:15:00', '2018-06-12 10:30:00',
          '2018-06-12 10:45:00', '2018-06-12 11:00:00', '2018-06-12 11:15:00', '2018-06-12 11:30:00',
          '2018-06-12 13:15:00', '2018-06-12 13:30:00', '2018-06-12 13:45:00', '2018-06-12 14:00:00',
          '2018-06-12 14:15:00', '2018-06-12 14:30:00', '2018-06-12 14:45:00', '2018-06-12 15:00:00',
          '2018-06-13 09:45:00', '2018-06-13 10:00:00', '2018-06-13 10:15:00', '2018-06-13 10:30:00',
          '2018-06-13 10:45:00', '2018-06-13 11:00:00', '2018-06-13 11:15:00', '2018-06-13 11:30:00',
          '2018-06-13 13:15:00', '2018-06-13 13:30:00', '2018-06-13 13:45:00', '2018-06-13 14:00:00',
          '2018-06-13 14:15:00', '2018-06-13 14:30:00', '2018-06-13 14:45:00', '2018-06-13 15:00:00',
          '2018-06-14 09:45:00', '2018-06-14 10:00:00', '2018-06-14 10:15:00', '2018-06-14 10:30:00',
          '2018-06-14 10:45:00', '2018-06-14 11:00:00', '2018-06-14 11:15:00', '2018-06-14 11:30:00',
          '2018-06-14 13:15:00', '2018-06-14 13:30:00', '2018-06-14 13:45:00', '2018-06-14 14:00:00',
          '2018-06-14 14:15:00', '2018-06-14 14:30:00', '2018-06-14 14:45:00', '2018-06-14 15:00:00',
          '2018-06-15 09:45:00', '2018-06-15 10:00:00', '2018-06-15 10:15:00', '2018-06-15 10:30:00',
          '2018-06-15 10:45:00', '2018-06-15 11:00:00']

    # logger.debug(hi_price)
    # logger.debug(rsi)
    finder = HiDeviationFinder(100)
    finder.add(hi_price, rsi, dt)
    finder.is_hi_deviation(10)
