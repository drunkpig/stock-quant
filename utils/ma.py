"""
各种平均计算
"""


def ths_SMA(pre_val, cur_val, cur_val_weight, time_period):
    """
    同花顺加权移动平均  y = (y'*(T-weight)+val*weight)/T
    :param pre_val: 前一次的SMA值
    :param cur_val: 当前的值
    :param cur_val_weight:当前值的权重
    :param time_period: 周期
    :return:
    """
    final_val = (pre_val * (time_period - cur_val_weight) + cur_val * cur_val_weight) / time_period
    return final_val