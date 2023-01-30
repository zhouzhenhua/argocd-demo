#!/srv/python2/bin/python
# _*_coding:utf-8 _*_
# zabbix钉钉报警
import requests
import json
import sys
import logging
import urllib2
import re
import time,datetime
import os
import uuid
from os.path import basename, dirname, isdir
from logging.handlers import TimedRotatingFileHandler
from qingstor.sdk.service.qingstor import QingStor
from qingstor.sdk.config import Config

HEADERS = {'Content-Type': 'application/json-rpc'}
ZABBIX_URL = 'http://zabbix.qx.com'
ZABBIX_USER = 'zabbix_api'
ZABBIX_PASS = 'zabbix_api'
BUCKET = 'zabbix-dof'
QINGYUN_CONFIG = Config('xxxxx', 'xxxxx')

# setup logger
LOG_FILE = '/data/log/zabbix/dingding.log'

CALL_LEVEL = ['High', 'Disaster']


HOLIDAY = {
     5 : '星期六',
     6 : '星期天',
}


DEFAULT_CALL_TIME = {
    "workday":{
        "start_time": "21:00:00",
        "stop_time": "08:00:00"
    },
    "holiday": {
        "start_time": "00:00:00",
        "stop_time": "23:59:59"
    }
}

DEFAULT_DINGDING_TOKEN = 'xxxxx'


ZONE_ALTER = {
        'dac':{
            'phone':["13488684017", "18501359852"],
            'call': True,
            'call_time':DEFAULT_CALL_TIME,
            'dingding':True,
            'dingding_token':DEFAULT_DINGDING_TOKEN,
        },
        'flb':{
            'phone':["18668302886", "18501359852"],
            'call': True,
            'call_time':DEFAULT_CALL_TIME,
            'dingding':True,
            'dingding_token':DEFAULT_DINGDING_TOKEN,
        },
        'yna':{
            'phone':["18668302886", "18501359852"],
            'call': True,
            'call_time':DEFAULT_CALL_TIME,
            'dingding':True,
            'dingding_token':DEFAULT_DINGDING_TOKEN,
        },
        'dof':{
            'phone':["18668302886", "18501359852"],
            'call': True,
            'call_time':DEFAULT_CALL_TIME,
            'dingding':True,
            'dingding_token':DEFAULT_DINGDING_TOKEN,
        },
        'tcs': {
            'phone': ["18668302886", "18501359852"],
            'call': True,
            'call_time': DEFAULT_CALL_TIME,
            'dingding': True,
            'dingding_token': DEFAULT_DINGDING_TOKEN,
        },
        'xyy': {
            'as_phone': ["18668302886", "18501359852"],
            'db_phone': ["18668302886", "18501359852"],
            'call': True,
            'call_time': DEFAULT_CALL_TIME,
            'dingding': True,
            'dingding_token': DEFAULT_DINGDING_TOKEN,
        },
}


KEYWORDS_COLOR = {
    "Average":'<font color=#FF8C00 size=4 face="黑体">Average</font>', #黄色
    "High":'<font color=#FF0000 size=4 face="黑体">High</font>',    #红色
    "OK":'<font color=#00FF00 size=4 face="黑体">Ok</font>',       #绿色
    "PROBLEM":'<font color=#FF0000 size=4 face="黑体">Problem</font>', #红色
}


if not isdir(dirname(LOG_FILE)):
    os.makedirs(dirname(LOG_FILE))


def get_logger():
    logger = logging.getLogger('dingding')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    th = TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, backupCount=7)
    th.setFormatter(formatter)
    logger.addHandler(th)

    return logger


logger = get_logger()


class Base(object):
    """
    获取zabbix Token
    """

    def __init__(self, username=ZABBIX_USER, password=ZABBIX_PASS, url='%s/api_jsonrpc.php' % ZABBIX_URL):
        self.data = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": "%s" % username,
                "password": "%s" % password
            },
            "id": 0,
        }
        self.url = url
        self.token = ''

    def _openurl(self, **kwargs):
        req = urllib2.Request(**kwargs)
        try:
            rfp = urllib2.urlopen(req)
        except Exception, e:
            return False, e

        if rfp.getcode() != 200:
            return False, 'Http Code not 200'

        response_raw = rfp.read()

        try:
            response = json.loads(response_raw)
        except:
            return False, 'Unpack json error'

        if response.get('error', False):
            return False, response.get('error')

        return True, response.get('result')

    def login(self):
        ret, self.token = self._openurl(url=self.url, data=json.dumps(self.data), headers=HEADERS)
        return ret, self.token


class ZabbixApi(Base):

    def __set(self, params, action):
        data = {
            "jsonrpc": "2.0",
            "method": action,
            "params": params,
            "id": 0,
            "auth": self.token
        }

        return self._openurl(url=self.url, data=json.dumps(data), headers=HEADERS)


    def get_item_graph(self, item_id=None):
        params = {
            "output": "extend",
            "itemids": item_id
        }

        ret, info = self.__set(params, action='graphitem.get')
        if not ret:
            return False, info
        result = []
        for i in info:
            result.append(i.get('graphid'))
        return True, result

    def get_action(self):
        params = {
            "output": "extend",
            "selectOperations": "extend",
            "selectFilter": "extend",
            "filter": {
                "eventsource": 2
            }
        }
        ret, info = self.__set(params, action="action.get")
        if not ret:
            return False, info
        return True, info


class Dingding(object):
    def __init__(self, token=''):
        self.url = "https://oapi.dingtalk.com/robot/send?access_token=%s" % token

    def send(self, title='', context='',mobiles=[]):
        headers = {'Content-Type': 'application/json'}

        tmp = title +"\n" + context

        for key,value in KEYWORDS_COLOR.items():
            if re.search(key,tmp):
                tmp = tmp.replace(key,value)

        send_data = {
            "msgtype": "markdown",
            "markdown":
            {
                "title": title,
                "text": '#### %s\n' % tmp  + "联系人："
            },
            "at": {
                "isAtAll":False
            }
        }
        if mobiles:
            at_mobiles = list(map(str, mobiles))
            at_mobiles_text = ' '.join([ '@%s'%i for i in at_mobiles])
            send_data["markdown"]["text"] += at_mobiles_text
            send_data["at"]["atMobiles"] = at_mobiles


        logger.info('send ding data:%s'%send_data)
        try:
            res = requests.post(url=self.url, data=json.dumps(send_data), headers=headers)
        except Exception, e:
            return False, str(e)

        if res.status_code != 200:
            return False, res.content()

        return True, ''


def upload_s3(imag_url):
    filename = 'zabbix_%s_%s' % (str(uuid.uuid4()), info[-1])
    with open('/tmp/%s' % filename, 'wb') as f:
        f.write(requests.get(zabbix_imag_url).content)
    try:
        qingstor = QingStor(QINGYUN_CONFIG)
        bucket = qingstor.Bucket(BUCKET, 'pek3b')
        with open('/tmp/%s' % filename, 'rb') as f:
            output = bucket.put_object(filename, body=f)
        if output.status_code > 400:
            return False,'upload s3 code error：%s' % output.status_code

    except Exception as e:
        return False,'upload s3 exception'

    os.unlink('/tmp/%s' % filename)
    s3_image_url = "http://%s.pek3b.qingstor.com/%s" % (BUCKET, filename)
    return True,s3_image_url



def send_alert(alter_data=None,alter_meta=None):

    cur_level = ''
    call_phone = 'as_phone'
    if alter_data.get('server_type') in ['db','bac']:
        call_phone = 'db_phone'

    phone_list = alter_meta.get(call_phone) if alter_meta.get(call_phone) else alter_meta.get('phone')
    call_text = alter_data.get('zone') + '区域有' + cur_level + '预警级别，详细信息请查看钉钉'


    for i in CALL_LEVEL:
        if re.search(i,alter_data.get('content','')):
            cur_level = i
            break

    logger.info('level:%s %s'%(cur_level,alter_meta.get('call','')))
    if alter_meta.get('dingding',''):
        dd = Dingding(alter_meta.get('dingding_token'))
        ret, info = dd.send(alter_data.get('title'), alter_data.get('content'),phone_list)
        if not ret:
            logger.error('send dingding fail')
        else:
            logger.info('send dingding success')


    if cur_level and alter_meta.get('call','') and phone_list:

        day_Week = datetime.datetime.now().weekday()

        call_time = alter_meta.get('workday',DEFAULT_CALL_TIME['workday'])
        if day_Week  in HOLIDAY:
            call_time = alter_meta.get('holiday',DEFAULT_CALL_TIME['holiday'])

        call_text = zone + '区域有' + cur_level + '预警级别，详细信息请查看钉钉'
        data = {
            "call_time": call_time,
            "call_phone": phone_list,
            "title": title,
            "call_content": call_text,
            "dingding": 0,
            "interval": 15,
            "type": "dof_zabbix",
            "dingding_token": alter_meta.get('dingding_token')
        }
        logger.info('send freeswitch body:%s'%data)
        resp = requests.post('http://haval:7socQoICzeqwtQ@192.168.228.2:19059/haval/alarm/call/other',
                             data=json.dumps(data), verify=False, timeout=10)
        if resp.status_code != 200:
            logger.error('send freeswitch fail')
        else:
            logger.info('send freeswitch success')



if __name__ == '__main__':

    user = sys.argv[1]
    title = sys.argv[2]
    text = str(sys.argv[3])
    content = ""
    server_name = ""
    # trigger = ""
    item_id = ""
    zone = ""

    for i in text.split(','):
        if re.match('服务器', i):
            server_name = re.match('服务器：(.*)', i).group(1).strip()
            zone = server_name.split('-')[0]
        # if re.match('故障内容', i):
        #     trigger = re.match('故障内容：(.*)', i).group(1).strip()
        if re.match('ITEM.ID', i):
            item_id = re.match('ITEM.ID：(.*)', i).group(1).strip()
            zbx = ZabbixApi()
            ret, info = zbx.login()
            if not ret:
                logger.error('connect to zabbix fail:%s' % (info))
            ret, info = zbx.get_item_graph(item_id=item_id)

            if not ret:
                logger.info('no found trigger graph:%s' % (info))
            else:
                if info:
                    zabbix_imag_url = '%s/chart2.php?graphid=%s&curtime=%s&period=3600' % (
                        ZABBIX_URL, info[-1], str(int(time.time())))
                    s3_image_url = ''
                    ret,info = upload_s3(zabbix_imag_url)
                    if ret:
                        s3_image_url = info

                    content = content + "> ![screenshot](%s\n)" % str(s3_image_url)
            continue

        content = content + "> ##### %s\n" % i

    alter_data = {
        'title':title,
        'content':content,
        'server_type':server_name.split('-')[-2],
        'zone':zone
    }

    if zone in ZONE_ALTER:
        send_alert(alter_data,ZONE_ALTER[zone])

