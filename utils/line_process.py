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
        if val >= max(arr[pre_start:i]) and val >= max(arr[i + 1:after_end]):
            max_val_index.append(i)
            i = after_end

    for i in range(1, len(max_val_index)):
        i_r = max_val_index[i]
        i_l = max_val_index[i - 1]
        if i_r - i_l - 1 < valid_step * 2:
            if arr[i_r] < arr[i_l]:
                del max_val_index[i]
            elif arr[i_r] > arr[i_l]:
                del max_val_index[i-1]
            else:
                del max_val_index[i-1]

    return max_val_index

