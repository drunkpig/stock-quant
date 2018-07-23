from gm.api import current, history_n


def is_stock_index_down_much(symbol, threshold=0):
    data = history_n(symbol=symbol, count=1, frequency='1d',df=False)

    return 3, False



def is_stock_down_much(symbol, threshold=0):
    current_data = current(symbol,fields='open,price')
    return 1, False


