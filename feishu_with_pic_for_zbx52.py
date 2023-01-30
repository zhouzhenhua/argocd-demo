#!/usr/bin/env python
# -*- coding=utf-8 -*-
import os, time, json, requests, re, urllib3, sys, configparser, datetime, hashlib, logging, collections, traceback
from pyzabbix import ZabbixAPI

if sys.version_info[0] == 2:
    from urlparse import urljoin

    reload(sys)
    sys.setdefaultencoding('utf-8')
elif sys.version_info[0] == 3:
    from urllib.parse import urljoin

# 获取配置
#parent_dir = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read('/usr/local/zabbix-5.2.4/share/zabbix/alertscripts/feishu_with_pic.conf', encoding='utf-8')
#config.read(parent_dir + "/feishu_with_pic.conf", encoding='utf-8')
log_file = config.get('config', 'log')
RobotApi = config.get('config', 'webhook')
AppId = config.get('config', 'app_id')
AppSecret = config.get('config', 'app_secret')
TokenCacheFile = config.get('config', 'token_cache_file')
ZabbixUrl = config.get('config', 'zabbix_url')
ZabbixUser = config.get('config', 'zabbix_user')
ZabbixPass = config.get('config', 'zabbix_pass')
ZabbixPicPath = config.get('config', 'zabbix_pic_path')
log_file = config.get('config', 'log')

# debug config
Debug = int(config.get('config', 'debug_mode'))
DebugRobotApi = config.get('config', 'debug_webhook')

logger = logging.getLogger('feishu')
logger.setLevel(logging.INFO)
# create console handler
ch = logging.FileHandler(filename=log_file)
# ch = logging.StreamHandler()
# create formatter
formatter = logging.Formatter("%(asctime)s %(name)s [%(process)d][{0}:%(lineno)s] [%(levelname)s] %(message)s",
                              "%Y-%m-%d %H:%M:%S")
ch.setFormatter(formatter)
logger.addHandler(ch)


def make_feishu_req_data(zbx_url, event, alert_map, zbx_image_key):
    """
    文档：https://ding-doc.dingtalk.com/doc#/serverapi3/iydd5h
    :param zbx_image_key:
    :param zbx_url:
    :param event:
    :param alert_map: zabbix传入的message,已处理为dict
    :return: {}
    """
    # 字段展示顺序
    field_map = collections.OrderedDict([('ip_addr', 'IP地址'), ('host_name', '故障主机') ,('failed_time', '故障时间'), ('recovery_time', '恢复时间'),
                                         ('duration', '持续时间'), ('level', '故障级别')])
    if 'failed_time' in alert_map.keys():
        color = 'red'
        card_title = '故障卡'
    else:
        color = 'green'
        card_title = '恢复卡'
    true = True
    false = False
    card = {
        "config": {
            "wide_screen_mode": true
        },
        "header": {
            "title": {
                "tag": "plain_text",
                "content": card_title
            },
            "template": color
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**{host}: {title}**".format(host=alert_map.get('host', None), title=event)
                },
                "fields": []
            },
            {
                "tag": "markdown",
                "content": "![{title}]({img_key})".format(title=event, img_key=zbx_image_key)
            },
            {
                "tag": "hr"
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "Send at: {cur_time}".format(
                            cur_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    },
                    {
                        "tag": "lark_md",
                        "content": "| [最新数据]({zbx_url}/history.php?action=showgraph&itemids[]={item_id})".format(
                            zbx_url=zbx_url, item_id=alert_map.get('item_id', None))
                    },
                    {
                        "tag": "lark_md",
                        "content": "| [配置主机]({zbx_url}/hosts.php?form=update&hostid={host_id})".format(zbx_url=zbx_url,
                                                                                                       host_id=alert_map.get(
                                                                                                           'host_id',
                                                                                                           None))
                    }
                ]
            }
        ]
    }
    for k, v in field_map.items():
        if k in alert_map.keys():
            tp = {
                "is_short": False,
                "text": {
                    "tag": "lark_md",
                    "content": "{sub}：{val}".format(sub=v, val=alert_map[k])
                }
            }
            card['elements'][0]['fields'].append(tp)
    req_dict = {
        "msg_type": "interactive",
        "card": card
    }
    return json.dumps(req_dict, ensure_ascii=False)

class Zabbix_Graph(object):
    """ Zabbix_Graph """
    def __init__(self, url=None, user=None, pwd=None, logger=None, timeout=None):
        urllib3.disable_warnings()
        if timeout == None:
            self.timeout = 1
        else:
            self.timeout = timeout
        self.url = url
        self.user = user
        self.pwd = pwd
        self.cookies = {}
        self.zapi = None
        self.logger = logger

    def _do_login(self):
        """ do_login """
        if self.url == None or self.user == None or self.pwd == None:
            self.logger.error("url or user or u_pwd can not None")
            return None
        if self.zapi is not None:
            return self.zapi
        try:
            zapi = ZabbixAPI(self.url)
            zapi.session.verify = False
            zapi.session.auth = (self.user, self.pwd)
            zapi.login(self.user, self.pwd)
            #self.cookies["zbx_sessionid"] = str(zapi.auth)
            self.cookies["zbx_session"] = "eyJzZXNzaW9uaWQiOiJjMmM5ZmU0YmVkNDMxNDJhZjBhYmQyZWY1OGJhYmJmMyIsInNlcnZlckNoZWNrUmVzdWx0Ijp0cnVlLCJzZXJ2ZXJDaGVja1RpbWUiOjE2MjI2MzMzMTMsInNpZ24iOiJcL0kyb1hFSHo2dnBmcjNGMnRrSUF6RVduaCttU0ZhbElVam4rd1JtQUlMT0NVUTdUR2pKZGw0OUloTEV4YVhoWHJWdTNqR1lKUGhwZGNXamhOTWZZWEpta2xtWnNQejNWdkhNNjRXd3pxSGdPMDhrM0s4MTBcL1NKakpRbkhwbmVlZFJGUTVEcHBKNkxva1wvWGcrZVlhbEE9PSJ9"
            self.zapi = zapi
            logger.info('zbx api version:%s' % self.zapi.api_version())
            return zapi
        except Exception as e:
            self.logger.error("auth failed:\t%s " % (e))
            return None

    def _is_can_graph(self, itemid=None):
        self.zapi = self._do_login()
        if self.zapi is None:
            self.logger.error("zabbix login fail, self.zapi is None:")
            return False
        if itemid is not None:
            """
            0 - numeric float; 
            1 - character; 
            2 - log; 
            3 - numeric unsigned; 
            4 - text.
            """
            item_info = self.zapi.item.get(
                filter={"itemid": itemid}, output=["value_type"])
            if len(item_info) > 0:
                if item_info[0]["value_type"] in [u'0', u'3']:
                    return True
            else:
                self.logger.error("get itemid fail")
        return False

    def get_graph_in_binary(self, itemid=None):
        """ get_graph """
        if itemid == None:
            self.logger.error("itemid %s is None" % itemid)
            return "ERROR"

        if self._is_can_graph(itemid=itemid) is False or self.zapi is None:
            self.logger.error("itemid %s can't graph" % itemid)
            return "ERROR"

        if len(re.findall('4.0', self.zapi.api_version())) == 1:
            graph_url = "%s/chart.php?from=now-1h&to=now&itemids[]=%s&width=360&height=60" % (
                self.url, itemid)
        else:
            graph_url = "%s/chart.php?period=3600&itemids[]=%s&width=480&height=60" % (
                self.url, itemid)
        try:
            ses = self.zapi.session
            # rq = requests.get(graph_url, cookies=self.cookies,
            #                   timeout=self.timeout, stream=True, verify=False)
            rq = ses.get(graph_url, timeout=self.timeout, cookies=self.cookies, stream=True, verify=False)
            if rq.status_code == 200:
                # 直接返回二进制数据
                return rq.content
            rq.close()
        except Exception as e:
            self.logger.error(e)
            return False

    def download_graph(self, save_path, itemid=None, ):
        """ get_graph """
        save_path = os.path.join(save_path, datetime.datetime.today().strftime('%Y-%m-%d'))
        if not os.path.isdir(save_path):
            os.makedirs(save_path, mode=0755)
        if itemid == None:
            self.logger.error("itemid %s is None" % itemid)
            return False

        if self._is_can_graph(itemid=itemid) is False or self.zapi is None:
            self.logger.error("itemid %s can't graph" % itemid)
            return False

        if len(re.findall('4.0', self.zapi.api_version())) == 1:
            graph_url = "%s/chart.php?from=now-1h&to=now&itemids[]=%s" % (
                self.url, itemid)
        else:
            graph_url = "%s/chart.php?period=3600&itemids[]=%s" % (
                self.url, itemid)
        self.logger.info('graph_url: %s' % graph_url)
        try:
            ses = self.zapi.session
            # rq = requests.get(graph_url, cookies=self.cookies,
            #                   timeout=self.timeout, stream=True, verify=False)
            rq = ses.get(graph_url, timeout=self.timeout, cookies=self.cookies, stream=True, verify=False)
            if rq.status_code == 200 or rq.status_code == 500:
                imgpath = os.path.join(save_path,
                                       '%s-%s.png' % (itemid, hashlib.md5(str(time.time()) + itemid).hexdigest()))
                with open(imgpath, 'wb') as f:
                    for chunk in rq.iter_content(1024):
                        f.write(chunk)
                return imgpath
            else:
                self.logger.error('failed to download graph, graph_url: %s return content: %s' % (graph_url, rq.content))
                rq.status_code
            rq.close()
        except Exception as e:
            self.logger.error(e)
            return False

def get_token(app_id, app_secret):
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/'
    body = {"app_id": app_id, "app_secret": app_secret}
    if os.path.isfile(TokenCacheFile):
        with open(TokenCacheFile, 'r') as f:
            d = json.loads(f.read())
            gen_ts = d['gen_ts']
        # 过期时间是7200s
        if time.time() - gen_ts < 7000:
            return d['tenant_access_token']
    resp = requests.post(url, data=body)
    data = resp.json()
    try:
        ret = data['tenant_access_token']
        with open(TokenCacheFile, 'w') as f:
            f.write(json.dumps({'tenant_access_token': ret, 'gen_ts': time.time()}))
        return ret
    except:
        raise Exception("Call Api Error, errorCode is %s" % data["code"])


def upload_image(image_path, tenant_access_token):
    """
    :param image_path:
    :param tenant_access_token:
    :return:
    """
    with open(image_path, 'rb') as f:
        image = f.read()
    resp = requests.post(
        url='https://open.feishu.cn/open-apis/image/v4/put/',
        headers={'Authorization': "Bearer %s" % tenant_access_token},
        files={
            "image": image
        },
        data={
            "image_type": "message"
        },
        stream=True)

    resp.raise_for_status()
    content = resp.json()
    print(content)
    if content.get("code") == 0:
        return content['data']['image_key']
    else:
        raise Exception("Call Api Error, errorCode is %s" % content["code"])


def _main():
    send_to = sys.argv[1]
    event = sys.argv[2]
    alert_message = sys.argv[3]
    #send_to = ''
    #event = 'cpu使用率超过99%'
    #alert_message = """level::average;host::XX-01 ;ip_addr::192.168.1.1;failed_time::11:20:10 ;item_id::39169;host_id::10385"""
    #alert_message = """level::average;host::XX-01 ;ip_addr::192.168.1.1;recovery_time::11:20:10;duration::21m;item_id::39169;host_id::10385"""

    """zbx传入alert_message格式:
        故障message：level::{TRIGGER.SEVERITY};host::{HOSTNAME1} ;ip_addr::{HOST.CONN};failed_time::{EVENT.TIME} ;item_id::{ITEM.ID};host_id::{HOST.ID}
        恢复message：host::{HOSTNAME1}; ip_addr::{HOST.CONN}; recovery_time::{EVENT.RECOVERY.TIME}; duration::{EVENT.AGE}; item_id::{ITEM.ID};host_id::{HOST.ID}
    """
    # 注意分隔符是 "::"
    alert_map = dict([tuple(tmp.split('::')) for tmp in alert_message.split(';')])
    itemid = alert_map.get('item_id', None)
    zbx = Zabbix_Graph(url=ZabbixUrl, user=ZabbixUser, pwd=ZabbixPass, logger=logger, timeout=3)
    if Debug:
        robot_url = DebugRobotApi
    else:
        robot_url = [
                     #weeget
                     "https://open.feishu.cn/open-apis/bot/v2/hook/d47f634b-32d4-4368-8679-3f6fc3bcf9e0"
                    ]
    pic_path = zbx.download_graph(save_path=ZabbixPicPath, itemid=itemid)
    tenant_access_token = get_token(app_id=AppId, app_secret=AppSecret)
    if not pic_path:
        logger.error('zbx download error')
	raise(Exception('zbx download error'))
    image_key = upload_image(pic_path, tenant_access_token)
    req_data_str = make_feishu_req_data(zbx_url=ZabbixUrl, event=event, alert_map=alert_map,
                                        zbx_image_key=image_key)
    for bot in robot_url:
      req = requests.post(url=bot, data=req_data_str, headers={'Content-Type': 'application/json'})
    res = req.json()
    if 'StatusCode' in res.keys() and res['StatusCode'] == 0:
        logger.info("sendto: %s||title:%s||content:%s" % (send_to, event, alert_map))
    else:
        logger.error('api error:%s' % req.content)


_main()
