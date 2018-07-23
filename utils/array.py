def array_max(arr, default_val_if_empty=None):
    """
    返回数组中最大的值和下标
    :param arr:
    :param default_val_if_empty: 如果数组是空的那么返回的默认值
    :return: (最大值，下标)
    """
    max_val = None
    max_i = None
    for i in range(0, len(arr)):
        if max_val is None:
            max_val = arr[i]
            max_i = i
        elif arr[i] > max_val:
            max_val = arr[i]
            max_i = i

    max_val = default_val_if_empty if max_val is None else max_val
    return max_val, max_i


def array_min(arr, default_val_if_empty=None):
    """
    返回数组中最小的值和下标
    :param arr:
    :param default_val_if_empty:
    :return:(最小值，最小值的下标)
    """
    min_val = None
    min_i = None
    for i in range(0, len(arr)):
        if min_val is None:
            min_val = arr[i]
            min_i = i
        elif arr[i] < min_val:
            min_val = arr[i]
            min_i = i

    min_val = default_val_if_empty if min_val is None else min_val
    return min_val, min_i
