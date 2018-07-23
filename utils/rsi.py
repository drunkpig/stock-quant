from functools import reduce


def rsi_init(close_price_arr, time_peroid):
    """
    通过迭代计算，平滑RSI的值
    :param close_price_arr:
    :param time_peroid:RSI周期
    :return:
    """
    diff = list(map(lambda x, y: x - y, close_price_arr[1:], close_price_arr[:-1]))
    diff_gt0 = list(map(lambda x: 0 if x < 0 else x, diff))
    diff_abs = list(map(lambda x: abs(x), diff))

    sma_diff_gt0 = reduce(lambda x, y: ((time_peroid - 1) * x + 1 * y) / time_peroid, diff_gt0)
    sma_diff_abs = reduce(lambda x, y: ((time_peroid - 1) * x + 1 * y) / time_peroid, diff_abs)
    sma_rsi = (sma_diff_gt0 / sma_diff_abs) * 100

    sma_diff_gt0 = round(sma_diff_gt0, 2)
    sma_diff_abs = round(sma_diff_abs, 2)
    sma_rsi = round(sma_rsi, 2)

    return sma_diff_gt0, sma_diff_abs, sma_rsi


def compute_history_rsi(close_price_arr, time_period):
    """

    :param close_price_arr:
    :param time_period:
    :return:
    """
    history_rsi = []
    diff = list(map(lambda x, y: x - y, close_price_arr[1:], close_price_arr[:-1]))
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
