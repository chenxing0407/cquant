# -*- coding: utf-8 -*-
import easyutils
from cquant.db.model import DanDanQushi, get_session, get_engine
from cquant.utils.send_msg import send_msg
from cquant.utils.config import cfg


import pandas as pd
import time
from datetime import date
from datetime import datetime
from datetime import timedelta

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt


VALVE_AMOUNT = cfg['qushi_valve_amount']
STEP_AMOUNT = cfg['qushi_step_amount']

NOW = datetime.now()
KP = NOW.replace(hour=9, minute=25)
LUNCH = NOW.replace(hour=11, minute=30)
KP2 = NOW.replace(hour=13, minute=0)
TEN = NOW.replace(hour=10, minute=15)
THREE = NOW.replace(hour=15, minute=1)

send_map = {}


S1 = '''<html>
<meta http-equiv="refresh" content="5">
<head>
<body>

<table border="1">

'''
S2 = '''

</table>
</body>
</html>
'''

fname = cfg['html_file_name']


def save_qushi(res):
    objs = []
    for x in res:
        objs.append(DanDanQushi(
            code=x, amount=res[x], date=date.today(),
            time=datetime.now().strftime('%H:%M')))
    ss = get_session()
    ss.bulk_save_objects(objs)


def plt_qushi(code):
    sql_cmd = 'select time, amount from stock_dadan_qushi ' \
              'where date="%s" and code="%s"' \
              % (date.today().strftime('%Y-%m-%d'), code)
    qs = pd.read_sql(sql_cmd, con=get_engine())
    pd.Series(data=list(qs.amount), index=qs.time).plot()
    plt.savefig(cfg['image_save_path'] +'%s.png' % code)
    plt.close()


def calc(data):
    res = {}
    for index, row in data.iterrows():
        amount = row.s
        t = row.type
        code = row.code
        if code not in res:
            res[code] = {}
            res[code]['diff'] = 0
            if t == 'B':
                res[code]['diff'] += amount
            else:
                res[code]['diff'] -= amount
            res[code][t] = amount
        else:
            if t == 'B':
                res[code]['diff'] += amount
            else:
                res[code]['diff'] -= amount
            res[code][t] = amount

    final_res = {}
    for x in res:
        final_res[x] = res[x]['diff']
    save_qushi(final_res)

    sr = sorted(final_res.items(), key=lambda d: -d[1])
    now = datetime.now()
    msg = []
    for x in sr:
        if x[1] > VALVE_AMOUNT and x[0] not in send_map:
            msg.append('%s, %s' % (x[0], x[1]))
            send_map[x] = {}
            send_map[x]['send_at'] = datetime.now()
            send_map[x]['diff'] = x[1]
            plt_qushi(x[0])
        elif x[0] in send_map:
            if (now - timedelta(minutes=2)) < send_map[x]['send_at'] or \
                    (x[1] - send_map[x]['diff'] > STEP_AMOUNT):
                plt_qushi(x[0])
                msg.append('%s, %s' % (x[0], x[1]))
                send_map[x]['send_at'] = datetime.now()
                send_map[x]['diff'] = x[1]
    send_msg('\n'.join(msg))

    with open(fname, 'w') as f:
        f.write(S1)
        s = '<tr> <td>%s </td><td><img width=120 src=%s></img></td></tr>'
        for a in msg:
            f.write(s % (a, a.split(',')[0] + '.png'))
        f.write(S2)


def calc_fun():
    while True:
        now = datetime.now()
        count = 0
        if not easyutils.is_holiday(now.strftime('%Y%m%d')):
            sql_cmd = 'select sum(count*price) as s ,type, code from ' \
                      'stock_dadan_history where date="%s" group by ' \
                      'type, code order by code, s desc;' \
                      % date.today().strftime('%Y-%m-%d')
            if count % 30 == 0:
                print('sleep in sql %s' % datetime.now())
            count += 1
            try:
                while now < KP:
                    time.sleep(2)
                    now = datetime.now()

                while LUNCH < now < KP2:
                    time.sleep(2)
                    now = datetime.now()
                if now > THREE:
                    time.sleep(600)

                df_mysql = pd.read_sql(sql_cmd, con=get_engine())
                calc(df_mysql)
                time.sleep(5)
            except Exception as e:
                print(e)
                continue
        else:
            print('now %s is holiday, sleeping ...' % now)
            time.sleep(24 * 3600)
            count = 0


if __name__ == '__main__':
    calc_fun()
