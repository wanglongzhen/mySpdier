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
            self.driver.quit()

    def start(self):
        self.login()

        self.spider()


    def init_cookie(self):

        self.ses = requests.session()

        print self.driver.get_cookies()
        # cookies = requests.utils.dict_from_cookiejar(self.driver.get_cookies())
        # print cookies
        for cookie in self.driver.get_cookies():

            requests.utils.add_dict_to_cookiejar(self.ses.cookies, {cookie['name']:cookie['value']})


    def login(self, img_sms = None):
        #登录
        self.init_driver()

        if self.open_login_page(self.login_url, self.phone_number, self.phone_passwd) == False:
            return 2, '登录页面加载失败'

        result, data = self.sumbit_login()
        if result == False and data != None:
            return 1, data
        elif result == False:
            return 2, '登录页面加载失败'

        self.init_cookie()

        return 0, '登录成功'


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


        #判断是否有验证码图片
        try:
            time.sleep(2)
            if self.driver.find_element_by_xpath("//img[@id='loginVerifyImg']").is_displayed():
                self.driver.maximize_window()

                element = self.driver.find_element_by_id('loginVerifyImg')
                src_file = self.phone_num + '_img.jpg'
                dst_file = self.phone_num + '_img_corp.jpg'
                # src_file = 'aaa' + 'aaaimg.jpg'
                self.driver.save_screenshot(src_file)

                location = element.location
                size = element.size
                im = Image.open(src_file)
                left = location['x']
                top = location['y']
                right = location['x'] + size['width']
                bottom = location['y'] + size['height']

                box = (left, top, right, bottom)
                im.crop(box).save(dst_file)

                f = open(dst_file, 'rb')  # 二进制方式打开图文件
                ls_f = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
                f.close()
                return False, ls_f
                # print("输入验证码")
                # self.logger.error(u'登录失败，输入验证码' + self.phone_num)
        except Exception, e:
            self.recordErrImg()
            self.logger.info(traceback.format_exc())
            print traceback.print_exc()
            print("登录成功")

        self.recordErrImg()

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

            return False, None

        self.write_log(u'登录成功')

        return True, None

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

        #个人信息
        personal_info = self.get_personal_info()

        # #账单
        # bill_info = self.get_bill_info()
        #
        # #通话
        # call_info = self.get_call_info()
        #
        # #短信
        # smss_info = self.get_smss_info()

        #存数据到数据库中\
        self.write_log(u'保存用户的信息到数据库，开始' + self.phone_number)
        if len(personal_info) > 0:
            Operator.save_basic(self, self.task_id, self.phone_number, [personal_info])
        # if len(bill_info) > 0:
        #     Operator.save_bill(self, self.task_id, self.phone_number, bill_info)
        # if len(call_info) > 0:
        #     Operator.save_calls(self, self.task_id, self.phone_number, call_info)
        # if len(smss_info) > 0:
        #     Operator.save_sms(self, self.task_id, self.phone_number, smss_info)

        self.write_log(u'保存用户的信息到数据库，完成。 ' + self.phone_number)

        self.exit()


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
        # result["state"] = -1
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


        for bill_date in bill_date_list[:-1]:
            ret = self.get_bill_by_month(bill_date)
            bill_info.append(ret)

        return bill_info


    def get_bill_by_month(self, bill_date):
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


    def get_smss_info(self):
        bill_info = list()
        today = datetime.date.today()
        bill_date_list = list(map(lambda delta: str(today + relativedelta(months=delta))[:7], range(-6, 1, 1)))

        smss_list = []
        for bill_date in bill_date_list[1:]:
            smss_list.extend(self.get_smss_by_month(bill_date))

        return smss_list

    def get_call_info(self):
        bill_info = list()
        today = datetime.date.today()
        bill_date_list = list(map(lambda delta: str(today + relativedelta(months=delta))[:7], range(-6, 1, 1)))

        call_list = []
        for bill_date in bill_date_list[1:]:
            call_list.extend(self.get_call_by_month(bill_date))

        return call_list

    def get_call_by_month(self, bill_date):
        """
        爬取指定日期的通话记录
        :param bill_date: 需要爬取的月份，例："2016-05"
        :return:
        """
        self.write_log(u"开始爬取通话记录: " + bill_date + "...")

        search_url = "http://iservice.10010.com/e3/query/call_dan.html"
        search_url2 = "http://iservice.10010.com/e3/static/query/callDetail?_={strtsmp}&menuid=000100030001"

        # 1. 设置查询的账单日期
        call_list = self.get_call_by_month_detail(search_url, search_url2, bill_date)

        if len(call_list) == 0:
            call_list = self.get_call_by_month_detail(search_url, search_url2, bill_date)
        return call_list

    def get_call_by_month_detail(self, check_url, url, bill_date):

        self.write_log(u"请求通话记录， 查询月份： " + str(bill_date))
        self.write_log(u"尝试设置查询日期：通话记录...")

        call_list = []
        # 依次进行如下操作：
        # 1. 打开信息首页，并检验是否登录状态
        try:
            self.ses.get(check_url)
        except Exception as e:
            self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + url)
            self.write_log(str(e))

        if not self.check_if_login():
            self.write_log(u"在查询 通话记录 掉出登录")

        # 2. 根据不同类型的信息，设置不同的post data
        date_list = Operator.get_begin_end_date(bill_date)

        page_no = 1
        post_data = {
            "pageNo": page_no,
            "pageSize": "20",
            "beginDate": date_list[0],
            "endDate": date_list[1]
        }

        try:
            strtsmp = self.get_timestamp()
            res = self.post(url.format(strtsmp=strtsmp), post_data=post_data)
            call_list.extend(self.get_call_by_page_detail(res.json()))
            self.write_log(u"查询数据" + str(bill_date) + "月, 查询第1页...")
        except Exception as e:
            self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + str(url))
            self.write_log(str(e))

        # 4. 检查是否成功获取指定信息：
        try:
            json_res = res.json()
            page_map = json_res.get('pageMap')
            if page_map != None:
                total_pages = page_map.get('totalPages')
                page_no = int(page_map.get('pageNo'))

                for page in range(2, total_pages):
                    try:
                        post_data['pageNo'] = str(page)
                        strtsmp = self.get_timestamp()
                        # res = self.ses.post(url.format(strtsmp=strtsmp), data=post_data)
                        res = self.post(url.format(strtsmp=strtsmp), post_data=post_data)
                        call_list.extend(self.get_call_by_page_detail(res.json()))
                        self.write_log(u"查询数据" + str(bill_date) + "月, 查询第" + str(page) + "页...， 总数据页数： " + str(total_pages))
                    except Exception as e:
                        self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + str(url))
                        self.write_log(u"查询数据失败， " + str(bill_date) + "月, 查询第" + str(page) + "页...， 总数据页数： " + str(total_pages))
                        self.write_log(traceback.format_exc())


            self.write_log(u"请求通话记录成功， 查询月份： " +  str(bill_date))
        except Exception as e:
            self.write_log(u"[3003] 获得的结果不匹配！通话记录 " )
            self.write_log(str(e))

        return call_list

    def get_smss_by_month(self, bill_date):
        """
        爬取指定日期的短信记录
        :param bill_date: 需要爬取的月份，例："2016-05"
        :return:
        """
        self.write_log(u"开始爬取短信记录" + bill_date + "...")

        search_url = "http://iservice.10010.com/e3/query/call_sms.html"
        search_url2 = "http://iservice.10010.com/e3/static/query/sms?_={strtsmp}&menuid=000100030002"

        # 1. 设置查询的账单日期
        smss_list = self.get_smss_by_month_detail(search_url, search_url2, bill_date)
        if len(smss_list) == 0:
            smss_list = self.get_smss_by_month_detail(search_url, search_url2, bill_date)
        return smss_list


    def get_smss_by_month_detail(self, check_url, url, bill_date):
        self.write_log(u"开始请求短信记录， 查询月份： " + str(bill_date))
        self.write_log(u"尝试设置查询日期：短信记录...")

        smss_list = []
        # 依次进行如下操作：
        # 1. 打开信息首页，并检验是否登录状态
        try:
            self.ses.get(check_url)
        except Exception as e:
            self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + url)
            self.write_log(str(e))

        if not self.check_if_login():
            self.write_log(u"在查询 短信记录 掉出登录")

        # 2. 根据不同类型的信息，设置不同的post data
        date_list = Operator.get_begin_end_date(bill_date)

        page_no = 1
        post_data = {
            "pageNo": "1",
            "pageSize": "20",
            "begindate": date_list[0].replace("-", ""),
            "enddate": date_list[1].replace("-", "")
        }


        try:
            strtsmp = self.get_timestamp()
            res = self.post(url.format(strtsmp=strtsmp), post_data=post_data)
            smss_list.extend(self.get_smss_by_page_detail(res.json()))
            self.write_log(u"查询数据" + str(bill_date) + "月, 查询第1页...")
        except Exception as e:
            self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + str(url))
            self.write_log(str(e))

        # 4. 检查是否成功获取指定信息：
        try:
            json_res = res.json()
            page_map = json_res.get('pageMap')
            if page_map != None:
                total_pages = page_map.get('totalPages')
                page_no = int(page_map.get('pageNo'))

                for page in range(2, total_pages):
                    try:
                        post_data['pageNo'] = str(page)
                        strtsmp = self.get_timestamp()
                        res = self.post(url.format(strtsmp=strtsmp), post_data=post_data)
                        smss_list.extend(self.get_smss_by_page_detail(res.json()))
                        self.write_log(u"查询数据" + str(bill_date) + "月, 查询第" + str(page) + "页...， 总数据页数： " + str(total_pages))
                    except Exception as e:
                        self.write_log(u"[3002] 无法打开查询网页(设置查询日期): " + str(url))
                        self.write_log(
                            u"查询数据失败， " + str(bill_date) + "月, 查询第" + str(page) + "页...， 总数据页数： " + str(total_pages))
                        self.write_log(traceback.format_exc())

            self.write_log(u"请求短信记录成功， 查询月份： " + str(bill_date))
        except Exception as e:
            self.write_log(u"[3003] 获得的结果不匹配！短信记录 ")
            self.write_log(str(e))

        return smss_list

    def get_smss_by_page_detail(self, json_data):
        ret = list()
        page_map = json_data.get('pageMap')
        if page_map != None:
            result = page_map.get('result')
            for call_item in result:
                ret_call = dict()
                ret_call['mobile'] = str(self.phone_number)
                ret_call['send_time'] = call_item['smsdate'] + ' ' + call_item['smstime']
                ret_call['receive_phone'] = call_item['othernum']
                if call_item['smstype'] == '1':
                    ret_call['trade_way'] = '发送'
                if call_item['smstype'] == '2':
                    ret_call['trade_way'] = '接收'
                ret.append(ret_call)

        return ret

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
        post_data = {
            "querytype": "0001",
            "querycode": "0001",
            "billdate": bill_date.replace("-", "")
        }

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
            if set_date_success is True:
                result_json = res.json().get("historyResultList")
                if result_json is None:
                    res_json = res.json().get("result")
                    if res_json is not None:
                        result_json = res_json.get("billinfo")
                        return self.get_bill_by_month_detail(result_json, bill_date)

        # # 如果获取关键词信息失败，那么这些关键词很可能已被更换
        # if set_date_success is None:
        #     self.write_log(u"[3003] 关键词'historyResultState/isSuccess等可能已不存在！")
        #
        # # 如果存在isSucess，且值为False，说明当月没有这类信息
        # if set_date_success is False:
        #     self.write_log(u"当月无" + current_infos + "!" + u"或网络问题设置账单日期失败！")
        #
        # if set_date_success:
        #     self.write_log(u"成功设置查询时间: " + current_infos + "!")


    def get_call_by_page_detail(self, json_data):
        ret = list()
        page_map = json_data.get('pageMap')
        if page_map != None:
            result = page_map.get('result')
            for call_item in result:
                ret_call = dict()
                ret_call['mobile'] = str(self.phone_number)
                ret_call['call_type'] = call_item['calltypeName']
                ret_call['call_time'] = call_item['calldate'] + ' ' + call_item['calltime']
                ret_call['receive_phone'] = call_item['othernum']
                ret_call['trade_time'] = call_item['calllonghour']
                ret_call['trade_type'] = call_item['landtype']
                ret_call['trade_addr'] = call_item['homeareaName']

                ret.append(ret_call)

        return ret

    def get_bill_by_month_detail(self, result_json, bill_date):
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


    def post(self, url, post_data):
        return self.ses.post(url, post_data)

    def get(self, url):
        return self.ses.post(url)

    def save_data(self):
        pass


if __name__ == '__main__':
    unicom = Unicom('18513622865', '861357')
    # unicom.login()
    unicom.start()
    pass