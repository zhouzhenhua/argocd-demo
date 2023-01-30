#!coding:utf-8
#!/usr/bin/env python
import io, sys

# sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
# sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

from flask import Flask, jsonify, make_response, Response
from flask import request
import urllib2
import logging
import json
import datetime
from copy import deepcopy
from collections import OrderedDict
from dateutil.parser import parse
import locale
#locale.setlocale(locale.LC_ALL,"en_US.UTF-8")

app = Flask(__name__)

console = logging.StreamHandler()
# logfile = logging.FileHandler('%s.log' % 'webhook_dingtalk')
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
formatter = logging.Formatter(fmt)
console.setFormatter(formatter)
# logfile.setFormatter(formatter)
log = logging.getLogger("flask_webhook_dingtalk")
log.addHandler(console)
# log.addHandler(logfile)
log.setLevel(logging.DEBUG)

EXCLUDE_LIST = ['prometheus', 'endpoint']

@app.route('/dingtalk/send/',methods=['POST'])
def hander_session():
    post_data = json.loads(request.get_data().decode("utf-8"))
    markdown_str = fillup_markdown_str(post_data)
    respon = SendToDingTalk(markdown_str)
    # respon = {'code':0}
    # log.info(json.dumps(markdown_str, indent=2))
    log.info("DingTalk Respon: "+respon)
    res = jsonify(respon)
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res

@app.route('/',methods=['GET', 'POST'])
def index():
    log.info(dict(request.headers))
    log.info('get data:' + request.get_data())
    log.info(dict(request.data))
    # res = Response(status=302)
    res = jsonify({'code': 0})

    res.headers['CUSTOM-HEADER'] = 'shiyan'
    return res

def fillup_markdown_str(data):
    alert_name = data['commonLabels']['alertname']
    prome_job = data['commonLabels']['job']
    alert_list = data['alerts']
    str_list = []
    # markdown添加alertname总标题
    str_list.append(u"### 告警项目:%s" % alert_name)
    for alert in alert_list:
        annotation_dict = OrderedDict(deepcopy(alert['annotations']))
        annotation_status = alert['status']
        try:
            title = annotation_dict.pop('title')
        except:
            title = ''
        # markdown添加小标题
        if annotation_status.upper() == 'FIRING':
            str_list.append(u"**FIRING**:<font color=#ff0000>%s</font>" % title)
        else:
            str_list.append(u"**RESOLVED**:<font color=#00ff00>%s</font>" % title)
        start_at_str = parse(alert['startsAt']).strftime('%Y-%m-%d %H:%M:%S')
        annotation_dict.update({u'Trigger time': start_at_str})
        if annotation_status.upper() == "RESOLVED":
            end_at_str = parse(alert['endsAt']).strftime('%Y-%m-%d %H:%M:%S')
            annotation_dict.update({u'Recovery time': end_at_str})
        # 取annotation object的内容组装markdown
        for k, v in annotation_dict.items():
            str_list.append(u"> **%s:** %s" % (k, v))
    # 列表合并为markdown
    markdown_str = '\n\n'.join(str_list) \
                   + "\n###### [Alertmanager](http://172.20.13.245:9093/#/alerts)" \
                   + u' %s推送' % datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    return markdown_str

def SendToDingTalk(markdown_str):
    # 钉钉机器人url
    url = "https://oapi.dingtalk.com/robot/send?access_token=db8138db581aba9f4d13d30f1750e331c1b7cac501818b5af0fe2539554d42cf"
    headers = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    data = {
      "msgtype": "markdown",
        "markdown": {
            "title": "Prometheus报警",
            "text": markdown_str
        },
        "at": {
            "atMobiles": [],
            "isAtAll": False
        }
    }
    request = urllib2.Request(url, data=json.dumps(data), headers=headers)
    respon = urllib2.urlopen(request).read()
    return respon

if __name__ == '__main__':
    app.debug = False
    app.run(host='0.0.0.0', port=8080)