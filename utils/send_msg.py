# -*- coding: utf-8 -*-

from config import cfg

import json
import traceback
from datetime import datetime, timedelta

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


Gtoken = ''
token_get_time = ''


def get_token():
    global Gtoken, token_get_time
    now = datetime.now()
    if not Gtoken or (token_get_time+timedelta(seconds=7100) < now):

        #微信公众号上应用的CropID和Secret
        CropID= cfg['corpid']
        Secret= cfg['secret']

        #获取access_token
        GURL="https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s" % (CropID, Secret)
        try:
            res = requests.get(GURL, verify=False)
            dict_result = json.loads(res.text)
        except Exception as e:
            print(traceback.format_exc())

        # error happened
        if 'errcode' in dict_result and dict_result['errcode'] != 0:
            print(dict_result)
            # 主动过期，再次获取
            token_get_time = datetime.now() + timedelta(seconds=-7210)

        Gtoken=dict_result['access_token']
        token_get_time = datetime.now()
        return Gtoken
    else:
        return Gtoken


def send_msg(msg):
    PURL = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % get_token()

    # 生成post请求信息
    post_data = {}
    post_data['touser'] = cfg['msg_send_to']
    post_data['msgtype'] = 'text'
    post_data['agentid'] = 1
    post_data['text'] = {'content': msg}
    post_data['safe'] = '0'
    # 由于字典格式不能被识别，需要转换成json然后在作post请求
    # 注：如果要发送的消息内容有中文的话，第三个参数一定要设为False
    json_post_data = json.dumps(post_data)
    try:
        request_post = requests.post(PURL, json_post_data, verify=False)
    except Exception as e:
        print(traceback.format_exc())

    if request_post.status_code != 200:
        print(request_post.text)
    result = json.loads(request_post.content)
    if 'errcode' in result and result['errcode'] != 0:
        print(result)


if __name__ == '__main__':
    for i in range(1):
        send_msg('test msg3')
