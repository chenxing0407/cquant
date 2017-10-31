# -*- coding: utf-8 -*-

from db.model import StockDaDantHistory, EstProfit, get_session, \
    StockCurrentInfo
from utils.config import cfg

from datetime import datetime
from sqlalchemy import desc, text
import pandas as pd
import easyutils


def get_close_price(code, date):
    sess = get_session()
    res = sess.query(StockDaDantHistory).filter(StockDaDantHistory.code == code) \
        .filter(StockDaDantHistory.date == date).order_by(
        desc(StockDaDantHistory.id)).first()
    return res.price if res else 0


def get_cand_code():
    sess = get_session()
    res = sess.query(StockCurrentInfo).filter(text(cfg[
                                                  'candidate_code_condition'])).all()
    return [x.code for x in res]


# 根据持续买入/卖出大单数量的 成交金额来判断。
# 每次买入的是一单价格
# 与每天的收盘价比较计算当天的收益
# count 连续次数的列表
# valve 金额的列表, 会乘以 * 10000

def calc_history_method1(c, d, count=10, valve=5000000):
    price = get_close_price(c, d)
    if price == 0:
        return
    sess = get_session()
    res = sess.query(StockDaDantHistory).filter(StockDaDantHistory.code == c) \
        .filter(StockDaDantHistory.date == d).all()

    if len(res) == 0:
        return

    for cc in count:
        for vv in valve:
            vv = vv * 10000
            print('#########date %s, code %s, count %s, valve %s #############'
                  % (d, c, cc, vv))

            hists = []
            rec = []
            last_sum = 0
            for x in res[:]:
                amount = x.count * x.price if x.type == 'B' else -x.count * x.price
                hists.append(amount)

                if len(hists) > cc:
                    hists = hists[-cc:]
                # print(hists)
                sum_amount = sum(hists)
                # if sum_amount > valve1:
                if sum_amount > vv and sum_amount > last_sum:
                    print('buy %s at %s with price %s, sum is %s, ' % (
                    x.code, x.time, x.price, sum_amount))
                    rec.append(x.price)
                # elif sum_amount < -valve1:
                elif sum_amount < -vv and sum_amount < last_sum:
                    print('sell %s at %s with price %s, sum is %s, ' % (
                    x.code, x.time, x.price, sum_amount))
                    rec.append(-x.price)
                last_sum = sum_amount
            profit = 0
            for x in rec:
                if x > 0:
                    profit += price - x
                else:
                    profit += -(x + price)
            if profit != 0:
                print('you earn %s if count  %s valve %s' % (profit, cc, vv))
                sess.begin()
                sess.add(EstProfit(code=c, date=d, count=cc, valve=vv,
                                   profit=profit))
                sess.commit()


if __name__ == '__main__':
    # print(get_cand_code())
    date = datetime.now().strftime('%Y-%m-%d')
    date_list = pd.date_range(cfg['est_begin_date'], pd.datetime.today()).tolist()
    trade_day = [d.date().strftime('%Y-%m-%d') for d in date_list if
                 not easyutils.is_holiday(d.date().strftime('%Y%m%d'))]
    code_list = get_cand_code()
    for code in code_list:
        for d in trade_day:
            calc_history_method1(code, d,
                                 count=range(3, 20, 2),
                                 valve=range(500, 5500, 500))
            # calc_history_method1(code, d, count=10, valve=1000 * 10000)
            # calc_history_method1(code, d, count=10, valve=2000 * 10000)
            # calc_history_method1(code, d, count=10, valve=500 * 10000)

            # calc_history_method1(code, d, count=5, valve=1000 * 10000)
            # calc_history_method1(code, d, count=5, valve=2000 * 10000)
            # calc_history_method1(code, d, count=5, valve=500 * 10000)
