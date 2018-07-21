from functools import reduce


def __max(arr):
    if len(arr) <= 0:
        return -1
    else:
        return max(arr)


def find_hi_point(arr, valid_step):
    """

    :param arr:
    :param valid_step: 左侧和右侧必须要有多少个低于的值
    :return:
    """
    max_val_index = []
    for i in range(0, len(arr)):
        val = arr[i]
        pre_start = max(0, i - valid_step)
        after_end = min(len(arr), i + 1 + valid_step)
        max_l = __max(arr[pre_start:i])
        max_r = __max(arr[i + 1:after_end])
        if val >= max_l and val >= max_r:
            max_val_index.append(i)
            i = after_end

    ret_index = []
    len_process = -1
    while len_process != len(ret_index):
        ret_index = []
        len_process = len(max_val_index)
        for i in range(1, len(max_val_index)):
            i_r = max_val_index[i]
            i_l = max_val_index[i - 1]
            if i_r - i_l - 1 < valid_step * 2:
                if arr[i_r] < arr[i_l]:
                    ret_index.append(i_l)
                elif arr[i_r] > arr[i_l]:
                    ret_index.append(i_r)
                else:
                    ret_index.append(i_r)  # 这里还应该根据最小点综合判断
            else:
                ret_index.append(i_l)
                if i ==len(max_val_index)-1:
                    ret_index.append(i_r)

        ret_index = reduce(lambda x, y: x if y in x else x + [y], ret_index, [])
        max_val_index = ret_index.copy()

    return ret_index
