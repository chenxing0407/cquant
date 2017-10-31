# -*- coding: utf-8 -*-

from utils.config import cfg
from .model import get_session
from .model import StockDaDantHistory

import easyquotation
import time
import threading
import datetime
import easyutils

last_check = {}
NOW = datetime.datetime.now()
KP = NOW.replace(hour=9, minute=25)
LUNCH = NOW.replace(hour=11, minute=30)
KP2 = NOW.replace(hour=13, minute=0)
TEN = NOW.replace(hour=10, minute=15)
THREE = NOW.replace(hour=15, minute=1)

VALVE = cfg['valve']


# t 类型（B/S)
# diff 成交量差额
def add_to_db(code, t, diff, st):
    sess = get_session()
    dadan = StockDaDantHistory(code=code, time=st['time'], date=st['date'],
                               name=st['name'],
                               type=t, count=diff, price=st['now'],
                               high=st['high'], low=st['low'])
    sess.begin()
    sess.add(dadan)
    sess.commit()


'''
价格无变动
now == buy
  buy > last_buy
    B
  else:
    S

now == sell
  B



价格减少
   now == buy
     S
   now == sell:
     sell < last_sell
       S
     else：
       M


价格增加：
sell < last_sell
 M
else:
   B

'''


def get_real(candi):
    sina = easyquotation.use('sina')
    count = 0
    while True:
        if count/30 == 0:
            print('now is %s, count is %s' % (time.ctime(), count))
        count += 1
        now = datetime.datetime.now()
        while now < KP:
            time.sleep(2)
            now = datetime.datetime.now()

        while LUNCH <now < KP2:
            time.sleep(2)
            now = datetime.datetime.now()
        if now > THREE:
            time.sleep(600)

        for code, st in sina.stocks(candi).items():
            try:
                if st['name'] not in last_check:
                    last_check[st['name']] = {}
                    last_check[st['name']]['turnover'] = st['turnover']
                    last_check[st['name']]['now'] = st['now']
                    last_check[st['name']]['buy'] = st['buy']
                    last_check[st['name']]['sell'] = st['sell']
                    last_check[st['name']]['rec'] = [] # 详细记录

                else:
                    # no change
                    if last_check[st['name']]['turnover'] == st['turnover']:
                        pass
                    else:
                        diff = st['turnover'] - \
                               last_check[st['name']]['turnover']

                        # TODO 准确性检查

                        # 价格无变动
                        if st['now'] == last_check[st['name']]['now']:
                            if st['now'] == st['buy']:
                                if st['buy'] > last_check[st['name']]['buy']:
                                    if st['now'] * diff > VALVE:  # 发出买入指令
                                        add_to_db(code, 'B', diff, st)
                                else:
                                    if st['now'] * diff > VALVE:  # 发出卖出指令
                                        add_to_db(code, 'S', diff, st)

                            if st['now'] == st['sell']:
                                if st['now'] * diff > VALVE:  # 发出买入指令
                                    add_to_db(code, 'B', diff, st)

                        # 价格减少
                        elif st['now'] < last_check[st['name']]['now']:
                            if st['now'] == st['sell']:
                                if st['sell'] < last_check[st['name']]['sell']:
                                    if st['now'] * diff > VALVE:  # 发出卖出指令
                                        add_to_db(code, 'S', diff, st)

                                else:
                                    pass
                            else:
                                # todo now == buy
                                if st['now'] * diff > VALVE:  # 发出卖出指令
                                    add_to_db(code, 'S', diff, st)

                        # 价格增加
                        else:
                            if not (st['sell'] <
                                    last_check[st['name']]['sell']):
                                if st['now'] * diff > VALVE:  # 发出买入指令
                                    add_to_db(code, 'B', diff, st)
                            else:
                                pass

                        # 更新最新的数据
                        last_check[st['name']]['turnover'] = st['turnover']
                        last_check[st['name']]['now'] = st['now']
                        last_check[st['name']]['buy'] = st['buy']
                        last_check[st['name']]['sell'] = st['sell']
            except Exception as e:
                print(e)
                continue

        time.sleep(2)


if __name__ == '__main__':
    easyquotation.update_stock_codes()
    sina_api = easyquotation.use('sina')
    stock_codes = sina_api.load_stock_codes()
    stock_with_exchange_list = [easyutils.stock.get_stock_type(code) +
                                code[-6:]
                                for code in stock_codes
                                if code.startswith(('00', '30', '60'))]

    request_num = len(stock_with_exchange_list)
    max_num = 400
    t_count = int(request_num/max_num) + 1
    for range_start in range(t_count):
        num_start = max_num * range_start
        num_end = max_num * (range_start + 1)
        th = threading.Thread(
            target=get_real,
            args=(stock_with_exchange_list[num_start:num_end],))
        print('starting one thread....')
        th.start()
