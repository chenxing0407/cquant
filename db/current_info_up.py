# -*- coding: utf-8 -*-

import easyquotation
import easyutils
from model import StockCurrentInfo, get_session


def up():
    qq = easyquotation.use('qq')
    stock_codes = qq.load_stock_codes()
    stock_with_exchange_list = [easyutils.stock.get_stock_type(code) + code[-6:]
                                for code in stock_codes if
                                code.startswith(('00', '30', '60'))]

    request_num = len(stock_with_exchange_list)
    max_num = 400
    t_count = int(request_num / max_num) + 1

    for range_start in range(t_count):
        res = []
        num_start = max_num * range_start
        num_end = max_num * (range_start + 1)
        for code, st in qq.stocks(stock_with_exchange_list[
                                  num_start:num_end]).items():
            res.append(StockCurrentInfo(code=code, name=st['name'],
                                        high=st['high'], low=st['low'],
                                        ltsz=st['流通市值'], total_sz=st['总市值'],
                                        pb=st['PB'], pe=st['PE'],
                                        date=st['datetime'].strftime(
                                            '%Y-%m-%d'), amount=st['成交额(''万)'],
                                        turnover=st['turnover'],
                                        volume=st['成交量(手)']
                                        ))
        ss = get_session()
        ss.bulk_save_objects(res)


if __name__ == '__main__':
    up()
