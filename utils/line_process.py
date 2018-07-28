from functools import reduce

from utils.array import array_max, array_min
import random

LOW_RSI = 35
HI_RSI = 75


def __get_hi_point(arr, valid_step, rsi=None):
    max_val_index = []
    for i in range(0, len(arr)):
        val = arr[i]
        pre_start = max(0, i - valid_step)
        after_end = min(len(arr), i + 1 + valid_step)
        max_l, _ = array_max(arr[pre_start:i], default_val_if_empty=0)
        max_r, _ = array_max(arr[i + 1:after_end], default_val_if_empty=0)
        if val >= max_l and val >= max_r:
            max_val_index.append(i)
            i = after_end

    ret = list(filter(lambda x: True if rsi[x] > HI_RSI else False, max_val_index))

    return ret


def __get_low_point(arr, valid_step, rsi=None):
    min_val_index = []
    for i in range(0, len(arr)):
        val = arr[i]
        pre_start = max(0, i - valid_step)
        after_end = min(len(arr), i + 1 + valid_step)
        min_l, _ = array_min(arr[pre_start:i], default_val_if_empty=0)
        min_r, _ = array_min(arr[i + 1:after_end], default_val_if_empty=0)
        if val <= min_l and val <= min_r:  # 小于两侧的
            min_val_index.append(i)
            i = after_end

    ret = list(filter(lambda x: True if rsi[x] < LOW_RSI else False, min_val_index))
    return ret


def __left_idx(i, index_arr):
    for idx in reversed(range(0, len(index_arr))):
        if index_arr[idx] < i:
            return index_arr[idx]

    return None


def __right_idx(i, index_arr):
    for idx in range(0, len(index_arr)):
        if index_arr[idx] > i:
            return index_arr[idx]

    return None


def __mid_idx(i_l, i_r, index_arr):
    mid_idx = []
    for idx in range(0, len(index_arr)):
        if i_l < index_arr[idx] < i_r:
            mid_idx.append(index_arr[idx])

    return mid_idx


def __optz_hi_eq_point(i_l, i_r, low_point_index_array, arr):
    """
    返回最合适高点的index
    距离两侧和中间最低点最远的高点最有效
    :param i_l:
    :param i_r:
    :param val_l:
    :param val_r:
    :param low_point_index_array:
    :return:
    """
    l_i = __left_idx(i_l, low_point_index_array)
    r_i = __right_idx(i_r, low_point_index_array)
    mid_idx = __mid_idx(i_l, i_r, low_point_index_array)
    val_l = -1 if l_i is None else arr[l_i]
    val_r = -1 if r_i is None else arr[r_i]
    val_mid, mid_i = (-1, -1) if len(mid_idx) == 0 else reduce(
        lambda x, y: (x[0], x[1]) if x[1] < y[1] else (y[0], y[1]),
        zip(range(len(mid_idx)), mid_idx))
    # 默认最坏情况下三个的值是相等的
    if val_l < val_r and val_l < val_mid:  # 左侧最小，保留右侧高点
        return i_r
    elif val_r < val_l and val_r < val_mid:
        return i_l
    else:  # 中间最小的情况下还要比较这个最小的点距离左边还是右边最近
        if mid_i - i_l < i_r - mid_i:
            return i_r
        elif mid_i - i_l > i_r - mid_i:
            return i_l
        else:  # 这个地方几乎不会出现
            return random.choice([i_r, i_l])


def __optz_low_eq_point(i_l, i_r, hi_point_index_array, arr):
    """
    返回最合适的低点的index
    距离两侧和中间最高点最远的低点最有效
    :param i_l:
    :param i_r:
    :param val_l:
    :param val_r:
    :param hi_point_array:
    :return:
    """
    l_i = __left_idx(i_l, hi_point_index_array)
    r_i = __right_idx(i_r, hi_point_index_array)
    mid_idx = __mid_idx(i_l, i_r, hi_point_index_array)
    val_l = -1 if l_i is None else arr[l_i]
    val_r = -1 if r_i is None else arr[r_i]
    val_mid, mid_i = (-1, -1) if len(mid_idx) == 0 else reduce(
        lambda x, y: (x[0], x[1]) if x[1] > y[1] else (y[0], y[1]),
        zip(range(len(mid_idx)), mid_idx))
    # 默认最坏情况下三个的值是相等的
    if val_l > val_r and val_l > val_mid:  # 左侧最大，保留右侧低点
        return i_r
    elif val_r > val_l and val_r > val_mid:
        return i_l
    else:  # 中间最大的情况下还要比较这个最大的点距离左边还是右边最近
        if mid_i - i_l < i_r - mid_i:
            return i_r
        elif mid_i - i_l > i_r - mid_i:
            return i_l
        else:  # 这个地方几乎不会出现
            return random.choice([i_r, i_l])


def find_hi_point(hi_arr, low_arr, valid_step, rsi=None):
    """
    找到峰顶的点
    :param hi_arr:
    :param valid_step: 左侧和右侧必须要有多少个低于的值
    :return:
    """
    low_point_index = None
    max_val_index = __get_hi_point(hi_arr, valid_step, rsi)

    ret_index = []
    len_process = -1
    while len_process != len(ret_index):  # 迭代直到收敛
        ret_index = []
        len_process = len(max_val_index)
        for i in range(1, len(max_val_index)):
            i_r = max_val_index[i]
            i_l = max_val_index[i - 1]
            if i_r - i_l - 1 < valid_step * 2:
                if hi_arr[i_r] < hi_arr[i_l]:  # 右侧比左侧小，说明右侧是下跌趋势里的反弹/反转小高峰，保留左侧高峰，但也很可能错过反弹/反转
                    ret_index.append(i_l)
                elif hi_arr[i_r] > hi_arr[i_l]:  # 右侧更大说明右侧是新高，保留无误, 但是这样去掉左侧可能导致背离判断不准确了
                    ret_index.append(i_r)
                else:  # 值相等，虽然很少会发生，取距离最低点最远的高点
                    if low_point_index is None:
                        low_point_index = __get_low_point(low_arr, valid_step, rsi)
                    opt_i = __optz_hi_eq_point(i_l, i_r, low_point_index, hi_arr)
                    ret_index.append(opt_i)
            else:
                ret_index.append(i_l)
                if i == len(max_val_index) - 1:
                    ret_index.append(i_r)

        ret_index = reduce(lambda x, y: x if y in x else x + [y], ret_index, [])
        max_val_index = ret_index.copy()

    return max_val_index

def __get_rsi(rsi, inx):
    rsi_arr = []
    for i in inx:
        rsi_arr.append(rsi[i])

    return rsi_arr

def find_low_point(low_arr, hi_arr, valid_step, rsi=None):
    """
    找到峰谷的点
    :param low_arr:
    :param valid_step:
    :return:
    """
    hi_point_index = None
    min_val_index = __get_low_point(low_arr, valid_step, rsi)

    tt = __get_rsi(rsi, min_val_index)

    ret_index = []
    len_process = -1
    while len_process != len(ret_index):  # 迭代直到收敛
        ret_index = []
        len_process = len(min_val_index)
        for i in range(1, len(min_val_index)):
            i_r = min_val_index[i]
            i_l = min_val_index[i - 1]
            if i_r - i_l - 1 < valid_step * 2:  # 点间距不满足标准？
                if low_arr[i_l] > low_arr[i_r]:  # 右侧的比左侧的小，说明价格越来越低了
                    ret_index.append(i_r)
                elif low_arr[i_l] < low_arr[i_r]:
                    ret_index.append(i_l)
                else:  # 这里还应该根据最高点综合判断
                    if hi_point_index is None:
                        hi_point_index = __get_hi_point(hi_arr, valid_step, rsi)
                    opt_i = __optz_low_eq_point(i_l, i_r, hi_point_index, low_arr)
                    ret_index.append(opt_i)
            else:
                ret_index.append(i_l)
                if i == len(min_val_index) - 1:
                    ret_index.append(i_r)

        ret_index = reduce(lambda x, y: x if y in x else x + [y], ret_index, [])  # 去重
        tt = __get_rsi(rsi, ret_index)
        min_val_index = ret_index.copy()


    return min_val_index


if __name__ == "__main__":
    lst = [1, 2, 3, 0, 5]
    i, val = reduce(lambda x, y: (x[0], x[1]) if x[1] < y[1] else (y[0], y[1]), zip(range(len(lst)), lst))
    print("%s\t%s" % (i, val))
