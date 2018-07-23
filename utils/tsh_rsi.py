from utils.ma import ths_SMA


class Tsh_RSI(object):
    """
    同花顺RSI的实现
    """
    def __init__(self, time_peroid, sma_diff_gt0, sma_abs_diff, cur_rsi):
        self.__time_period = time_peroid
        self.__sma_gt0_diff = sma_diff_gt0
        self.__sma_abs_diff = sma_abs_diff
        self.__cur_rsi = cur_rsi

    def ths_rsi(self, close_price):
        """

        :param pre_rsi:
        :param close_price: 长度是2 nparray
        :param time_period:
        :return:
        """
        cur_diff = close_price[1] - close_price[0]
        cur_abs_diff = abs(cur_diff)
        self.__sma_gt0_diff = self.__SMA(self.__sma_gt0_diff, max(cur_diff, 0), 1)
        self.__sma_abs_diff = self.__SMA(self.__sma_abs_diff, cur_abs_diff, 1)

        self.__cur_rsi = round(((self.__sma_gt0_diff / self.__sma_abs_diff) * 100), 2)

        return self.__cur_rsi

    def __SMA(self, pre_val, cur_val, cur_val_weight):
        """
        reduce(lambda x, y: ((time_period - 1) * x + y) / time_period, val_arr)
        :param pre_val:
        :param val_arr:
        :param time_period:
        :return:
        """

        final_val = ths_SMA(pre_val, cur_val, cur_val_weight, self.__time_period)
        return final_val


if __name__ == "__main__":
    pass
