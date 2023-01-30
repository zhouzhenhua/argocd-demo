#!/usr/bin/env python
# coding:utf-8
'''
https://azure-storage.readthedocs.io/en/latest/index.html
https://www.azure.cn/documentation/articles/python-how-to-install/
https://docs.azure.cn/zh-cn/storage/storage-python-how-to-use-blob-storage
pip install azure-mgmt-compute
pip install azure-storage
pip install azure-batch
git clone git://github.com/Azure/azure-storage-python.git
cd azure-storage-python
python setup.py install
'''

import ConfigParser
import json
import os
import re
import socket
import tarfile
import time
from datetime import datetime
from datetime import timedelta

import redis
import requests
# 导出普通blob模块
from azure.storage.blob import BlockBlobService
from azure.storage.blob import ContentSettings

# 容器名字
hostname = socket.gethostname()
container = socket.gethostname().replace('.', '-')


def Dingding_Send(data):
    headers = {'Content-Type': 'application/json'}
    Api_Url = 'https://oapi.dingtalk.com/robot/send?access_token=9edd100272358866974b7e543c2afdaf6b7c75a232caa740af6e43f9df3fce20'
    send_data = {
        "msgtype": "text",
        "at": {
            "isAtAll": 'true',
        },
        "text": {
            "content": data
        },
    }
    try:
        print requests.post(url=Api_Url, headers=headers, data=json.dumps(send_data)).text
    except Exception,e:
        print e


class Azure_blob_Service(object):
    def __init__(self):
        self._log_account_name = blob_log_account_name
        self._log_account_key = blob_log_account_key
        self._endpoint_suffix = 'core.chinacloudapi.cn'
        self._block_blob_service = BlockBlobService(account_name=self._log_account_name, account_key=self._log_account_key,
                                                    endpoint_suffix=self._endpoint_suffix)

    ##新增容器
    def create_container(self, str):
        self._block_blob_service.create_container(str)

    def check_blob(self, container, log_dir):
        generator = self._block_blob_service.list_blobs(container)
        for blob in generator:
            if blob.name == log_dir:
                return True

    # 上传blob到普通型容器中
    def upload_blob(selt, container, blob, file_name, file_tpye):
        selt._block_blob_service.create_blob_from_path(container, blob, file_name,
                                                       content_settings=ContentSettings(content_type=file_tpye))

    def delete_blob(self, contaniner, blob):
        self._block_blob_service.delete_blob(contaniner, blob)

    def download_blob(self,mycontainer,remote_path,local_path):
        self._block_blob_service.get_blob_to_path(mycontainer,remote_path,local_path)

def Update_Redis_Data():
    try:
        r = redis.Redis(host=redis_ip, port=redis_port, db=redis_db, password=redis_password)
        new_blob_log_account_name = r.get('log_account_name')
        new_blob_log_account_key = r.get('log_account_key')
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        config.remove_option("Account_conf", "log_account_name")
        config.remove_option("Account_conf", "log_account_key")
        config.set('Account_conf', 'log_account_name', new_blob_log_account_name)
        config.set('Account_conf', 'log_account_key', new_blob_log_account_key)
        #--set global
        global blob_log_account_name
        global blob_log_account_key
        blob_log_account_name = config.get("Account_conf", "log_account_name")
        blob_log_account_key = config.get("Account_conf", "log_account_key")
        with open(config_file, 'w+') as f:
            config.write(f)
    except Exception, e:
        Dingding_Send(hostname + str(e))

def upload_logfile(container, Log_Dir_List, Log_File_Type, expire_day_interval=90):
    # 时间格式
    Dtime = time.strftime("%Y/%m", time.localtime())
    for Log_Dir in Log_Dir_List:
        os.chdir(Log_Dir)
        for i in os.listdir(Log_Dir):
            if os.path.isfile(i):
                if len(i.split('.')) != 2 and re.findall("[0-9]", i):
                    # file_name = i.split('.')[0]
                    file_name = ('.'.join(i.split('.')[0:-1]))
                    archive = tarfile.open('{0}.tar.gz'.format(file_name), 'w:gz')
                    archive.add(i)
                    archive.close()
                    blob = Dtime + Log_Dir + '/' + file_name + '.tar.gz'
                    # 上传文件
                    try:
                        Azure_blob_Service().upload_blob(container, blob, os.path.abspath(file_name + '.tar.gz'),Log_File_Type)
                        os.remove(i)
                    except Exception as e:
                        Dingding_Send(hostname + ': ' + blob + ': ' + '上传失败' + e)
                    finally:
                        os.remove(file_name + '.tar.gz')

def delete_logfile():
    # 定义过期文件日期
    now = datetime.now()
    aday = timedelta(days=-int(expire_day_interval))
    expire_day = now + aday
    expire_day_format = expire_day.strftime('%Y/%m')
    #如果Tomcat_Dir_List列表为空，则不进行删除操作
    if Tomcat_Dir_List:
        exit(1)
    now = datetime.now()
    aday = timedelta(days=-1)
    yesterday = now + aday
    for tomcatdir in Tomcat_Dir_List:
        os.chdir(tomcatdir)
        if 'logs' not  in tomcatdir:
            exit(1)
        try:
            os.system(
                "cd {0} &&  echo ' ' > catalina.out".format(tomcatdir))
        except Exception, e:
            Dingding_Send(hostname + ': ' + tomcatdir + ': ' + '删除失败')
        try:
            os.system("cd {0} && find {0} -mtime +1 -type f |xargs rm -f".format(tomcatdir))
        except Exception, e:
            Dingding_Send(hostname + ': ' + tomcatdir + ': ' + '删除失败')


def init_log_dir(log_center):
    path = []
    log_dir_list = []
    log_dir_list.append(log_center)
    for i in os.listdir(log_center):
        path_dir = os.path.join(log_center, i)
        if os.path.isdir(path_dir):
            path.append(path_dir)
    for dir in path:
        for root,dirs,files in os.walk(dir):
            log_dir_list.append(root)

    config = ConfigParser.ConfigParser()
    config.read(config_file)
    config.remove_option("Log_dir", "log_dir_list")
    config.set('Log_dir', 'log_dir_list', re.sub(r'\[|\]|\'',"",str(list(set(log_dir_list)))))
    with open(config_file, 'w+') as f:
        config.write(f)


if __name__ == '__main__':
    try:
        log_center = '/data/log-center'
        config_file = os.path.dirname(os.path.abspath(__file__)) + '/blob.ini'
        init_log_dir(log_center)
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        blob_log_account_name = config.get('Account_conf', 'log_account_name')
        blob_log_account_key = config.get('Account_conf', 'log_account_key')
        redis_ip = config.get('Redis_conf', 'ip')
        redis_db = config.get('Redis_conf', 'db')
        redis_password = config.get('Redis_conf', 'password')
        redis_port = config.get('Redis_conf', 'port')
        Log_Dir_List = config.get('Log_dir', 'log_dir_list').replace(' ','').split(',')
        # Tomcat路径
        try:
            Tomcat_Dir_List = config.get('Log_dir', 'tomcat_dir_list').split(',')
        except Exception,e:
            Tomcat_Dir_List = []
        Log_File_Type = "application/x-compressed-tar"
        expire_day_interval = config.get('day', 'expire_day_interval')
        try:
            Azure_blob_Service().create_container(container)
        except Exception, e:
            Update_Redis_Data()
        #---上传日志文件及删除tomcat日志
        upload_logfile(container, Log_Dir_List, Log_File_Type, expire_day_interval)
        #delete_logfile()
    except Exception, e:
        Dingding_Send(hostname + ': ' + str(e))
