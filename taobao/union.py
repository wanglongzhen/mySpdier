# -*- coding:utf-8 -*-

"""
File Name: union.py
Version: 0.1
Description: 基类：包含公共设置

Author: gonghao
Date: 2016/6/23 16:08
"""

from comm_log import comm_log
import requests
import time
import datetime
import calendar
import re
import sys

reload(sys)
sys.setdefaultencoding("utf-8")


class Union(object):
    """
    公共配置
    """
    def __init__(self, proc_num):
        # 1. 配置日志
        self.logger = comm_log(proc_num)

        # 2. 创建一个Session
        # 2.1 配置头信息
        ua = ("Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 " +
              "(KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36")
        self.header = {
            "HOST": "iservice.10010.com",
            "Origin": "http://iservice.10010.com",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": r"https://uac.10010.com/portal/homeLogin",
            "Accept": r"application/json, text/javascript, */*; q=0.01",
            "User-Agent": ua,
            "Accept-Encoding": r"deflate",
            "Accept-Language": r"zh-CN,zh;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Content-Type": r"application/x-www-form-urlencoded;charset=UTF-8"
        }

        # 2.2 创建带上述头信息的会话
        self.ses = requests.Session()
        self.ses.headers = self.header

        # 3. 相关网页
        # 3.1 主页
        self.home_url = "http://www.10010.com/"
        # 3.2 登录页面
        self.login_url = "https://uac.10010.com/portal/homeLogin"
        # 3.3 登录认证页面 -- 存在需要替换的字符
        self.login_url2 = ("https://uac.10010.com/portal/Service/" +
                           "MallLogin?callback=jQuery1720029789068" +
                           "503305316_{t1}&req_time={t2}&redirectURL" +
                           "=http%3A%2F%2Fwww.10010.com&userName=" +
                           "{number}&password={password}&pwdType=" +
                           "01&productType=01&redirectType=" +
                           "01&rememberMe=1&_={t3}")
        # 3.4 通话记录下载地址 excel
        self.call_url = "http://iservice.10010.com//e3/ToExcel.jsp?type=sound"
        # 3.5 个人信息地址
        self.per_info_url = "https://uac.10010.com/cust/infomgr/infomgrInit"
        self.per_json = "https://uac.10010.com/cust/infomgr/anonymousInfoAJAX"

        # 3.6 历史账单使用json返回值输出，不使用下载excel的方式

        # 3.7 短信记录下载地址
        self.sms_url = "http://iservice.10010.com/e3/ToExcel.jsp?type=sms3"

        # 3.8 套餐使用余量查询
        self.user_info = "https://uac.10010.com/cust/userinfo/userInfoInit"
        self.user_json = "https://uac.10010.com/cust/userinfo/getBindnumInfo"

        # 3.9 获取号码归属地
        self.location_info = "http://iservice.10010.com/e3/static/life/callerLocationQuery?_="

        # 3.10 获取套餐余量
        self.package_info = "http://iservice.10010.com/e3/static/query/queryLeavePackageData?_={ts}&menuid=000100040001"

        # 3.11 获取账户充值记录
        self.money_info = "http://iservice.10010.com/e3/static/query/paymentRecord?_={ts}&menuid=000100010003"

        # 4. 格式化不同不类型的查询信息
        self.keyword_infos = {
            "call": u"通话记录信息",
            "sms": u"短信记录信息",
            "bill": u"历史账单信息",
        }

    @staticmethod
    def get_timestamp():
        """
        获取时间戳
        :return: 一个时间戳
        """
        return str(time.time()).replace(".", "0")

    def check_if_login(self):
        """
        检查是否成功登录（同时也是获取各个页面的中间必要通信环节）
        :return: True for success; False for not.
        """
        self.logger.info(u"验证是否是登录状态...")

        checkin_url = "http://iservice.10010.com/e3/static/check/checklogin?_="
        try:
            res = self.ses.post(checkin_url + Union.get_timestamp())
        except Exception as e:
            self.logger.error(u"[1001] 无法发送获取登录状态的请求" + str(checkin_url))
            self.logger.error(str(e))
            return False, "0003"

        try:
            result = res.json().get("isLogin")
        except Exception as e:
            self.logger.error(u"[1002] check_login登录状态返回内容异常")
            self.logger.error(str(e))
            return False, "0001"

        if result is None:
            self.logger.error(u"[1002] check_login登录状态返回内容异常")
            return False, "0001"

        if result:
            self.logger.info(u"成功登录联通官网")
            return True, "0000"
        else:
            self.logger.warning(u"登录联通官网失败")
            return False, "0003"

    @staticmethod
    def get_begin_end_date(bill_date):
        """
        根据输入的年月，输出当月的起始天数
        :param bill_date: 2015-06
        :return: ["2015-06-01", "2015-06-30"]
        """
        # 检验是否是当月
        today = str(datetime.date.today())
        current_ym = today[:7]
        if current_ym == bill_date:
            return bill_date + "-01", today

        bd = list(map(int, bill_date.split("-")))
        days = calendar.monthrange(*bd)

        return bill_date + "-01", bill_date + "-" + str(days[1])

    @staticmethod
    def convert_c_time(c_time):
        """
        将中文时间转换成秒数：
        "1时1分20秒" => "3680"
        "1分20秒" => "80"
        "20秒" => "20"
        :param c_time: 中文时间
        :return:
        """
        hms = map(int, re.findall(u"\d+", c_time))
        if len(hms) == 3:
            return 3600 * hms[0] + 60 * hms[1] + hms[2]

        if len(hms) == 2:
            return 60 * hms[0] + hms[1]

        if len(hms) == 1:
            return hms[0]

        return None

if __name__ == '__main__':
    pass
