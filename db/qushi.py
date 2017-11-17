# -*- coding: utf-8 -*-
import traceback

import easyutils
from cquant.db.model import get_session
from cquant.utils.config import cfg


import time
import datetime
from influxdb import InfluxDBClient

VALVE_AMOUNT = cfg['qushi_valve_amount']
STEP_AMOUNT = cfg['qushi_step_amount']


RECORD_COUNT = 0


def send_to_influxdb():
    cl = InfluxDBClient(host=cfg['influx_db_url'], database='stock')
    n1 = datetime.datetime.now().replace(hour=0)
    n1str = n1.strftime('%Y-%m-%d %H-%M-%S')
    ss = get_session()
    cmd = 'select * from stock_dadan_qushi2  where timestamp >"%s" order by id desc limit %d' % (n1str, RECORD_COUNT)
    res = ss.execute(cmd)
    points = []
    for x in res:
        p = {
            "measurement": "qushi",
            "tags": {
                "code": x.code,
            },
            "time": x.timestamp,
            "fields": {
                "value": x.amount
            }
        }
        points.append(p)
    cl.write_points(points)


def save_qushi():
    n1 = datetime.datetime.now().replace(hour=0)
    n1str = n1.strftime('%Y-%m-%d %H-%M-%S')
    ss = get_session()
    global RECORD_COUNT
    count_cmd = 'select distinct(code) as count from stock_dadan_history2 where timestamp >"%s"' % n1str
    res = ss.execute(count_cmd)
    RECORD_COUNT = len(res.fetchall())
    cmd = 'insert into stock_dadan_qushi2(code, amount,timestamp) select code, sum(amount),date_add(current_timestamp, interval 8 hour) from ' \
          'stock_dadan_history2 where timestamp >"%s" group by code' % n1str
    ss.execute(cmd)

    send_to_influxdb()


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
                try:
                    save_qushi()
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                    time.sleep(5)
                    continue

                time.sleep(5)

        else:
            while True:
                now = datetime.datetime.now()
                if not easyutils.is_holiday(now.strftime('%Y%m%d')):
                    break
                else:
                    print('now %s is holiday, sleeping ...' % now)
                    time.sleep(60)


if __name__ == '__main__':
    calc_fun()
