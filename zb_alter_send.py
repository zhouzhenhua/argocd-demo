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
ZABBIX_URL = 'http://zabbix..com'
ZABBIX_USER = 'zabbix_api'
ZABBIX_PASS = 'zabbix_api'
BUCKET = 'zabbix-zof'
QINGYUN_CONFIG = Config('xxxx', 'xxxxx')

# setup logger
LOG_FILE = '/data/log/zabbix/dingding.log'


if not isdir(dirname(LOG_FILE)):
    os.makedirs(dirname(LOG_FILE))


def get_logger():
    logger = logging.getLogger('dingding')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    th = TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, backupCount=7, encoding='utf-8')
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




if __name__ == '__main__':

    user = sys.argv[1]
    title = sys.argv[2]
    text = str(sys.argv[3])
    content = ""
    server_name = ""
    item_id = ""
    zone = ""
    level = ""

    for i in text.split(','):
        if re.match('服务器', i):
            server_name = re.match('服务器：(.*)', i).group(1).strip()
            zone = server_name.split('-')[0]
            print server_name
        if re.match('告警级别', i):
            level = re.match('告警级别：【(.*)】', i).group(1).strip()
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
    
    send_data = {
        'title':title,
        'content':content,
        'source_type':zone,
        'level':level
    }
    requests.post('http://192.168.139.3:18380/audi/api/v1/alarm/notify', data=send_data)
