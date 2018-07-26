import time


def now_tm():
    str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    return str
