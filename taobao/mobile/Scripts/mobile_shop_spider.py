#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
File Name : 'shop_spider'.py 
Description:
Author: 'zhengyang' 
Date: '2016/10/25' '11:25'
"""
import datetime
import json
import os
import random
import sys
import time
import threading
import functools
import datetime
import traceback
import hashlib
try:
    import cPickle as pickle
except ImportError:
    import pickle

import jsonpath_rw_ext
import requests
from dateutil.relativedelta import relativedelta

import ConfigParser
import codecs
import platform
import utils
import comm_log
from models import Sms, Call, Basic, Bill, PackageUsage, Recharge, PackageItem, Status
from settings import headers, RETRY_TIMES, DELAY_TIME, DETAIL_FAIL_INFO
from mongodb_connect import connect_mongodb, get_last_scape_dt
from redis_connect import redis_hget_meta, redis_expire_meta, redis_hset_meta, redis_insert_set
import sendmail
reload(sys)
sys.setdefaultencoding("utf-8")


def retry(value_to_check, tries=RETRY_TIMES, delay=DELAY_TIME):
    """重试调用一个函数
    :param value_to_check: 需要重试的返回值
    :param tries: 重试次数 [int]
    :param delay: 重试间隔时间(秒) [float]
    """
    def _deco(func):
        @functools.wraps(func)
        def _func(self, *args, **kwargs):
            m_tires, m_delay = tries, delay
            while m_tires > 1:
                value = func(self, *args, **kwargs)
                # 函数返回值本身就是bool类型 True和False
                if isinstance(value, bool) and value == value_to_check:
                    self.logger.info(u"重试{}秒...".format(m_delay))
                    time.sleep(m_delay)
                    m_tires -= 1
                # 函数返回值由bool类型和一个状态码组成的tuple
                # 如(True, "0001") 和(False, "1001")
                elif isinstance(value, tuple) and value[0] == value_to_check:
                    self.logger.info(u"重试{}秒...".format(m_delay))
                    time.sleep(m_delay)
                    m_tires -= 1
                else:
                    return value
            return func(self, *args, **kwargs)
        return _func
    return _deco


def log(logging_info):
    """在函数开始和结束打日志, 并记录函数的执行时间，写入结束时的日志
    :param logging_info 打印的日志"""
    def _deco(func):
        @functools.wraps(func)
        def _func(self, *args, **kwargs):
            self.logger.info(u"{0:*^100}".format(u"{}开始".format(logging_info)))
            start_time = time.time()
            value = func(self, *args, **kwargs)
            end_time = time.time()
            # logging_info_end = u"{}结束:用时:{:0.2f}".format(logging_info, end_time - start_time)
            self.logger.info(u"{0:*^100}".format(u"{}结束:用时:{:0.2f}".format(logging_info, end_time - start_time)))
            return value
        return _func
    return _deco


class MobileShopSpider(object):
    def __init__(self, task_id, phone, password=None, proc_num=0, step="Login"):

        self.phone = phone
        self.task_id = task_id
        self.proc_num = proc_num
        self.step = step

        # 日志
        # self.logger = comm_log.comm_log(self.proc_num, "")
        self.logger = comm_log.init_log(self.phone)

        # 上次该phone的爬取时间
        # 获得该电话号码上次的爬取时间
        # 返回样例 (u'2016-11-29 11:52:55', u'2016-11', u'201611', u'2016-11-29 00:00:00')
        # (self.last_scape_dt, self.last_scape_month_str, self.last_scape_month, self.last_scape_dt_0) = \
        #     get_last_scape_dt(self.phone)
        (self.last_scape_dt, self.last_scape_month_str, self.last_scape_month, self.last_scape_dt_0) = None, None, None, None

        # 证书
        self.cacert = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cacert.pem")

        # 今天零点字符串表示 '2016-11-29 00:00:00'
        self.today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")

        # meta信息 包含session和password
        # meta = redis_hget_meta(self.task_id)

        if self.step == "Login":
            self.s = requests.session()
            self.s.verify = self.cacert
            self.logger.info(u"Login 重新生成session")
        else:
            meta_json = json.loads(self.session)
            self.s = pickle.loads(meta_json.get("session").encode("utf-8"))
            self.password = meta_json.get("password")
            self.logger.info(u"从redis中读取meta")

        # 密码
        if password is not None:
            self.password = password

        # 详单类型
        self.bill_type_mapping = {u"通话详单": "02", u"短信/彩信详单": "03"}

        # 超时时间
        self.REQUEST_TIMEOUT = 60
        # 两次发短信的时间间隔 需大于60秒 否则第二条短信收不到
        self.SMS_INTERVAL = 65

        # 数据库连接
        # self.mongodb_conn = connect_mongodb()

        self.to_who = ['mime-spider@mi-me.com']
        self.subject = 'CMCC WEB: {} {}'.format(self.step, self.task_id)

    def init_log(self, phone_number, conf = 'db.conf'):
        #读取日志的路径
        cur_script_dir = os.path.split(os.path.realpath(__file__))[0]
        cfg_path = os.path.join(cur_script_dir, conf)
        cfg_reder = ConfigParser.ConfigParser()
        cfg_reder.readfp(codecs.open(cfg_path, "r", "utf_8"))

        today = datetime.date.today().strftime('%Y%m%d')

        self._SECNAME = "LOGPATH"
        if platform.platform().find("windows") != -1 or platform.platform().find("Windows") != -1:
            self._OPTNAME = "WINDOWS_LOGDIR"
        else:
            self._OPTNAME = "LINUX_LOGDIR"
        self._LOGROOT = cfg_reder.get(self._SECNAME, self._OPTNAME)

        #创建日志文件的路径
        log_path = os.path.join(self._LOGROOT, today)
        if not os.path.isdir(log_path):
            os.makedirs(log_path)

        self.logger = comm_log(phone_number, logpath=log_path)

        self.imgroot = os.path.join(self._LOGROOT, 'img')
        # 如果目录不存在，则创建一个目录
        if not os.path.isdir(self.imgroot):
            os.makedirs(self.imgroot)

        return self.logger

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 关闭mongodb连接
        # self.mongodb_conn.close()

        # 发送邮件
        # if exc_type is not None:
        #     self.logger.critical("{}-{}".format(self.task_id, self.phone))
        #     self.logger.critical(exc_type)
        #     self.logger.critical(exc_val)
        #     self.logger.critical(''.join(traceback.format_tb(exc_tb)))
        #     sendmail.intf_send_mail(self.to_who, self.subject, ''.join(traceback.format_tb(exc_tb)))
        pass

    def write_session(self):
        """将meta(包含session和password)序列化并写入redis"""
        session = pickle.dumps(self.s)
        meta = dict(session=session, password=self.password)
        self.session = meta
        # redis_hset_meta(self.task_id, json.dumps(meta))
        # redis_expire_meta(self.task_id)
        # self.logger.info(u"将meta写入redis")

    @property
    def month_list(self):
        """本次所需爬取的月份
        :return:"""
        # todo 确定每月1号的情况
        today = datetime.date.today()
        if today.day == 1:
            _month_list = [datetime.date.strftime(today + relativedelta(months=-1), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-2), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-3), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-4), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-5), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-6), '%Y%m')]
        else:
            _month_list = [datetime.date.strftime(today, '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-1), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-2), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-3), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-4), '%Y%m'),
                           datetime.date.strftime(today + relativedelta(months=-5), '%Y%m')]

        return _month_list

    @log(u"登录移动商城")
    @retry(False)
    def login(self):
        """登录移动商城 请求触发登录短信验证码
        :return 网络异常 (False, "1010")
                成功 (True, "0001")
               """

        # 初始登录  从北京移动进入
        url = r"https://login.10086.cn/html/login/login.html" +\
              r"?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1"

        try:
            self.s.get(url, headers=headers["login"], verify=self.cacert, timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            self.logger.info(u"移动服务异常，初始登录失败 :{}".format(e.args[0]))
            return False, "1010"
        else:
            self.logger.info(u"初始登录成功")

        # 请求一个图片页
        url = r"https://login.10086.cn/captchazh.htm?type=12"

        try:
            self.s.get(url, headers=headers["login_captchazh"], timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            # 类似这些步骤只是模仿浏览器的，所以即使发生异常了也不return，在最终结果处return
            self.logger.info(u"请求一个图片页失败:{}".format(e.args[0]))

        # 请求checkUidAvailable页面
        url = r"https://login.10086.cn/checkUidAvailable.action"

        try:
            self.s.post(url, headers=headers["login_send"], timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            self.logger.info(u"请求checkUidAvailable页面失败:{}".format(e.args[0]))

        # 请求needVerifyCode页面 check_num为请求次数
        check_num = 1
        for _ in range(check_num):
            url = "".join([r"https://login.10086.cn/needVerifyCode.htm",
                           r"?accountType=01",
                           r"&account={}".format(self.phone),
                           r"&timestamp={:13.0f}".format(time.time() * 1000)])

            try:
                self.s.get(url, headers=headers["login_need_verify"], timeout=self.REQUEST_TIMEOUT)
            except requests.RequestException as e:
                self.logger.info(u"请求needVerifyCode页面失败:{}".format(e.args[0]))

            time.sleep(random.random())

        # 校验电话号码 # 成功的返回样例 u'true'
        url = r"https://login.10086.cn/chkNumberAction.action"
        payload = {"userName": self.phone}

        try:
            r = self.s.post(url, headers=headers["login_send"], data=payload, timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            self.logger.info(u"校验电话号码失败:{}".format(e.args[0]))

        # 向移动商城请求短信验证码
        url = r"https://login.10086.cn/sendRandomCodeAction.action"
        payload = {"userName": self.phone,
                   "type": "01",
                   "channelID": "12002"}
        try:
            r = self.s.post(url, headers=headers["login_send"], data=payload, timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            self.logger.info(u"向移动商城请求短信验证码失败:{}".format(e.args[0]))
            return False, "1010"
        else:
            # 成功的返回样例 u'0'
            result = r.text
            if result == "0":
                self.logger.info(u"向移动商城请求短信验证码返回值正确:{}".format(result))
                self.write_session()
                return True, "0001"
            else:
                self.logger.info(u"向移动商城请求短信验证码返回值不正确:{}".format(result))
                return False, "1010"

    @log(u"登录短信验证码校验")
    def get_sms_verifycode(self, sms):
        """登录短信验证码校验 成功后点击发送二次短信验证码
        :param sms 短信验证码
        :return 用户名密码不匹配 (False, "1001")
                登录短信验证码错误 (False, "1003")
                网络异常 or 请求爬取短信验证码失败 (False, "1010")
                请求爬取短信验证码成功 (True, "0003")"""

        # 向移动商城提交短信验证码
        url = r"http://login.10086.cn/login.htm"

        # 抓包是https请求而且有{"protocol": "https:"}参数的，但是带着这个参数发https请求一直超时，
        # 去掉了加了 会301到https页面...
        payload = {"accountType": "01",
                   "account": self.phone,
                   "password": self.password,
                   "pwdType": "01",
                   "smsPwd": sms,
                   "inputCode": "",
                   "backUrl": "http://shop.10086.cn/mall_100_100.html?forcelogin=1",
                   "rememberMe": "0",
                   "channelID": "12002",
                   # "protocol": "https:", #抓包有的且url为https
                   "timestamp": int(time.time() * 1000)}

        try:
            r = self.s.get(url, headers=headers["login_post"], params=payload, timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            self.logger.info(u"向移动商城提交短信验证码失败:{}".format(e.args[0]))
            return False, "1003"
        else:
            result = r.content
            if result.find(u"密码不匹配") > -1:
                self.logger.info(u"用户名和密码不匹配:{}".format(result))
                return False, "1001"
            elif result.find(u"不正确或已过期") > -1:
                self.logger.info(u"登录短信验证码不正确或已过期:{}".format(result))
                return False, "1003"

            try:
                json_data = r.json()
            except Exception as e:
                self.logger.info(u"向移动商城提交短信验证码失败:{}:{}".format(r.content, e.args[0]))
                return False, "1003"
            else:
                artifact = json_data.get("artifact")

            if not artifact:
                self.logger.info(u"向移动商城提交短信验证码返回值artifact未找到:{}".format(r.content))
                return False, "1003"
            else:
                self.logger.info(u"向移动商城提交短信验证码成功artifact:{}".format(artifact))

        self.logger.info(u"点击发送爬取短信验证码开始...")
        # 校验步骤的开始时刻
        start_time = time.time()

        # 重要校验步骤
        url = "".join([r"http://shop.10086.cn/sso/getartifact.php",
                       r"?backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_100_100.html%3Fforcelogin%3D1",
                       r"&artifact={}".format(artifact)])

        try:
            self.s.get(url, headers=headers["login_auth"], timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            self.logger.info(u"登录后校验失败:{}".format(e.args[0]))
            return False, "1003"
        else:
            self.logger.info(u"登录后校验成功")

        # 若成功 开始尝试触发爬取短信验证码
        # 普通校验步骤
        def url_gen():
            """生成一串需要校验的url"""
            yield headers["get_sms_check_0"], r"http://shop.10086.cn/i/?f=billdetailqry"
            yield headers["get_sms_check_1"], r"http://shop.10086.cn/i/v1/auth/loginfo?_={:13.0f}".format(time.time() * 1000)
            yield headers["get_sms_check_2"], r"https://login.10086.cn/SSOCheck.action?channelID=12003&backUrl=http://shop.10086.cn/i/?f=billdetailqry",
            yield headers["get_sms_check_3"], r"http://shop.10086.cn/i/apps/pageapps/pmenu/index.html"

        for i, (headers_value, url) in enumerate(url_gen()):
            try:
                r = self.s.get(url, headers=headers_value)
            except requests.RequestException as e:
                self.logger.info(u"普通校验步骤{}失败:{}".format(i, e.args[0]))
            else:
                self.logger.info(u"test:url:{}:content:{}".format(url, r.content[:150]))

        # 点击详单页
        self.logger.info(u"点击详单页")
        url = r"http://shop.10086.cn/i/apps/serviceapps/billdetail/index.html"
        try:
            self.s.get(url, headers=headers["get_sms_verifycode_1"])
        except requests.RequestException as e:
            self.logger.info(u"无法点击详单页:{}".format(e.args[0]))
        else:
            self.logger.info(u"test:url:{}:content:{}".format(url, r.content[:150]))

        # 获得城市 省份
        self.logger.info(u"获得城市省份设置cookies")
        url = r"http://shop.10086.cn/i/v1/res/numarea/{}?_={:13.0f}".format(self.phone, time.time())
        try:
            r = self.s.get(url, headers=headers["get_sms_verifycode_2"])
        except requests.RequestException as e:
            self.logger.info(u"无法获得城市省份:{}".format(e.args[0]))
        else:
            try:
                result = r.json()
            except Exception as e:
                self.logger.info(u"无法获得城市省份json:{}:{}".format(r.content, e.args[0]))
            else:
                try:
                    id_area_cd = result["data"]["id_area_cd"][-3:]
                    prov_cd = result["data"]["prov_cd"]
                except (TypeError, IndexError, KeyError) as e:
                    self.logger.info(u"获得城市省份返回值错误:{}:{}".format(result, e.args[0]))
                else:
                    extra_cookies = {"CmLocation": "{}|{}".format(prov_cd, id_area_cd)}
                    requests.utils.add_dict_to_cookiejar(self.s.cookies, extra_cookies)

                    url = r"http://shop.10086.cn/i/v1/cust/tipcfg?provCode={}&_=1477447952016".format(prov_cd)
                    try:
                        self.s.get(url, headers=headers["get_sms_verifycode_2"])
                    except requests.RequestException as e:
                        self.logger.info(u"点击客户信息页失败:{}".format(e.args[0]))

        # 点击当月通话详单触发爬取短信验证码
        self.logger.info(u"点击当月通话详单触发爬取短信验证码")
        bill_type, qry_month = self.bill_type_mapping[u"通话详单"], datetime.datetime.now().strftime("%Y%m")
        url = "".join(["https://shop.10086.cn/i/v1/fee/detailbillinfojsonp/{}".format(self.phone),
                       "?callback=jQuery183030442507771585037_{:13.0f}".format(time.time() * 1000),
                       "&curCuror=1",
                       "&step=100",
                       "&qryMonth={}".format(qry_month),
                       "&billType={}".format(bill_type),
                       "&_={:13.0f}".format(time.time() * 1000)])

        try:
            self.s.get(url, headers=headers["get_sms_verifycode_1"])
        except requests.RequestException as e:
            self.logger.info(u"点击当月通话详单触发爬取短信验证码失败:{}".format(e.args[0]))
        else:
            self.logger.info(u"test:点击通话详单触发爬取短信验证码:url:{}:content:{}".format(url, r.content[:150]))

        # 点击爬取短信验证码触发弹窗
        # 成功返回样例 含有'为确保您的详单信息安全，需要对登录号码进行身份验证'
        self.logger.info(u"点击短信验证码触发弹窗")
        url = r"http://shop.10086.cn/i/apps/serviceapps/billdetail/showvec.html"

        try:
            self.s.get(url, headers=headers["get_sms_verifycode_1"])
        except requests.RequestException as e:
            self.logger.info(u"点击爬取短信验证码触发弹窗失败:{}".format(e.args[0]))
        else:
            self.logger.info(u"test:点击爬取短信验证码触发弹窗:url:{}:content:{}".format(url, r.content[:150]))

        # 校验步骤的结束时刻
        end_time = time.time()

        # 移动商城两次触发短信时间间隔需在60秒之上 这里设置成max(self.SMS_INTERVAL - (end_time - start_time), 0)
        self.logger.info(u"两次短信验证码休息开始...")
        time.sleep(max(self.SMS_INTERVAL - (end_time - start_time), 0))

        # 触发短信验证码
        self.logger.info(u"触发短信验证码")
        url = r"https://login.10086.cn/sendSMSpwd.action?callback=result&userName={}".format(self.phone)

        try:
            r = self.s.get(url, headers=headers["get_sms_verifycode_2"])
        except requests.RequestException as e:
            self.logger.info(u"无法触发爬取短信验证码:{}".format(e.args[0]))
            return False, "1010"
        else:
            # 成功的返回样例 'result({"resultCode":"0"})'
            # 失败的返回样例 'result({"resultCode":"1"})'
            resp = r.content
            if resp.find('"0"') > -1:
                self.logger.info(u"成功触发第二次信验证码:{}".format(resp))
                self.write_session()
                return True, "0003"
            else:
                self.logger.info(u"触发爬取短信验证码返回值错误:{}".format(resp))
                return False, "1010"

    @log(u"爬取短信验证码校验")
    def check_sms_verifycode(self, sms):
        """爬取短信验证码校验
        :param sms 爬取短信验证码
        :return 网络异常 (False, "1010")
                爬取短信验证码不正确或过期 (False, "1004")
                短信验证码校验成功 准备爬取 (True, "0004")"""
        url = "".join(["https://login.10086.cn/temporaryauthSMSandService.action",
                       "?callback=result",
                       "&account={}".format(self.phone),
                       "&servicePwd={}".format(self.password),
                       "&smsPwd={}".format(sms),
                       "&accountType=01",
                       "&backUrl=",
                       "&channelID=12003",
                       "&businessCode=01"])

        try:
            r = self.s.get(url, headers=headers["check_sms_verifycode"])
        except requests.RequestException as e:
            self.logger.info(u"提交爬取短信验证码失败:{}".format(e.args[0]))
            return False, "1010"
        else:
            # 验证码输对的返回样例
            # 'result({"assertAcceptURL":"http://shop.10086.cn/i/v1/auth/getArtifact","code":"0000","desc":"认证成功!","islocal":false,"result":"0000"})'
            resp = r.content
            if resp.find(u"认证成功") > -1:
                self.logger.info(u"爬取短信验证码校验成功, 正在爬取:{}".format(resp))
                return True, "0004"
            else:
                # 短信验证码5分钟过期 服务端不区分过期和不正确
                self.logger.info(u"爬取短信验证码校验失败:{}".format(resp))
                return False, "1004"

    @log(u"爬取短信详单")
    def get_sms(self):
        """爬取短信详单
        :return is_sms_success 正常爬取 True ‘特殊时期不受理详单查询业务’ False"""
        for month in self.month_list:
            # 用于增量爬取 月份大于等于上次爬取的月份才爬 month:"201610"  last_scape_month:"201609"
            if month >= self.last_scape_month:
                resp = self.get_detail_by_month(month, bill_type=u"短信/彩信详单")
                self.logger.info(u"test:短信/彩信详单:{}:{}:{}".format(self.phone, month, resp))
                for sms in self.parse_sms_by_month(resp, month):
                    # 用于增量爬取 时间(精确到秒)大于等于上次爬取的时间才入库
                    if self.last_scape_dt_0 <= sms["time"] < self.today:
                        sms.save()
                    else:
                        self.logger.info(u"{}短信时间{}早于上次爬取时间{}(或晚于当天{}) 不再入库 跳过".
                                         format(self.phone, sms["time"], self.last_scape_dt_0, self.today))
            else:
                self.logger.info(u"{}短信月份{}早于上次爬取月份{} 不再爬取 跳过".
                                 format(self.phone, month, self.last_scape_month))
        return True

    @log(u"爬取通话详单")
    def get_call(self):
        """爬取通话详单
        :return is_call_success 正常爬取 True
        DETAIL_FAIL_INFO False 掉出登录"""
        for month in self.month_list:
            # 用于增量爬取 月份大于等于上次爬取的月份才爬 month:"201610"  last_scape_month:"201609"
            if month >= self.last_scape_month:
                resp = self.get_detail_by_month(month, bill_type=u"通话详单")
                self.logger.info(u"test:通话详单:{}:{}:{}".format(self.phone, month, resp))
                if resp.find(DETAIL_FAIL_INFO) > 0:
                    self.logger.info(u"{}掉出登录:{}".format(self.phone, resp))
                    return False
                else:
                    for call in self.parse_call_by_month(resp, month):
                        # 用于增量爬取 时间(精确到秒)大于等于上次爬取的时间才入库
                        if self.last_scape_dt_0 <= call["time"] < self.today:
                            call.save()
                        else:
                            self.logger.info(u"{}通话详时间{}早于上次爬取时间{}(或晚于当天{}) 不再入库 跳过".
                                             format(self.phone, call["time"], self.last_scape_dt_0, self.today))
            else:
                self.logger.info(u"{}通话月份{}早于上次爬取月份{} 不再爬取 跳过".
                                 format(self.phone, month, self.last_scape_month))
        return True

    @retry(False)
    def get_detail_by_month(self, month_name, bill_type):
        """爬取短信/通话详单的通用函数
        :param month_name 月份 "201610"
        :param bill_type 详单类型
        :return 没有网络异常: r.content
                出现网络异常 False"""
        url = "".join(["https://shop.10086.cn/i/v1/fee/detailbillinfojsonp/{}".format(self.phone),
                       "?callback=jQuery18305637221474059924_{:13.0f}".format(time.time() * 1000),
                       "&curCuror=1",
                       "&step=100",
                       "&qryMonth={}".format(month_name),
                       "&billType={}".format(self.bill_type_mapping[bill_type]),
                       "&_={:13.0f}".format(time.time() * 1000)])

        try:
            r = self.s.get(url, headers=headers["_get_detail"])
        except requests.RequestException as e:
            self.logger.info(u"下载{}{}详单失败:{}".format(month_name, bill_type, e.args[0]))
            return False
        else:
            # 失败样例 {u'retCode': u'500003', u'retMsg': u'not login.but must login.sso flag.'}
            self.logger.info(u"下载{}{}详单成功".format(month_name, bill_type))
            return r.content

    def parse_sms_by_month(self, resp, month):
        """获得当月的短信详单
        :param month 月份
        :param resp 返回值
        :return [Sms生成器]"""

        try:
            resp = utils.get_jquery_detail(resp)
        except ValueError as e:
            self.logger.info(u"{}短信详单格式改变1:{}".format(month, e.args[0]))
            return

        json_data = json.loads(resp).get("data")

        if not isinstance(json_data, list):
            self.logger.info(u"{}短信详单格式改变2:{}".format(month, resp))
            return

        for value in json_data:
            sms = Sms(task_id=self.task_id, mobile=self.phone)

            # 开始时间 如果开始时间是20(年份)开头，保持不变，否则加上年份
            start_time = value.get("startTime", "").strip()
            sms["time"] = utils.get_detail_time(start_time, month)

            # 对方号码
            sms["peer_number"] = value.get("anotherNm", "")

            # 通话地
            sms["location"] = value.get("commPlac", "")

            # 收发状态
            send_type = value.get("commMode")
            sms["send_type"] = utils.get_send_type(send_type)

            # 信息类型
            msg_type = value.get("infoType")
            sms["msg_type"] = utils.get_msg_type(msg_type)

            # 业务名称 优先从busiName获得 然后从meal获得
            busi_name = value.get("busiName", "")
            meal = value.get("meal", "")

            sms["service_name"] = busi_name or meal

            # 通话费
            fee = value.get("commFee")
            sms["fee"] = utils.get_value(fee)

            yield sms

    def parse_call_by_month(self, resp, month):
        """获得当月的通话详单
        :param month 月份
        :param resp 返回值
        :return [Call生成器]"""

        try:
            resp = utils.get_jquery_detail(resp)
        except ValueError as e:
            self.logger.info(u"{}通话详单格式改变1:{}".format(month, e.args[0]))
            return

        json_data = json.loads(resp).get("data")

        if not isinstance(json_data, list):
            self.logger.info(u"{}通话详单格式改变2:{}".format(month, resp))
            return

        for value in json_data:
            call = Call(task_id=self.task_id, mobile=self.phone)

            # 开始时间 如果开始时间是20(年份)开头，保持不变，否则加上年份
            start_time = value.get("startTime", "").strip()
            call["time"] = utils.get_detail_time(start_time, month)

            # 对方号码
            call["peer_number"] = value.get("anotherNm", "")

            # 通话地
            call["location"] = value.get("commPlac", "")

            # 通话类型
            call["location_type"] = value.get("commType", "")

            # 通话时长
            duration = value.get("commTime")
            call["duration"] = utils.get_duration(duration)

            # 主被叫
            dial_type = value.get("commMode")
            call["dial_type"] = utils.get_dial_type(dial_type)

            # 通话费
            fee = value.get("commFee")
            call["fee"] = utils.get_value(fee)

            yield call

    @log(u"爬取基本信息")
    @retry(False)
    def get_basic(self):
        """获得基本信息
        :return 成功 True  移动异常 False"""

        # 获得用户基本资料 [左侧我的信息-个人信息]
        url = r"http://shop.10086.cn/i/v1/cust/info/{}?_={:13.0f}".format(self.phone, time.time() * 1000)
        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取个人信息-基本资料失败:{}".format(e.args[0]))
            return False
        else:
            # 失败样例
            result = r.content

        # 获得当前余额 [左上方个人中心]
        url = r"http://shop.10086.cn/i/v1/fee/real/{}?_={:13.0f}".format(self.phone, time.time() * 1000)

        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取个人信息-当前余额失败{}".format(e.args[0]))
            result_2 = ""
        else:
            # 失败样例
            result_2 = r.content

        # 获得套餐名称  [左上方个人中心]
        url = r"http://shop.10086.cn/i/v1/cust/mergecust/{}?_={:13.0f}".format(self.phone, time.time() * 1000)
        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取个人信息-套餐名称失败:{}".format(e.args[0]))
            result_3 = ""
        else:
            result_3 = r.content

        # 获得省份城市 [左上方个人中心]
        url = r"http://shop.10086.cn/i/v1/res/numarea/{}?_={:13.0f}".format(self.phone, time.time() * 1000)
        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取个人信息-省份城市失败:{}".format(e.args[0]))
            result_4 = ""
        else:
            result_4 = r.content

        self.logger.info(u"test:个人信息-基本资料:{}:{}".format(self.phone, result))
        self.logger.info(u"test:个人信息-套餐名称:{}:{}".format(self.phone, result_2))
        self.logger.info(u"test:个人信息-当前余额:{}:{}".format(self.phone, result_3))
        self.logger.info(u"test:个人信息-省份城市:{}:{}".format(self.phone, result_4))

        # 解析得到基本信息
        basic = self.parse_basic(result, result_2, result_3, result_4)
        basic.save()

        return True

    def parse_basic(self, resp, resp_2, resp_3, resp_4):
        """解析基本信息
        :param resp [str] 用户基本资料相关数据
        :param resp_2 [str] 当前余额相关数据
        :param resp_3 [str] 套餐名称相关数据
        :param resp_4 [str] 省份-城市相关数据
        :return [Basic] 基本信息"""

        basic = Basic(task_id=self.task_id, mobile=self.phone, carrier="CHINA_MOBILE",
                      last_modify_time=datetime.datetime.now().strftime('%Y-%m-%d'),
                      scrape_dt=datetime.datetime.now().strftime('%Y-%m-%d'))

        # 个人信息-基本资料
        try:
            result = json.loads(resp).get("data")
        except ValueError as e:
            self.logger.info(u"个人信息-基本资料格式改变1:{}:{}".format(e.args[0], resp))
            basic["name"], basic["level"], basic["state"] = "", "", -1
        else:
            if isinstance(result, dict):
                basic["name"] = result.get("name", "")
                basic["level"] = result.get("level", "")

                state = result.get("status")
                basic["state"] = utils.get_state(state)

                # 先从inNetDate获得入网时间，如失败，从netAge获取
                # 样例 inNetDate=20160828155042 netAge=2个月
                open_time = result.get("inNetDate")
                basic["open_time"] = open_time[:4] + "-" + open_time[4:6] + "-" + open_time[6:8]
                if not basic["open_time"]:
                    self.logger.info(u"无法获得入网时间 尝试从网龄获取")
                    open_time = result.get("netAge")
                    basic["open_time"] = utils.get_open_time(open_time)
            else:
                self.logger.info(u"个人信息-基本资料格式改变2:{}".format(resp))
                basic["name"], basic["level"],  basic["state"] = "", "", -1

        # 个人信息-套餐名称
        try:
            result_3 = json.loads(resp_3).get("data")
        except ValueError as e:
            self.logger.info(u"个人信息-套餐名称格式改变1:{}:{}".format(e.args[0], resp_3))
            basic["package_name"] = ""
        else:
            if isinstance(result_3, dict):
                # 套餐名称 优先取curPlanName字段中的 如为空 取nextPlanName中的(陕西就是这种情况)
                try:
                    package_name = result_3["curPlanQryOut"]["curPlanName"]
                except (TypeError, IndexError, KeyError):
                    package_name = ""

                try:
                    package_name_2 = result_3["curPlanQryOut"]["nextPlanName"]
                except (TypeError, IndexError, KeyError):
                    package_name_2 = ""

                basic["package_name"] = package_name or package_name_2
            else:
                self.logger.info(u"个人信息-套餐名称格式改变:{}".format(resp_3))
                basic["package_name"] = ""

        # 个人信息-当前余额
        try:
            result_2 = json.loads(resp_2).get("data")
        except ValueError as e:
            self.logger.info(u"个人信息-当前余额格式改变1:{}:{}".format(e.args[0], resp_2))
            basic["province"], basic["city"] = "", ""
        else:
            if isinstance(result_2, dict):
                available_balance = result_2.get("curFee")
                basic["available_balance"] = utils.get_value(available_balance)
            else:
                self.logger.info(u"个人信息-当前余额格式改变2:{}".format(resp_2))
                basic["available_balance"] = 0

        # 个人信息-省份城市
        try:
            result_4 = json.loads(resp_4).get("data")
        except ValueError as e:
            self.logger.info(u"个人信息-省份城市格式改变1:{}:{}".format(e.args[0], resp_4))
            basic["province"], basic["city"] = "", ""
        else:
            if isinstance(result_4, dict):
                # 省份
                province = int(result_4.get("prov_cd", 0))
                try:
                    basic["province"] = utils.get_province_code(province)
                except ValueError as e:
                    self.logger.info("{}".format(e.args[0]))
                # 城市
                basic["city"] = result_4.get("id_name_cd", "")
            else:
                self.logger.info(u"个人信息-省份城市格式改变2:{}".format(resp_4))
                basic["province"], basic["city"] = "", ""

        return basic

    @log(u"获得套餐余量信息")
    @retry(False)
    def get_package_usage(self):
        """获得套餐余量信息"""

        url = r"http://shop.10086.cn/i/v1/fee/planbal/{}?_={:13.0f}".format(self.phone, time.time() * 1000)
        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取套餐余量失败:{}".format(e.args[0]))
            return False
        else:
            resp = r.content
            self.logger.info(u"test:套餐余量:{}:{}".format(self.phone, resp))
            package_usage = self.parse_package_usage(resp)
            package_usage.save()

        return True

    def parse_package_usage(self, resp):
        """解析套餐余量信息
        :param resp 套餐余量信息
        :return [PackageUsage] 套餐余量"""
        resp = json.loads(resp).get("data")
        package_usage = PackageUsage(task_id=self.task_id, mobile=self.phone)
        package_usage["bill_month"] = datetime.datetime.today().strftime("%Y-%m")
        package_usage["bill_start_date"] = package_usage["bill_month"] + "-01"
        package_usage["bill_end_date"] = datetime.datetime.today().strftime("%Y-%m-%d")

        package_usage["items"] = []
        try:
            result_list = resp[0]["arr"]
        except (KeyError, AttributeError, TypeError) as e:
            self.logger.info(u"套餐余量格式改变1:{}:{}".format(e.args[0], resp))
        else:
            for result in result_list:
                package_item = PackageItem()
                package_item["item"] = result.get("mealName")
                try:
                    infos = result["resInfos"][0]["secResInfos"][0]["resConInfo"]
                except (KeyError, IndexError, TypeError) as e:
                    self.logger.info(u"套餐余量格式改变2:{}:{}".format(e.args[0], resp))
                else:
                    package_item["total"] = infos.get("totalMeal", "")
                    package_item["used"] = infos.get("useMeal", "")
                    unit = infos.get("unit", "")
                    package_item["unit"] = utils.get_unit(unit)
                    package_usage["items"].append(package_item)

            return package_usage

    @log(u"爬取账单信息")
    @retry(False)
    def get_bill(self):
        """爬取账单信息"""
        # begin_month, end_month 样例("201610", "201605")
        begin_month, end_month = self.month_list[1], self.month_list[-1]

        url = r"http://shop.10086.cn/i/v1/fee/billinfo/{}?bgnMonth={}&endMonth={}&_={:13.0f}".\
            format(self.phone, begin_month, end_month, time.time() * 1000)

        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取账单信息失败:{}".format(e.args[0]))
            return False
        else:
            resp = r.content
            self.logger.info(u"test:账单信息:{}:{}".format(self.phone, resp))
            today = datetime.date.today()
            for bill in self.parse_bill(resp):
                last_month = datetime.date.strftime(today + relativedelta(months=-1), '%Y-%m')
                if today.day <= 5 and bill["bill_month"] == last_month:
                    # 如果今天是5号之前, 那么上个月的账单未出, 需要跳过
                    self.logger.info(u"今天是每月{}号:跳过{}账单".format(today.day, bill["bill_month"]))
                    continue

                if bill["base_fee"] == 0 and bill["total_fee"] == 0:
                    # base_fee为零 舍弃
                    self.logger.info(u"{}的{}月的账单套餐费与总费用为0 跳过".format(self.phone, bill["bill_month"]))
                    continue

                # 这个最后做
                flag_string = str(self.phone) + bill["bill_month"]
                flag_md = hashlib.md5()
                flag_md.update(flag_string)
                flag_code = redis_insert_set(flag_md.hexdigest())

                if flag_code == 0:
                    # 重复
                    self.logger.info(u"{}的{}月的账单已经存在 跳过".format(self.phone, bill["bill_month"]))
                    continue

                bill.save()

        return True

    def parse_bill(self, resp):
        """获得当月的账单信息
        :param resp 爬取得到信息
        :return [Bill生成器]"""
        resp_list = json.loads(resp).get("data")

        if not isinstance(resp_list, list):
            self.logger.info(u"账单信息格式改变:{}".format(resp))
            return

        json_path = {"base_fee": u"$.billMaterials[?(@.billEntriy='01')].billEntriyValue",
                     "extra_service_fee": u"$.billMaterials[?(@.billEntriy='05')].billEntriyValue",
                     "voice_fee": u"$.billMaterials[?(@.billEntriy='02')].billEntriyValue",
                     "sms_fee": u"$.billMaterials[?(@.billEntriy='04')].billEntriyValue",
                     "web_fee": u"$.billMaterials[?(@.billEntriy='03')].billEntriyValue",
                     "extra_fee": u"$.billMaterials[?(@.billEntriy='09')].billEntriyValue",
                     "daishou_fee": u"$.billMaterials[?(@.billEntriy='06')].billEntriyValue",
                     }
        for resp_value in resp_list:
            bill = Bill(task_id=self.task_id, mobile=self.phone)

            bill_month = resp_value.get("billMonth", "")

            # 爬取当月的的账单不需要
            if bill_month == datetime.datetime.today().strftime("%Y%m") \
                    or bill_month == datetime.datetime.today().strftime("%Y-%m"):
                continue

            # 账单月
            if len(bill_month) == 6:
                # 形如201611
                bill["bill_month"] = bill_month[:4] + "-" + bill_month[4:6]
            elif len(bill_month) == 7:
                # 形如2016-11
                bill["bill_month"] = bill_month[:4] + "-" + bill_month[5:7]
            else:
                bill["bill_month"] = ""

            # 账单起始日期
            bill_start_date = resp_value.get("billStartDate")
            if bill_start_date:
                bill["bill_start_date"] = "-".join([bill_start_date[:4], bill_start_date[4:6], bill_start_date[6:8]])
            else:
                bill["bill_start_date"] = ""

            # 账单结束日期
            bill_end_date = resp_value.get("billEndDate")
            if bill_end_date:
                bill["bill_end_date"] = "-".join([bill_end_date[:4], bill_end_date[4:6], bill_end_date[6:8]])
            else:
                bill["bill_end_date"] = ""

            try:
                base_fee = jsonpath_rw_ext.parse(json_path["base_fee"]).find(resp_value)[0].value
                extra_service_fee = jsonpath_rw_ext.parse(json_path["extra_service_fee"]).find(resp_value)[0].value
                voice_fee = jsonpath_rw_ext.parse(json_path["voice_fee"]).find(resp_value)[0].value
                sms_fee = jsonpath_rw_ext.parse(json_path["sms_fee"]).find(resp_value)[0].value
                web_fee = jsonpath_rw_ext.parse(json_path["web_fee"]).find(resp_value)[0].value
                extra_fee = jsonpath_rw_ext.parse(json_path["extra_fee"]).find(resp_value)[0].value
                daishou_fee = jsonpath_rw_ext.parse(json_path["daishou_fee"]).find(resp_value)[0].value
            except Exception as e:
                base_fee, extra_service_fee,  voice_fee, sms_fee, web_fee, extra_fee, daishou_fee = (None, None, None,
                                                                                                     None, None, None,
                                                                                                     None)
                self.logger.info(u"账单信息格式改变:{}:{}".format(e.args[0], resp))

            bill["base_fee"] = utils.get_value(base_fee)
            bill["extra_service_fee"] = utils.get_value(extra_service_fee)
            bill["voice_fee"] = utils.get_value(voice_fee)
            bill["sms_fee"] = utils.get_value(sms_fee)
            bill["web_fee"] = utils.get_value(web_fee)
            bill["extra_fee"] = utils.get_value(extra_fee)
            # discount理解成代收费
            bill["discount"] = utils.get_value(daishou_fee)

            bill["actual_fee"] = sum([bill["base_fee"], bill["extra_service_fee"], bill["voice_fee"], bill["sms_fee"],
                                     bill["web_fee"], bill["extra_fee"]])

            bill["total_fee"] = bill["actual_fee"] + bill["discount"]

            bill["extra_discount"] = 0
            bill["paid_fee"] = 0
            bill["unpaid_fee"] = 0
            bill["point"] = -1
            bill["last_point"] = -1
            bill["related_mobiles"] = []
            bill["notes"] = ""

            yield bill

    @log(u"爬取充值信息")
    @retry(False)
    def get_recharge(self):
        """爬取充值信息"""
        end_time = datetime.datetime.today()
        start_time = end_time + relativedelta(months=-5)
        url = r"http://shop.10086.cn/i/v1/pay/his/{}?startTime={}&endTime={}&_={:13.0f}". \
            format(self.phone, start_time.strftime("%Y%m%d"), end_time.strftime("%Y%m%d"), time.time() * 1000)

        try:
            r = self.s.get(url, headers=headers["_get_basic"])
        except requests.RequestException as e:
            self.logger.info(u"爬取充值信息失败:{}".format(e.args[0]))
            return False
        else:
            resp = r.content
            self.logger.info(u"test:充值信息:{}:{}".format(self.phone, resp))
            for recharge in self.parse_recharge(r.content):
                # 用于增量爬取 时间(精确到秒)大于上次爬取的时间才入库
                if self.last_scape_dt_0 <= recharge["recharge_time"] < self.today:
                    recharge.save()

        return True

    def parse_recharge(self, resp):
        """解析充值信息
        :param resp 充值信息
        :return [Recharge生成器]"""
        result = json.loads(resp).get("data")
        if not isinstance(result, list):
            self.logger.info(u"充值信息格式改变:{}".format(resp))
            return

        for item in result:
            recharge = Recharge(task_id=self.task_id, mobile=self.phone)
            recharge_time = item.get("payDate")
            if recharge_time:
                recharge["recharge_time"] = recharge_time[:4] + "-" + recharge_time[4:6] + "-" + recharge_time[6:8]
            else:
                self.logger.info(u"充值信息格式改变:{}".format(resp))
                recharge["recharge_time"] = ""

            amount = item.get("payFee")
            recharge["amount"] = utils.get_value(amount)
            recharge["type"] = item.get("payTypeName", "")

            # 如甘肃18794224550 有不少充值金额为0 不要了
            if recharge["amount"] > 0:
                yield recharge

    @log(u"解析入库")
    def start_spider_details_mul(self):
        """获得信息并解析入库-多线程
        没有使用"""

        # 获得该电话号码上次的爬取时间
        # 返回样例 (u'2016-11-04 17:15:04', u'2016-11', u'201611')
        # self.last_scape_dt, self.last_scape_month_str, self.last_scape_month = get_last_scape_dt(self.phone)

        thread_list = []

        f_list = [self.get_sms, self.get_call, self.get_basic, self.get_package_usage, self.get_bill, self.get_recharge]
        for f in f_list:
            thread_list.append(threading.Thread(target=f))

        for t in thread_list:
            t.start()
            # 随机休息0-1秒 不然请求太集中 可能抓不到内容
            time.sleep(random.random())

        for t in thread_list:
            t.join()

        # 写入成功的信息
        self.get_status()

    @log(u"解析入库")
    def start_spider_details(self):
        """获得信息并解析入库-单线程
        :return 成功: (True, "5000")
                失败: (False, "4001")
                移动服务异常: (False, "1010")
                掉出登录: (False, "3001")"""

        is_call_success = self.get_call()

        if not is_call_success:
            # 掉出登录
            return False, "3001"

        self.get_sms()
        is_basic_success = self.get_basic()
        self.get_package_usage()
        self.get_bill()
        is_recharge_success = self.get_recharge()

        # 写入成功的信息
        if is_recharge_success and is_basic_success:
            self.get_status()
            self.logger.info(u"入库成功")
            return True, "5000"
        else:
            self.logger.info(u"入库失败")
            return False, "4001"

    def get_status(self):
        """写入成功信息"""
        status = Status(task_id=self.task_id,
                        mobile=self.phone,
                        status="1",
                        scrape_dt=datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S"))
        status.save()


if __name__ == "__main__":

    a = MobileShopSpider(task_id="111", phone="123", password="kkk", proc_num=101, step="Login")
    print a.last_scape_dt, a.last_scape_dt_0










