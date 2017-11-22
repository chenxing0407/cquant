# -*- coding: utf-8 -*-

from cquant.utils.config import cfg
from cquant.db.model import get_session, StockDaDantHistory2
from cquant.est.dadan_history_calc import get_cand_code

import easyquotation
import time
import threading
import datetime
import easyutils

last_check = {}

VALVE = cfg['dadan_valve']


# t 类型（B/S)
# diff 成交量差额
def add_to_db(code, diff, st):
    sess = get_session()
    dadan = StockDaDantHistory2(code=code, timestamp='%s %s' %
                                                     (st['date'], st['time']),
                                amount=diff*st['now'])
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
    while True:
        now = datetime.datetime.now()
        kp = now.replace(hour=9, minute=25)
        lunch = now.replace(hour=11, minute=30)
        kp2 = now.replace(hour=13, minute=0)
        three = now.replace(hour=15, minute=1)

        if not easyutils.is_holiday(now.strftime('%Y%m%d')):
            previous_day = now.strftime('%d')
            count = 0
            while True:
                now = datetime.datetime.now()
                if count % 30 == 0:
                    print('now is %s, count is %s' % (time.ctime(), count))
                count += 1

                while now < kp:
                    time.sleep(10)
                    now = datetime.datetime.now()
                    kp = now.replace(hour=9, minute=25)

                while lunch < now < kp2:
                    time.sleep(10)
                    now = datetime.datetime.now()
                    lunch = now.replace(hour=11, minute=30)
                    kp2 = now.replace(hour=13, minute=0)

                while now > three:
                    print('now is %s, not holiday' % (time.ctime()))
                    time.sleep(60)
                    now = datetime.datetime.now()
                    three = now.replace(day=now.day, hour=15, minute=1)

                current_day = now.strftime('%d')
                if current_day != previous_day:
                    break

                for code, st in sina.stocks(candi).items():
                    try:
                        if st['name'] not in last_check:
                            last_check[st['name']] = {}
                            last_check[st['name']]['turnover'] = st['turnover']
                            last_check[st['name']]['now'] = st['now']
                            last_check[st['name']]['buy'] = st['buy']
                            last_check[st['name']]['sell'] = st['sell']

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
                                                add_to_db(code, diff, st)
                                        else:
                                            if st['now'] * diff > VALVE:  # 发出卖出指令
                                                add_to_db(code, -diff, st)

                                    if st['now'] == st['sell']:
                                        if st['now'] * diff > VALVE:  # 发出买入指令
                                            add_to_db(code, diff, st)

                                # 价格减少
                                elif st['now'] < last_check[st['name']]['now']:
                                    if st['now'] == st['sell']:
                                        if st['sell'] < last_check[st['name']]['sell']:
                                            if st['now'] * diff > VALVE:  # 发出卖出指令
                                                add_to_db(code, -diff, st)

                                        else:
                                            pass
                                    else:
                                        # todo now == buy
                                        if st['now'] * diff > VALVE:  # 发出卖出指令
                                            add_to_db(code, -diff, st)

                                # 价格增加
                                else:
                                    if not (st['sell'] <
                                            last_check[st['name']]['sell']):
                                        if st['now'] * diff > VALVE:  # 发出买入指令
                                            add_to_db(code, diff, st)
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
        else:
            while True:
                now = datetime.datetime.now()
                print('now %s is holiday, sleeping ...' % now)
                time.sleep(60)
                if not easyutils.is_holiday(now.strftime('%Y%m%d')):
                    break


if __name__ == '__main__':
    sina_api = easyquotation.use('sina')
    # stock_codes = sina_api.load_stock_codes()
    # stock_with_exchange_list = [easyutils.stock.get_stock_type(code) +
    #                             code[-6:]
    #                             for code in stock_codes
    #                             if code.startswith(('00', '30', '60'))]

    stock_with_exchange_list = [easyutils.stock.get_stock_type(code) +
                                code
                                for code in get_cand_code()]

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
