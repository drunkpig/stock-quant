import logging
from logging.config import fileConfig
from functools import reduce
import numpy as np

logger = logging.getLogger()


class HiDeviationFinder(object):
    def __init__(self, cache_len, valid_hi_price_interval, price_eq_endurance, rsi_eq_endurance,
                 effective_deviation_distance, hi_price_2_point_distance):
        self.__cache_len = cache_len  # 保存多少个周期的数据
        self.__hi_price = []
        self.__rsi = []
        self.__dt = []
        self.__effective_deviation_distance = effective_deviation_distance
        self.__valid_hi_price_interval = valid_hi_price_interval  # 有效最高价格必须要高于左侧和右侧多少个点
        self.__price_equal_endurance = price_eq_endurance  # 判断高低点的误差
        self.__rsi_equal_endurance = rsi_eq_endurance
        self.__hi_price_2_point_distance = hi_price_2_point_distance

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
        if val_l == 0 or val_r == 0:
            min_val = 0.1
        else:
            min_val = min(val_l, val_r)
        delta = abs(val_l - val_r) / min_val
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
    def __max_valid_val(val_arr, step, r_index, valid_price_interval, pre_point_i=10000):
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
            max_after_val, mx_after_val_i = HiDeviationFinder.__arr_max(  # 向后检查
                val_arr[mx_i:min(mx_i + valid_price_interval, len(val_arr))])
            if mx >= max_after_val:
                #logger.info("@@")
                return mx, mx_i, False
            else:
                #logger.info("!!")
                return 0, 0, False  # 为了避免判断麻烦就返回0代替None，这样肯定不会顶背离

        #logger.info("++")

        mx, mx_i = HiDeviationFinder.__arr_max(val_arr[l_index:r_index])  # 找到一步之内的最大值
        mx_i = l_index + mx_i

        # 如果最大值向后去看和右侧最大值统治的区间重合则排除这个点继续向前搜索
        if mx_i+valid_price_interval >= pre_point_i-valid_price_interval:
            return HiDeviationFinder.__max_valid_val(val_arr, step, max(0, r_index-valid_price_interval),
                                                     valid_price_interval, pre_point_i)

        # 从最大值向前推进
        # r_index = l_index
        l_index = mx_i - valid_price_interval
        l_index_abs = max(0, l_index)
        mx_pre_val, mx_pre_val_i = HiDeviationFinder.__arr_max(val_arr[l_index_abs:mx_i])  # 向前检查是否是有效的最大值
        mx_pre_val_i = l_index_abs + mx_pre_val_i

        # 向后看看是不是最大的
        after_i = min(mx_i + valid_price_interval + 1, len(val_arr))
        max_after_val, mx_after_val_i = HiDeviationFinder.__arr_max(val_arr[mx_i + 1:after_i])
        mx_after_val_i = mx_i + 1 + mx_after_val_i

        if mx >= max_after_val and mx >= mx_pre_val:  # 比前后都大
            return mx, mx_i, l_index > 0
        elif mx < max_after_val and mx >= mx_pre_val:  # 比后面小，但是比前面大,继续向前找大的
            return HiDeviationFinder.__max_valid_val(val_arr, step, max(0, mx_i - valid_price_interval),
                                                     valid_price_interval, pre_point_i)
        else:
            # mx>=max_after_val and mx<mx_pre_val: #比前面小，比后面大
            return HiDeviationFinder.__max_valid_val(val_arr, step, mx_pre_val_i + 1,
                                                     valid_price_interval, pre_point_i)

    def is_hi_deviation(self, debug_flag=False):
        """
        判断是否是背离产生了
        :param debug_flag:
        :return:
        """
        step = self.__valid_hi_price_interval - 1
        len_arr = len(self.__hi_price)

        max_r, max_r_i, has_next = self.__max_valid_val(self.__hi_price, step, len_arr,
                                                        self.__valid_hi_price_interval)
        if not has_next:  # 没办法比较，认为没有背离
            #logger.info("&&&&")
            return False
        max_l_i = max(0, max_r_i - step)
        while has_next:  # 没有发现背离而且可以和下一个比较
            logger.debug("左侧点(%s, %s | %s, %s)" % (
                self.__dt[max_l_i], max_l_i, self.__hi_price[max_l_i], self.__rsi[max_l_i]))
            next_r_i = max(0, max_l_i - self.__valid_hi_price_interval)
            max_l, max_l_i, has_next = self.__max_valid_val(self.__hi_price, step, next_r_i,
                                                            self.__valid_hi_price_interval, max_r_i)

            logger.debug("右侧点(%s, %s | %s, %s)" % (
                self.__dt[max_r_i], max_r_i, self.__hi_price[max_r_i], self.__rsi[max_r_i]))
            logger.debug("左侧点(%s, %s | %s, %s)" % (
                self.__dt[max_l_i], max_l_i, self.__hi_price[max_l_i], self.__rsi[max_l_i]))
            if self.__is_price_equal_or_hi(max_l, max_r):

                if self.__is_rsi_hi_deviation(self.__rsi[max_l_i], self.__rsi[max_r_i]):
                    distance_now = len_arr - max_r_i  # 距离当前距离多少
                    top_point_distance = abs(max_r_i - max_l_i)  # 2个顶点之间的距离
                    if top_point_distance >= self.__hi_price_2_point_distance:
                        if distance_now <= self.__effective_deviation_distance:
                            logger.info("顶背离%s发生(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                                len_arr - max_r_i, self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i,
                                self.__dt[max_r_i], max_r,
                                self.__rsi[max_r_i], max_r_i))
                            logger.debug(
                                "0*实际距离当前周期%s, 设定有效距离%s" % (len_arr - max_r_i, self.__effective_deviation_distance))
                            return True
                        else:
                            logger.info(
                                "1*实际距离当前周期%s, 设定有效距离%s" % (len_arr - max_r_i, self.__effective_deviation_distance))
                            logger.info("不满足周期间隔(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                                self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                                self.__rsi[max_r_i], max_r_i))

                            return False
                    else:
                        logger.info("两顶点之间距离%s<%s太短(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                            top_point_distance, self.__hi_price_2_point_distance,
                            self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                            self.__rsi[max_r_i], max_r_i))

                        max_r = max_l
                        max_r_i = max_l_i

                else:
                    logger.info("没有背离(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                        self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                        self.__rsi[max_r_i], max_r_i))
                    max_r = max_l
                    max_r_i = max_l_i
            else:
                logger.info("价格不满足(%s, %s, %s, %s), (%s, %s, %s, %s)" % (
                    self.__dt[max_l_i], max_l, self.__rsi[max_l_i], max_l_i, self.__dt[max_r_i], max_r,
                    self.__rsi[max_r_i], max_r_i))
                max_r = max_l
                max_r_i = max_l_i

        #logger.info("****")
        return False
