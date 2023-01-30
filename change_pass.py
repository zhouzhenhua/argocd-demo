#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# @Author  : zhouzh

import sys
import os
import requests
import json
import string
import random
import time

username='acs'
password=''.join(random.sample( string.letters + string.digits, 14))
pass_db_path='/data/nginx/htpasswd/.acs.htpasswd'

def Change_Pass():
    try:
        os.system('/usr/bin/htpasswd -b {pass_db_path} {username} {password}'.format(pass_db_path=pass_db_path,username=username,password=password))
        Dingding_Send(username, password,'成功')

    except Exception as e:
        print(e)


def Dingding_Send(username, password,status):
    headers = {'Content-Type': 'application/json'}
    Api_Url_list = [
                   #
                   "https://oapi.dingtalk.com/robot/send?access_token=42170caa98337524e2fdac16f42ca06dfe68e7c3fd6eee84e9c9380c95786876",
                   #内部系统外部密码推送群
                   "https://oapi.dingtalk.com/robot/send?access_token=45a9ef6b33a3c7d117a859730aff0c12c51c429064ddd47ec01c8d6d6ae754d7"
                   ]
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "推送通知",
            "text": "### 催收密码重置消息通知\n" +
                   "**帐号**:  {0} \n".format(username) + '\n'
                   "**密码**:  {0} \n".format(password) + '\n'
                   "**网址**:\n" 
                   "> [催收系统](http://acs.zfurl.cn/login)\n\n" + '\n'
                   "**时间**:  {0} \n".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + '\n'
                   "**状态**:  <font color=#38C759> {0} \n".format(status)  + '\n'

        },
        "at": {
            "isAtAll": 'True'
    }
    }
    for Api_Url in Api_Url_list:
        print (requests.post(url=Api_Url, headers=headers, data=json.dumps(data)).text)


if __name__ == '__main__':

    Change_Pass()
