import logging
from utils.line_process import find_hi_point

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

    def is_hi_deviation(self, debug_flag=False):
        len_dt = len(self.__hi_price)
        hi_points_index = find_hi_point(self.__hi_price, self.__valid_hi_price_interval)

        for i in reversed(range(0, len(hi_points_index))):
            i_l = hi_points_index[i - 1]
            i_r = hi_points_index[i]
            if i_l < 0:
                break

            price_l = self.__hi_price[i_l]
            price_r = self.__hi_price[i_r]
            rsi_l = self.__rsi[i_l]
            rsi_r = self.__rsi[i_r]

            is_price_ok = self.__is_price_equal_or_hi(price_l, price_r)
            is_rsi_ok = self.__is_rsi_hi_deviation(rsi_l, rsi_r)
            if is_price_ok and is_rsi_ok:
                if (len_dt - i_r) > self.__effective_deviation_distance:
                    logger.info("背离发生,但距离太远[%s>%s]>> (%s, %s, %s, %s), (%s,%s, %s, %s)" % (
                        len_dt - i_r, self.__effective_deviation_distance, self.__dt[i_l], price_l, rsi_l, i_l, self.__dt[i_r], price_r, rsi_r, i_r))
                    return False
                elif (i_r - i_l - 1) < self.__hi_price_2_point_distance:
                    logger.info("背离发生，但两点距离太近[%s<%s]>> (%s, %s, %s, %s), (%s,%s, %s, %s)" % (
                        i_r - i_l - 1, self.__hi_price_2_point_distance,self.__dt[i_l], price_l, rsi_l, i_l, self.__dt[i_r], price_r, rsi_r, i_r))
                    #return False
                else:
                    logger.info("背离发生>> (%s, %s, %s, %s), (%s,%s, %s, %s)" % (
                        self.__dt[i_l], price_l, rsi_l, i_l,
                        self.__dt[i_r], price_r, rsi_r, i_r))
                    return True
            elif not is_price_ok:
                logger.debug("价格不满足>> (%s, %s, %s, %s), (%s,%s, %s, %s)" % (
                    self.__dt[i_l], price_l, rsi_l, i_l, self.__dt[i_r], price_r, rsi_r, i_r))
                #return False
            elif not is_rsi_ok:
                logger.debug("RSI没有背离>> (%s, %s, %s, %s), (%s,%s, %s, %s)" % (
                    self.__dt[i_l], price_l, rsi_l, i_l, self.__dt[i_r], price_r, rsi_r, i_r))
                #return False

        return False

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

    def __watch(self, arr):
        for i in range(len(arr)):
            index = arr[i]
            logger.info("%s\t%s\t%s\t%s"%(self.__dt[index], self.__hi_price[index], self.__rsi[index],index))
