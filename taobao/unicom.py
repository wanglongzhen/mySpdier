# -*- coding:utf-8 -*-
"""
File Name : 'Spider'.py
Description:
Author: 'wanglongzhen'
Date: '2016/11/20' '21:00'
"""

import sys
import os
import time
from bs4 import BeautifulSoup as bs
import requests

from selenium import webdriver
from selenium.webdriver.common.action_chains import  ActionChains
import selenium.webdriver.support.ui as ui
import requests
import comm_log
import urlparse
import re
import ConfigParser
import MySQLdb
import traceback
from PIL import Image
import base64
import cookielib
from location_scraper import location_scrape
from Operator import Operator
import datetime
from dateutil.relativedelta import relativedelta

from requests.utils import DEFAULT_CA_BUNDLE_PATH
import calendar
import json
import shutil


reload(sys)
sys.setdefaultencoding("utf-8")

class Unicom(Operator):
    def __init__(self, phone_number, phone_passwd):
        self.phone_number = phone_number
        self.phone_passwd = phone_passwd

        Operator.__init__(self, phone_number, phone_passwd)
        Operator.get_task_no(self, phone_number=phone_number)

        self.homepage = 'http://www.10010.com'
        self.login_url = 'https://uac.10010.com/portal/homeLogin'
        self.driver = None

    def init_driver(self):
        try:
            self.driver = webdriver.PhantomJS()
            # self.driver = webdriver.Chrome()
            # self.driver = webdriver.Firefox()
            self.driver.maximize_window()

            self.driver.delete_all_cookies()
        except Exception, e:
            self.write_log(traceback.format_exc())

    def exit(self):
        if self.driver != None:
            self.driver.exit()

    def start(self):
        self.login()

        self.init_cookie()
        self.spider()

    def init_cookie(self):

        self.ses = requests.session()

        print self.driver.get_cookies()
        # cookies = requests.utils.dict_from_cookiejar(self.driver.get_cookies())
        # print cookies
        for cookie in self.driver.get_cookies():
            print cookie
            requests.utils.add_dict_to_cookiejar(self.ses.cookies, {cookie['name']:cookie['value']})


        print self.ses.cookies

        print "u"
        pass

    def login(self, img_sms = None):
        #登录
        self.init_driver()

        self.open_login_page(self.login_url, self.phone_number, self.phone_passwd)

        self.sumbit_login()



    def open_login_page(self, login_url, phone_number, phone_passwd):
        self.driver.get(login_url)
        self.write_log(u'成功打开登录页： ' + login_url)

        try:
            self.driver.find_element_by_xpath("//input[@id='userName']").clear()
            self.driver.find_element_by_xpath("//input[@id='userName']").send_keys(phone_number)

            self.write_log(u'输入用户名： ' + phone_number)

            self.driver.find_element_by_xpath("//input[@id='userPwd']").clear()
            self.driver.find_element_by_xpath("//input[@id='userPwd']").send_keys(phone_passwd)

            self.write_log(u'输入密码： ' + phone_passwd)
        except Exception, e:
            self.recordErrImg()
            self.write_log(traceback.format_exc())
            return False

        return True

    def sumbit_login(self):
        self.driver.find_element_by_xpath("//input[@id='login1']").click()
        if self.wait_element_displayed(self.driver, 'nickSpan') == False:
            self.write_log(u'元素加载失败')

        if self.driver.current_url == self.login_url:
            # 没有跳转
            message = ""
            try:
                message = self.driver.find_element_by_xpath('//span[@class="error left mt35mf32"]').text
            except:
                self.recordErrImg()
                self.write_log(traceback.format_exc())
            try:
                message = self.driver.find_element_by_xpath('//span[@class="error left mt10mf32"]').text
            except:
                self.recordErrImg()
                self.write_log(traceback.format_exc())

            return False

        self.write_log(u'登录成功')

        return True

    def wait_element_displayed(self, browser, element):
        count = 0
        while(True):
            count = count + 1
            if count > 3:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver : driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                self.write_log(u'元素没有显示' + element)

        return True

    def spider(self):

        #获取数据
        personal_info = self.get_personal_info()
        if len(personal_info) != 0:
            print personal_info
            for item in personal_info:
                print item
                print personal_info[item]

        # bill_info = self.get_bill_info()

        call_info = self.get_call_info()
        print 'u'




        #存储数据

    def get_personal_info(self):
        """
        获取账号基本信息
        :return:
        """
        # 1. 获取个人基本信息
        checkin_url = "http://iservice.10010.com/e3/static/check/checklogin?_="
        try:
            res = self.ses.post(checkin_url + Operator.get_timestamp())
        except Exception as e:
            self.write_log(u"[3002] 无法发送获取登录状态的请求" + str(checkin_url))
            self.write_log(str(e))
            return False

        try:
            res_json = res.json().get("userInfo")
        except Exception as e:
            self.write_log(u"[3003] 用户基本信息(userInfo)返回内容异常")
            self.write_log(str(e))
            return False

        # 2. 获取余额以及最近更新时间
        try:
            self.ses.get(self.user_info)
            res2 = self.ses.post(self.user_json)
        except Exception as e:
            self.write_log(u"[3002] 无法打开账户信息页面" + str(self.user_json))
            self.write_log(str(e))
            return False

        try:
            res2_json = res2.json().get("defBindnumInfo").get("costInfo")
        except Exception as e:
            self.write_log(u"[3003] 账户信息页面(costInfo)返回内容异常")
            self.write_log(str(e))
            res2_json = None

        # 3. 整理结果
        open_time = res_json.get("opendate")
        if open_time is None:
            try:
                open_time = res2.json().get("defBindnumInfo").get("mydetailinfo").get("opendate")
            except Exception as e:
                self.write_log(u"[3003] 账户信息页面返回内容异常")
                self.write_log(str(e))
                open_time = ""
            else:
                open_time = open_time.replace(u"年", "-").replace(u"月", "-").replace(u"日", "").strip()
        else:
            open_time = open_time[:4] + '-' + open_time[4:6] + '-' + open_time[6:8]

        result = dict()
        result["real_name"] = res_json.get("custName")
        result["id_card"] = res_json.get("certnum")
        result["addr"] = res_json.get("certaddr")
        result["user_source"] = "CHINA_UNICOM"
        result["level"] = res_json.get("vip_level")
        result["state"] = -1
        result["open_time"] = open_time
        result["package_name"] = res_json.get("packageName")

        if result["level"] is None:
            try:
                res = self.ses.post("https://uac.10010.com/cust/userinfo/userInfo")
                level_json = res.json()
            except Exception as e:
                self.write_log(u"[3002] 无法获取用户VIP等级")
                result["level"] = ""
                self.write_log(str(e))
            else:
                result["level"] = level_json.get("vipLevel")

        if result["level"] is None:
            result["level"] = ""

        if res2_json is not None:
            try:
                result["phone_remain"] = int(float(res2_json.get("balance")) * 100)
            except Exception as e:
                self.write_log(u"[3003] 获取的账户余额数值异常: " + str(res2_json.get("balance")))
                self.write_log(str(e))
                result["phone_remain"] = None
        else:
            result["phone_remain"] = None
        result["last_modify_time"] = ""

        if result["phone_remain"] is None:
            result["phone_remain"] = ''

        # 获取归属地
        try:
            result["province"], result["city"] = location_scrape(self.phone_number)
        except Exception as e:
            self.write_log(u"[3004] 获取号码归属地的程序出现异常")
            self.write_log(str(e))
            result["province"], result["city"] = ["", ""]


        return result

    def get_bill_info(self):

        bill_info = list()
        today = datetime.date.today()
        bill_date_list = list(map(lambda delta: str(today + relativedelta(months=delta))[:7], range(-6, 1, 1)))


        # for bill_date in bill_date_list[:-1]:
        #     ret = self.get_bills_info(bill_date)
        #     bill_info.append(ret)

        for bill_date in bill_date_list[1:]:
            self.get_calls_info(bill_date)
            # self.get_smss_info(bill_date)

        return bill_info

    def get_call_info(self):
        bill_info = list()
        today = datetime.date.today()
        bill_date_list = list(map(lambda delta: str(today + relativedelta(months=delta))[:7], range(-6, 1, 1)))

        for bill_date in bill_date_list[1:]:
            self.get_calls_info(bill_date)
            # self.get_smss_info(bill_date)

        return bill_info

    def get_calls_info(self, bill_date):
        """
        爬取指定日期的通话记录
        :param bill_date: 需要爬取的月份，例："2016-05"
        :return:
        """
        self.write_log(u"开始爬取通话记录: " + bill_date + "...")

        search_url = "http://iservice.10010.com/e3/query/call_dan.html"
        search_url2 = "http://iservice.10010.com/e3/static/query/callDetail?_={strtsmp}&menuid=000100030001"

        # 1. 设置查询的账单日期
        set_date_success = self.set_date(search_url, search_url2, bill_date, keyword="call")

        # 2. 下载通话记录信息，保存至file_path
        file_name = "{tid}_call_log_{bill_date}.xls".format(tid=self.task_id, bill_date=bill_date)
        file_path = os.path.join(self.parent_path, "output", self.task_id, file_name)
        if set_date_success:
            self.save_data(self.call_url, file_path, keyword="call")

        if set_date_success is False:
            self.un_success.append(("call", bill_date))
            self.write_log(bill_date + u"不存在通话记录信息！或网络问题设置账单日期失败!")

        if set_date_success is None:
            self.un_success.append(("call", bill_date))
            self.write_log(u"[3004] 无法设定通话详单的账单日期")
            self.write_log(u"通话记录信息获取失败!")

    def get_smss_info(self, bill_date):
        """
        爬取指定日期的短信记录
        :param bill_date: 需要爬取的月份，例："2016-05"
        :return:
        """
        self.write_log(u"开始爬取短信记录" + bill_date + "...")

        search_url = "http://iservice.10010.com/e3/query/call_sms.html"
        search_url2 = "http://iservice.10010.com/e3/static/query/sms?_={strtsmp}&menuid=000100030002"

        # 1. 设置查询的账单日期
        set_date_success = self.set_date(search_url, search_url2, bill_date, keyword="sms")

        # 2. 下载通话记录信息，保存至file_path
        file_name = "{tid}_sms_log_{bill_date}.xls".format(tid=self.task_id, bill_date=bill_date)
        file_path = os.path.join(self.parent_path, "output", self.task_id, file_name)
        if set_date_success:
            self.save_data(self.sms_url, file_path, keyword="sms")

        if set_date_success is False:
            self.un_success.append(("sms", bill_date))
            self.write_log(bill_date + u"不存在短信记录信息！或网络问题设置账单日期失败!")

        if set_date_success is None:
            self.un_success.append(("sms", bill_date))
            self.write_log(u"[3004] 无法设定短信记录的账单日期")
            self.write_log(u"短信记录信息获取失败!")

    def get_bills_info(self, bill_date):
        """
        爬取指定日期的历史账单
        :param bill_date: 需要爬取的月份，例："2016-05"
        :return:
        """
        self.write_log(u"开始获取历史账单信息" + bill_date + "...")
        ret_data = {}
        # 1. 检查账单日期是否是当月，如果当月，则不能查询
        if bill_date == str(datetime.date.today())[:7]:
            self.write_log(u"历史记录不能查询当月！")
            return ret_data

        search_url = "http://iservice.10010.com/e3/query/history_list.html"
        search_url2 = "http://iservice.10010.com/e3/static/query/queryHistoryBill?_={strtsmp}&menuid=000100020001"

        # 2. 设置查询的账单日期
        ret_data = self.set_date(search_url, search_url2, bill_date, keyword="bill")

        # 3. 如果设置成功，则成功，否则失败！
        if len(ret_data) > 0:
            return ret_data
        else:
            self.write_log(u"[3004] 无法设定历史账单的账单日期")
            self.write_log(u"账单历史信息获取失败!")


    def set_date(self, url, url2, bill_date, keyword):
        """
        设置查询账单的日期（不同类型的信息，传输的内容存在不同）
        :param url: 信息首页
        :param url2：设置查询时间信息首页
        :param bill_date：查询时间
        :param keyword：查询那种信息
                        'call': 通话记录
                        'sms': 短信记录
                        'net': 上网记录
                        'bill': 历史账单
        :return: None: 获取信息失败
                 False: 该月不存在要查询的信息
                 True: 获取信息成功
        """
        set_date_success = None

        current_infos = self.keyword_infos.get(keyword)
        if current_infos is None:
            self.write_log(keyword + u" -- 还不能提供该类信息的查询!")
            self.write_log(u"设置查询日期失败(查询信息类型不支持): " + str(keyword) + "!")
            return set_date_success
        else:
            self.write_log(u"尝试设置查询日期：" + str(current_infos) + "...")

        # 依次进行如下操作：
        # 1. 打开信息首页，并检验是否登录状态
        try:
            self.ses.get(url)
        except Exception as e:
            self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + str(current_infos) + " : " + url)
            self.write_log(str(e))
            return set_date_success

        if not self.check_if_login():
            self.write_log(u"在查询" + str(current_infos) + "掉出登录")
            return set_date_success

        # 2. 根据不同类型的信息，设置不同的post data
        date_list = Operator.get_begin_end_date(bill_date)
        if keyword == "call":
            post_data = {
                "pageNo": "1",
                "pageSize": "20",
                "beginDate": date_list[0],
                "endDate": date_list[1]
            }
        elif keyword == "sms":
            post_data = {
                "pageNo": "1",
                "pageSize": "20",
                "begindate": date_list[0].replace("-", ""),
                "enddate": date_list[1].replace("-", "")
            }
        elif keyword == "bill":
            post_data = {
                "querytype": "0001",
                "querycode": "0001",
                "billdate": bill_date.replace("-", "")
            }
        else:
            return None

        # 3. 传送post data到指定信息页面
        try:
            strtsmp = self.get_timestamp()
            res = self.ses.post(url2.format(strtsmp=strtsmp), data=post_data)
        except Exception as e:
            self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + str(url2))
            self.write_log(str(e))
            return set_date_success

        # 4. 检查是否成功获取指定信息：
        try:
            json_res = res.json()
        except Exception as e:
            self.write_log(u"[3003] 获得的结果不匹配！" + str(current_infos))
            self.write_log(str(e))
            return set_date_success

        # 5. 根据查询信息的类别，提取关键词信息
        if keyword == "bill":
            set_date_success = json_res.get("issuccess")
            if set_date_success is None:
                if json_res.get("historyResultState") == "success":
                    set_date_success = True
                else:
                    if json_res.get("historyResultState") is None:
                        set_date_success = None
                    else:
                        set_date_success = False

            if set_date_success is True:
                result_json = res.json().get("historyResultList")
                if result_json is None:
                    res_json = res.json().get("result")
                    if res_json is not None:
                        result_json = res_json.get("billinfo")

                if result_json is None:
                    self.write_log(u"[3003] 历史账单关键词可能已经更改")
                else:
                    return self.save_bill_info(result_json, bill_date)
        else:
            set_date_success = json_res.get("isSuccess")

        # 如果获取关键词信息失败，那么这些关键词很可能已被更换
        if set_date_success is None:
            self.write_log(u"[3003] 关键词'historyResultState/isSuccess等可能已不存在！")

        # 如果存在isSucess，且值为False，说明当月没有这类信息
        if set_date_success is False:
            self.write_log(u"当月无" + current_infos + "!" + u"或网络问题设置账单日期失败！")

        if set_date_success:
            self.write_log(u"成功设置查询时间: " + current_infos + "!")



    def save_bill_info(self, result_json, bill_date):
        """
        整理账单返回的JSON信息，保存到数据库
        :param result_json: 爬取返回的历史账单JSON（字典）
        :param bill_date: 历史账单所属的具体所属月份
        :return:
        """
        result = dict()
        result["month"] = bill_date
        result["bill_start_date"] = bill_date + "-01"
        result["bill_end_date"] = bill_date + "-" + str(calendar.monthrange(*map(int, bill_date.split("-")))[1])

        for info in result_json:
            item_name = info.get("name")
            if item_name is None:
                item_name = info.get("integrateitem")

            item_value = info.get("value")
            if item_value is None:
                item_value = info.get("fee")

            if item_name is None:
                self.logger.error(u"[3003] 历史账单返回的JSON，字段发生变化")

            if item_name.strip() == u"\u6708\u56fa\u5b9a\u8d39":  # 月固定费
                result["base_fee"] = int(float(item_value) * 100)
            elif item_name.strip() == u"\u589e\u503c\u4e1a\u52a1\u8d39":  # 增值业务费
                result["extra_service_fee"] = int(float(item_value) * 100)
            elif item_name.strip() in u"上网费":
                result["web_fee"] = int(float(item_value) * 100)
            elif item_name.strip() == u"抵扣合计":
                result["discount"] = int(float(item_value) * 100)
            elif item_name.strip() == u"实际应缴合计":
                result["actual_fee"] = int(float(item_value) * 100)
            elif item_name.strip() == u"违约金":
                result["extra_fee"] = int(float(item_value) * 100)
            else:
                continue

        if len(result) <= 3:
            return

        result["voice_fee"] = 0
        result["sms_fee"] = 0

        if result.get("web_fee") is None:
            result["web_fee"] = 0

        if result.get("extra_fee") is None:
            result["extra_fee"] = 0

        if result.get("extra_service_fee") is None:
            result["extra_service_fee"] = 0

        result["call_pay"] = (result["base_fee"] + result["extra_service_fee"] + result["voice_fee"] +
                               result["sms_fee"] + result["web_fee"] + result["extra_fee"])

        result["paid_fee"] = 0
        result["unpaid_fee"] = 0
        result["related_mobiles"] = ""


        self.write_log(u"成功获取历史账单信息!")
        return result


    def check_if_login(self):
        """
        检查是否成功登录（同时也是获取各个页面的中间必要通信环节）
        :return: True for success; False for not.
        """
        self.logger.info(u"验证是否是登录状态...")

        checkin_url = "http://iservice.10010.com/e3/static/check/checklogin?_="
        try:
            res = self.ses.post(checkin_url + Operator.get_timestamp())
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


    def save_data(self):
        pass


if __name__ == '__main__':
    unicom = Unicom('18513622865', '861357')
    # unicom.login()
    unicom.start()
    pass