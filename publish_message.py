#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019-4-15
# @Author  : zhouzh
# @File    : jira.py
# @Software: PyCharm

from jira import JIRA
import requests
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import commands
import argparse
import datetime
import time

from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
import smtplib


"""
pip install jira
"""

class JiraAPI(object):

     def __init__(self):
         self.jiraServer = 'http://jira.scm.ppmoney.com'
         self.jiraUsername = 'shrl_robot'
         self.jiraPassword = 'pX5qR5Wf2019'
         self.myissue = None
         self.JIRA_Creator = None
         self.JIRA_Reviewer = None
         self.JIRA_Worker = None
         self.JIRA_Kind = None
         self.JIRA_Project = None
         self.JIRA_Project_Version = None
         self.JIRA_Content = None
         self.JIRA_Notice = None
         self.JIRA_Status = None
         self.JIRA_Adreess = None

     def login_jira(self):

         myjira = JIRA(self.jiraServer,basic_auth=(self.jiraUsername,self.jiraPassword))

         #self.myissue = myjira.issue('JDYW-3423')
         #self.myissue = myjira.issue(sys.argv[1])
         self.myissue = myjira.issue(projectid)


     def getIssue(self):

         #报告人
         self.JIRA_Creator = self.myissue.fields.creator.displayName
         #经办人
         self.JIRA_Reviewer = self.myissue.fields.customfield_10424[0].displayName
         #工作人
         self.JIRA_Worker = self.myissue.fields.customfield_10400[0].displayName
         #更新类型
         self.JIRA_Kind = self.myissue.fields.customfield_10109.value
         #更新项目
         self.JIRA_Project = self.myissue.fields.customfield_12101.value
         #版本号
         self.JIRA_Project_Version = self.myissue.fields.customfield_11104
         #更新主题
         self.JIRA_Content = self.myissue.fields.summary
         #更新状态
         self.JIRA_Status = self.myissue.fields.status.name
         #本次更新公告
         self.JIRA_Notice = self.myissue.fields.customfield_10119
         #工单地址
         #self.JIRA_Adreess =  self.jiraServer + "/browse/" + (sys.argv[1])
         #self.JIRA_Adreess = self.jiraServer + "/browse/" + "JDYW-3423"
         self.JIRA_Adreess = self.jiraServer + "/browse/" + (projectid)

         print "报告人:" + (self.JIRA_Creator)
         print "经办人:" + (self.JIRA_Reviewer)
         print "工作人:" + (self.JIRA_Worker)
         print "更新类型:" + (self.JIRA_Kind)
         print "更新项目:" + (self.JIRA_Project)
         print "版本号:" + (self.JIRA_Project_Version)
         print "更新主题:" + (self.JIRA_Content)
         print "更新状态:" + (self.JIRA_Status)
         print "本次更新公告:" + (self.JIRA_Notice)
         print "工单地址：" + (self.JIRA_Adreess)
         #return self.JIRA_Project_Version


def jira_pre_file(projectid):
    #a = 'lvs'  # --------------------要查询的字符串
    with open('/tmp/pre_file.txt', 'a+') as foo:
        for line in foo.readlines():
            if projectid in line:
                print '单号存在，不可重复推送发布记录'
                sys.exit()

    print '单号不存在，可推送发布记录'
    fo = open('/tmp/pre_file.txt', 'a+')
    fo.write(projectid+"\n")
    fo.close()

def jira_fin_file(projectStatus):
    #a = 'lvs'  # --------------------要查询的字符串
    with open('/tmp/fin_file.txt', 'a+') as foo:
        for line in foo.readlines():
            if projectid in line:
                print '单号存在，不可重复推送发布记录'
                sys.exit()

    print '单号不存在，可推送发布记录'
    fo = open('/tmp/fin_file.txt', 'a+')
    fo.write(projectid+"\n")
    fo.close()


def Dingding_Send(JIRA_Reviewer,JIRA_Project,JIRA_Project_Version,JIRA_Kind,JIRA_Content,JIRA_Adreess,projectid,projectStatus,projectuser,build_fin_time):
    headers = {'Content-Type': 'application/json'}
    #dingtalk_token = ["https://oapi.dingtalk.com/robot/send?access_token=fc682db6254100f462d1e1a5bc7d48878627296608dc57255f34600345cbae0b"]
    dingtalk_token = [
        #上线发布群
        "https://oapi.dingtalk.com/robot/send?access_token=4fe53bb5fb85ed4102be564bfa72b9bd51d10894377d04ac45f4be27430cc4b5",
        #JD-boss
        "https://oapi.dingtalk.com/robot/send?access_token=608b5f9d7a0e5c3929ee83607e706427d0368f0a4f46f9bb260786e17ccc4fb1"
    ]
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "发布通知",
            "text":  "@{0} \n".format(JIRA_Reviewer)+ '\n'
                     "运维 :  {0} \n".format(projectuser)+ '\n'                                      
                     "项目 :  {0} \n".format(JIRA_Project)+ '\n'
                     "类型 :  {0} \n".format(JIRA_Kind)+ '\n'
                     "版本 :  {0} \n".format(JIRA_Project_Version)+ '\n'
                     "内容 :  {0} \n".format(JIRA_Content)+ '\n'                                          
                     "详情 :  [{0}]({1}) \n".format(projectid,JIRA_Adreess)+ '\n'
                     "状态 :  {0} ({1}min)\n".format(projectStatus,build_fin_time)

        },
        "at": {
            "isAtAll": 'True'
    }
    }
    for Api_Url in dingtalk_token:
        print(requests.post(url=Api_Url, headers=headers, data=json.dumps(data)).text)


def SendMail(JIRA_Content,JIRA_Notice):
    #发送邮箱服务器
    smtpserver = "smtp.exmail.qq.com"
    #发送邮箱用户名密码
    user = "jiedai_noc@ppmoney.com"
    password = "ZOjEx=3a5T4FR250"

    sender = "jiedai_noc@ppmoney.com"
    receivers = ["all-it@ppmoney.com"]
    mail_realname = "借贷运维组"

    subject = JIRA_Content
    content = JIRA_Notice


    # 创建一个带附件的实例
    #msg = MIMEMultipart()
    #msg.attach(MIMEText(content, 'html', 'utf-8'))
    msg = MIMEText(content, "plain", 'utf-8')  #处理换行BUG

    # 加邮件头
    msg['to'] = ";".join(receivers)
   #msg['from'] = sender
    msg['from'] = '%s<%s>' % (mail_realname, sender)
    msg['subject'] = Header(subject, 'utf-8')

    # 发送邮件
    try:
        server = smtplib.SMTP()
        server.connect(smtpserver)
        server.login(user, password)  # XXX为用户名，XXXXX为密码
       #server.sendmail(msg['from'], msg['to'],msg.as_string())
        server.sendmail(sender, receivers, msg.as_string())
        server.quit()
        print '发送成功'
    except Exception, e:
        print str(e)

if __name__ == '__main__':

     parser = argparse.ArgumentParser()
     parser.add_argument('-n', '--num', type=str, help='display jira project id')
     parser.add_argument('-s', '--status', type=str, help='display jira project deploy status')
     parser.add_argument('-u', '--ops', type=str, help='display jira project build user')
     args = parser.parse_args()
     #print(args.num)
     projectid = (args.num)
     projectStatus = (args.status)
     projectuser = (args.ops)

     jira_obj = JiraAPI()
     jira_obj.login_jira()
     jira_obj.getIssue()

     if projectStatus == "准备上线":
        jira_pre_file(projectid)
        os.system("/bin/touch /tmp/%s" % (projectid))
     elif projectStatus == "完成上线":
        jira_fin_file(projectid)
     else:
        print "验证上线状态"
        sys.exit()

     #starttime = datetime.datetime.now()
     #time.sleep(70)
     #endtime = datetime.datetime.now()

     if projectStatus == "完成上线":
         #build_fin_time = ((endtime - starttime).seconds // 60 + 1)
         #retcode, ret = commands.getstatusoutput('echo "`date +%s` - `stat -c %Y /tmp/projectid`" |bc')
         retcode, ret = commands.getstatusoutput('echo "`date +%s` - `stat -c %Y /tmp/{0}`" |bc' .format(projectid))

         timeoffset = int(ret)
         #print type(timeoffset)
         #print timeoffset
         build_fin_time = timeoffset / 60
         print build_fin_time
         os.system("/bin/rm -f /tmp/%s" % (projectid))
     else:
         build_fin_time = None
         pass

     Dingding_Send(jira_obj.JIRA_Reviewer,jira_obj.JIRA_Project,jira_obj.JIRA_Project_Version,jira_obj.JIRA_Kind,jira_obj.JIRA_Content,jira_obj.JIRA_Adreess,projectid,projectStatus,projectuser,build_fin_time)
     SendMail(jira_obj.JIRA_Content,jira_obj.JIRA_Notice)
