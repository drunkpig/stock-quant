

def array_max(arr, default_val_if_empty=None):
    """
    返回数组中最大的值和下标
    :param arr:
    :param default_val_if_empty: 如果数组是空的那么返回的默认值
    :return: (最大值，下标)
    """
    mx_val = default_val_if_empty
    mx_i = None
    for i in range(0, len(arr)):
        if mx_val is None:
            mx_val = arr[i]
            mx_i = i
        elif arr[i] > mx_val:
            mx_val = arr[i]
            mx_i = i

    return mx_val, mx_i


