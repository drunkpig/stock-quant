class HiDeviationFinder(object):
    def __init__(self, cache_len):
        self.cache_len = cache_len  # 保存多少个周期的数据
        self.hi_price = []
        self.rsi = []
        self.valid_hi_price_interval = 4
        self.price_equal_endurance = 0.01  # 判断高低点的误差
        self.rsi_equal_endurance = 0.005

    @staticmethod
    def compute_history_rsi(close_arr, time_period):
        #TODO
        pass

    def add(self, hi_price, rsi):
        l = min(len(hi_price), len(rsi))

        self.hi_price += hi_price[-l:]
        self.rsi += rsi[-l]
        if len(self.hi_price) > self.cache_len:
            del self.hi_price[0]
            del self.rsi[0]

    def __arr_max(self, arr):
        mx_el = 0
        mx_i = 0
        for i in arr:
            if arr[i] > mx_el:
                mx_el = arr[i]
                mx_i = i
        return mx_el, mx_i

    def __is_price_equal_or_hi(self, val_l, val_r):
        """
        val_r 等于或者大于val_l
        :param val_l:
        :param val_r:
        :return:
        """
        delta = abs(val_l - val_r) / min(val_l, val_r)
        if delta < self.price_equal_endurance:
            return True
        elif val_r > val_l:
            return True
        else:
            return False

    def __is_rsi_hi_deviation(self, val_l, val_r):
        delta = abs(val_l - val_r) / min(val_l, val_r)
        if delta < self.rsi_equal_endurance:
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
        valid_price_interval = self.valid_hi_price_interval
        len_arr = len(self.hi_price)

        n = 0
        step = valid_price_interval * 2 + 1

        r_start = -step
        r_end = len_arr - step * n - 1
        max_r, max_r_i = self.__arr_max(self.hi_price[r_start:r_end])
        max_r_i += (len_arr + r_start)

        l_start = -step * (n + 1)
        l_end = len_arr - step * (n + 1) - 1
        while abs(l_start) < len_arr:
            max_l, max_l_i = self.__arr_max(self.hi_price[l_start:l_end])
            max_l_i += (len_arr + l_start)
            n += 1
            l_start = -step * (n + 1)
            l_end = len_arr - step * (n + 1) - 1
            if self.__is_price_equal_or_hi(max_l, max_r):
                if self.__is_rsi_hi_deviation(self.rsi[max_l_i], self.rsi[max_r_i]):
                    if len_arr - max_r_i <= interval:
                        return True

        return False
