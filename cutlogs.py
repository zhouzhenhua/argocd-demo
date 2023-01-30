#!/usr/bin/env python
# coding:utf-8
# 判断文件是否是文件夹或文件需要绝对路径

import os,tarfile,time,datetime,requests

# 定义压缩日志的日期名
log_time=time.strftime("%Y%m%d",time.localtime())
print log_time
# 定期清理日志文件时间
expired = 180
PID = '/usr/local/openresty/nginx/logs/nginx.pid'
log_dir = r'/data/wwwlogs'
#host_list = []

def Dingding_Send(data):
    headers = {'Content-Type': 'application/json'}
    Api_Url = 'https://oapi.dingtalk.com/robot/send?access_token=xxx'
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

def cleanfile(path,expiredTime):
    for obj in os.listdir(path):
        objpath = os.path.join(path,obj)
        if os.path.isfile(objpath):
            delExpiredfile(objpath,expiredTime)
        elif os.path.isdir(objpath):
            cleanfile(objpath,expiredTime)

def delExpiredfile(filepath,expiredTime):
    expiredsec =  expiredTime * 24 * 3600
    stat_result =  os.stat(filepath)
    ctime =  stat_result.st_mtime
    ntime = time.time()
    if (ntime-ctime)>expiredsec:
        try:
            os.remove(filepath)
        except Exception as e:
            print e
    else:
        return False

# 压缩日志文件
def compress_logfile ():
    for dir in os.listdir(log_dir):
        top_level_site_dir = os.path.join(log_dir, dir)
        for list in os.listdir(top_level_site_dir):
            if os.path.isdir(os.path.join(top_level_site_dir, list)):
                continue
            # 多台nginx使用nfs公用日志文件，因此存在nfs的因此文件
            if '.nfs' in os.path.join(top_level_site_dir,list):
                continue
            try:
                second_level_site_name = list.split('_')[1].split('.log')[0]
            except Exception as e:
                Dingding_Send("slb-nginx %s" % e)	
            second_level_site_dir = os.path.join(top_level_site_dir, second_level_site_name)
            if not os.path.exists(second_level_site_dir):
                os.mkdir(second_level_site_dir)
            try:
                # 定义压缩日志名字
                tarfile_name = r'{0}/{1}-{2}.tar.gz'.format(os.path.join(top_level_site_dir, second_level_site_name), second_level_site_name, log_time)
                print dir,list,tarfile_name
                archive = tarfile.open(tarfile_name,'w:gz')
                # 压缩指定日志
                list_log = os.path.join(os.path.join(top_level_site_dir, list))
                os.chdir(top_level_site_dir)
                archive.add(list)
                archive.debug = 1
                archive.close()
                os.remove(list_log)
                #删除过期文件
                #delExpiredfile(os.path.join(top_level_site_dir, second_level_site_name), expired)
		cleanfile(second_level_site_dir,expired)
            except Exception as e:
		Dingding_Send("slb-nginx %s" % e)

if __name__ == '__main__':
    try:
     compress_logfile()
    except Exception as e:
     print str(e)
    os.system("kill -USR1 `cat %s`" % PID)

