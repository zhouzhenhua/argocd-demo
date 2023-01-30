 #!/usr/bin/python
# -*- coding: utf-8 -*-
 
import json
import os
from flask import request, Flask    #flask模块
from dingtalkchatbot.chatbot import DingtalkChatbot     #钉钉发送群消息模块
 
#将数据写入到文件中
def Open(s):
    Path = './temp.json'
    #判断文件是否存在
    if os.path.exists(Path):
        os.remove(Path)     #先删除文件
    #文件不存在时，将数据写入到文件中
    f = open(Path, 'w')
    print(s, file = f)
    f.close()
 
#接收数据
def GetData():
    PostData = request.get_data()  # 获取jira POST请求的原始数据
    Data = json.loads(PostData)  # 将json格式的数据转换为字典
    JsonData = json.dumps(Data, ensure_ascii=False, indent=4)   #格式化json数据
    return Data
#Open函数和GetData函数用作获取数据，对数据进行分析使用
 
#Flask通用配置
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
 
 
@app.route('/webhook/test/', methods=['POST'])
def IssueCreate():
    # Open(GetData())
    description = GetData()['commonAnnotations']['description']
    status = GetData()['status']
    serverity = GetData()['alerts'][0]['labels']['severity']
    job = GetData()['alerts'][0]['labels']['job']
    instance = GetData()['alerts'][0]['labels']['instance']
    start_time = GetData()['alerts'][0]['startsAt']
    message = str('##' + 'Prometheus告警：%s' %description + '##' + '\n'
                '状态：%s' %status + '\n'
                '告警级别：%s' %serverity + '\n'
                '分组名称：%s' %job + '\n'
                'IP地址：%s' %instance + '\n'
                '开始时间：%s' %start_time + '\n'
    )
    print(message)
    send_message(message)
    return "OK", 200
 
def send_message(message):
    webhook = '{钉钉机器人URL地址}'
    xiaoding = DingtalkChatbot(webhook)
    xiaoding.send_text(msg=message, is_at_all=True)     #is_at_all参数为True表示@所有人
 
if __name__ == '__main__':
    app.run(debug = False, host = '{脚本所在服务器的IP地址}', port = 8888)
