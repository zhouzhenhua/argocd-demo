# --coding:utf8--
#!/usr/bin/env python
import json
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkdyvmsapi.request.v20170525.SingleCallByTtsRequest import SingleCallByTtsRequest
from aliyunsdkdyvmsapi.request.v20170525.QueryCallDetailByCallIdRequest import QueryCallDetailByCallIdRequest
import logging

logger = logging.getLogger('gunicorn.glogging.Logger')


class CallPhone(object):
    def __init__(self,ak,sk,tts_code,called_show_number,zone='cn-hangzhou',):
        self.client = AcsClient(ak,sk,zone)
        self.ttsRequest = SingleCallByTtsRequest()
        # 申请的语音通知tts模板编码,必填
        self.ttsRequest.set_TtsCode(tts_code)
        # 语音通知显示号码，必填
        self.ttsRequest.set_CalledShowNumber(called_show_number)
        # 设置播放次数
        self.ttsRequest.set_PlayTimes(2)

    def call_phone(self, call_phone, monitor_phone, tts_param):
        # tts模板变量参数
        phone_type = {
            1: call_phone,
            2: monitor_phone
        }

        querydate = str(int(time.time()) * 1000)
        self.ttsRequest.set_TtsParam(json.dumps(tts_param))
        result = []
        for type in phone_type:
            for phone in phone_type.get(type):
                # 语音通知的被叫号码，必填
                self.ttsRequest.set_CalledNumber(phone['mobile'])
                logger.info('开始拨打电话')
                Response = self.client.do_action_with_exception(self.ttsRequest)
                Response = json.loads(Response)
                if Response.get('Code') != 'OK':
                     RuntimeError('呼叫失败:%s'%Response)

                time.sleep(60)
                ret,call_detail = self.get_call_detail(Response.get('CallId'),querydate)
                call_detail = json.loads(call_detail.get('Data'))
                if call_detail.get('state') in ["200005", "200004", "200011", "200010", "200002", "200005", "200003"]:
                    logger.info("%s[%s] 未接听：%s"%(phone['name'],phone['mobile'],call_detail))
                    continue
                else:
                    result.append("%s[%s] 接听电话：%s"%(phone['name'],phone['mobile'],call_detail.get('stateDesc')))
                    break

    def get_call_detail(self, callid, querydate, prodid='11000000300006'):
        query_call = QueryCallDetailByCallIdRequest()
        query_call.set_accept_format('json')
        query_call.set_ProdId(prodid)
        query_call.set_CallId(callid)
        query_call.set_QueryDate(querydate)
        Response = self.client.do_action_with_exception(query_call)
        Response = json.loads(Response)
        if Response.get('Code') != 'OK':
            return False, Response

        return True, Response
