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


def save_qushi():
    n1 = datetime.now().replace(hour=0)
    n1str = n1.strftime('%Y-%m-%d %H-%M-%S')
    ss = get_session()
    cmd = 'insert into stock_dadan_qushi2(code, amount) select code, sum(amount) from ' \
          'stock_dadan_history2 where timestamp >"%s" group by code' % n1str
    ss.execute(cmd)


def plt_qushi(code):
    n1 = datetime.now().replace(hour=0)
    n1str = n1.strftime('%Y-%m-%d %H-%M-%S')
    sql_cmd = 'select timestamp, amount from stock_dadan_qushi2 ' \
              'where code="%s" and timestamp >"%s"  ' \
              % (code, n1str)
    qs = pd.read_sql(sql_cmd, con=get_engine())
    pd.Series(data=list(qs.amount), index=qs.timestamp).plot()
    plt.savefig(cfg['image_save_path'] +'%s.png' % code)
    plt.close()


def calc():
    save_qushi()

    valve = 1
    n1 = datetime.now().replace(hour=0)
    n1str = n1.strftime('%Y-%m-%d %H-%M-%S')
    ss = get_session()
    cmd = 'select code, sum(amount) as amount from stock_dadan_qushi2 where timestamp >"%s" and amount >%f group by code order by amount' % (n1str, valve)
    res = ss.execute(cmd)
    msg = []
    for x in res:
        msg.append('%s, %s' % (x.code, x.amount))
        plt_qushi(x.code)
    send_msg('\n'.join(msg))

    with open(fname, 'w') as f:
        f.write(S1)
        s = '<tr> <td>%s </td><td><img width=120 src=%s></img></td></tr>'
        for a in msg:
            f.write(s % (a, a.split(',')[0] + '.png'))
        f.write(S2)


def calc_fun():
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
                    three = now.replace(hour=15, minute=1)

                current_day = now.strftime('%d')
                if current_day != previous_day:
                    break
                # TODO 某一刻记录下 qushi
                calc()

                time.sleep(5)

        else:
            while True:
                now = datetime.datetime.now()
                print('now %s is holiday, sleeping ...' % now)
                time.sleep(60)
                if not easyutils.is_holiday(now.strftime('%Y%m%d')):
                    break


if __name__ == '__main__':
    calc_fun()
