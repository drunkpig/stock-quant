import logging

logger = logging.getLogger()


def __is_price_eq_or_hi(price_l, price_r, price_equal_endurance):
    if price_l == 0 or price_r == 0:
        min_val = 0.1
    else:
        min_val = min(price_l, price_r)
    delta = abs(price_l - price_r) / min_val
    if delta < price_equal_endurance:
        return True
    elif price_l < price_r:
        return True
    else:
        return False


def __is_price_eq_or_low(price_l, price_r, price_eq_endurance):
    if price_l == 0 or price_r == 0:
        min_val = 0.1
    else:
        min_val = min(price_l, price_r)
    delta = abs(price_l - price_r) / min_val
    if delta < price_eq_endurance:
        return True
    elif price_l > price_r:
        return True
    else:
        return False


def __is_rsi_hi_deviation(rsi_l, rsi_r, rsi_equal_endurance):
    delta = abs(rsi_l - rsi_r) / min(rsi_l, rsi_r)
    if delta < rsi_equal_endurance:
        return True
    elif rsi_r < rsi_l:
        return True
    else:
        return False


def __is_rsi_low_deviation(rsi_l, rsi_r, rsi_eq_endurance):
    if rsi_r==0: #防止除0异常
        return False
    elif rsi_l==0 and rsi_r>0:
        return True


    delta = abs(rsi_l - rsi_r) / min(rsi_l, rsi_r)
    if delta < rsi_eq_endurance:
        return True
    elif rsi_r > rsi_l:
        return True
    else:
        return False


def is_low_deviation(i_l, i_r, price_l, price_r, rsi_l, rsi_r, valid_2_point_distance, price_equal_endurance,
                     rsi_equal_endurance):
    is_price_ok = __is_price_eq_or_low(price_l, price_r, price_equal_endurance)
    is_rsi_ok = __is_rsi_low_deviation(rsi_l, rsi_r, rsi_equal_endurance)
    if is_price_ok and is_rsi_ok:
        if (i_r - i_l - 1) < valid_2_point_distance:
            logger.debug("底背离发生，但两点距离太近(实际距离：%s， 期望：%s)" % (i_r - i_l - 1, valid_2_point_distance))
            return False
        else:
            logger.debug("底背离发生")
            return True
    elif not is_price_ok:
        logger.debug("价格不满足")
        return False
    elif not is_rsi_ok:
        logger.debug("RSI没有底背离")
        return False

    return False


def is_hi_deviation(i_l, i_r, price_l, price_r, rsi_l, rsi_r, valid_2_point_distance, price_equal_endurance,
                    rsi_equal_endurance):
    is_price_ok = __is_price_eq_or_hi(price_l, price_r, price_equal_endurance)
    is_rsi_ok = __is_rsi_hi_deviation(rsi_l, rsi_r, rsi_equal_endurance)
    if is_price_ok and is_rsi_ok:
        if (i_r - i_l - 1) < valid_2_point_distance:
            logger.debug("顶背离发生，但两点距离太近(实际距离：%s， 期望：%s)" % (i_r - i_l - 1, valid_2_point_distance))
            return False
        else:
            logger.debug("顶背离发生")
            return True
    elif not is_price_ok:
        logger.debug("价格不满足")
        return False
    elif not is_rsi_ok:
        logger.debug("RSI没有顶背离")
        return False

    return False
