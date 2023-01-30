from aliyun.log import LogClient
# sdk配置
accessKeyId = ''
accessKey = ''
project = 'logbackup'

# accessKeyId = ''
# accessKey = ''
# project = ''

endpoint = 'cn-shenzhen.log.aliyuncs.com'

# # # # # # # # #
client = LogClient(endpoint, accessKeyId, accessKey)     #创建LogClient
res = client.list_logstore(project_name=project)
# 获取到所有logstore
data = res.get_body()['logstores']
print(data)
# # # # # # # # #
# 投递规则
config = {
  "shipperName": "shipper-test",
  "targetConfiguration": {
    "bufferInterval": 600,
    "bufferSize": 256,
    "compressType": "snappy",
    "enable": True,
    "ossBucket": "prod-weeget",
    "ossPrefix": "testfix",
    "pathFormat": "%Y/%m/%d/%H/%M",
    "roleArn": "acs:ram::1942906690265594:role/aliyunlogdefaultrole",
    "storage": {
      "detail": {
        "columns": [
        ]
      },
      "format": "json"
    }
  },
  "targetType": "oss"
}
# # # # # # # # #
# 迭代所有日志库,更新投递oss规则
# for logstore in data:
#     #print ('helllo,{0}'.format(logstore))
#
#     res = client.update_shipper(project=project, logstore=logstore, detail=config)
# # # # # # # # # #
#
# for logstore in data:
#     config['targetConfiguration']['ossPrefix'] = logstore
#     res = client.update_shipper(project=project, logstore=logstore, detail=config)


#res = client.create_shipper(project=project, logstore='rocky-logstoge', detail=config)
# # # # # # # # #
