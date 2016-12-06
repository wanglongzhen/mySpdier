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
            self.driver.exit()

    def start(self):
        self.login()

        self.init_cookie()

        self.spider()

    def init_cookie(self):
        cks = {}
        for cookie in self.driver.get_cookies():
            cks[cookie['name']] = cookie['value']

            requests.utils.add_dict_to_cookiejar(self.ses, {cookie['name']:cookie['value']})

        print "dd"

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

            self.logger.info(u'输入用户名： ' + phone_number)

            self.driver.find_element_by_xpath("//input[@id='userPwd']").clear()
            self.driver.find_element_by_xpath("//input[@id='userPwd']").send_keys(phone_passwd)

            self.logger.info(u'输入密码： ' + phone_passwd)
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
                self.logger.info(traceback.format_exc())
            try:
                message = self.driver.find_element_by_xpath('//span[@class="error left mt10mf32"]').text
            except:
                self.recordErrImg()
                self.logger.info(traceback.format_exc())

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
        self.get_personal_info()


    def get_personal_infos(self):
        """
        获取账号基本信息
        :return:
        """
        # 1. 获取个人基本信息
        checkin_url = "http://iservice.10010.com/e3/static/check/checklogin?_="
        try:
            res = self.ses.post(checkin_url + Operator.get_timestamp())
        except Exception as e:
            self.logger.error(u"[3002] 无法发送获取登录状态的请求" + str(checkin_url))
            self.logger.error(str(e))
            return False

        try:
            res_json = res.json().get("userInfo")
        except Exception as e:
            self.logger.error(u"[3003] 用户基本信息(userInfo)返回内容异常")
            self.logger.error(str(e))
            return False

        # 2. 获取余额以及最近更新时间
        try:
            self.ses.get(self.user_info)
            res2 = self.ses.post(self.user_json)
        except Exception as e:
            self.logger.error(u"[3002] 无法打开账户信息页面" + str(self.user_json))
            self.logger.error(str(e))
            return False

        try:
            res2_json = res2.json().get("defBindnumInfo").get("costInfo")
        except Exception as e:
            self.logger.error(u"[3003] 账户信息页面(costInfo)返回内容异常")
            self.logger.error(str(e))
            res2_json = None

        # 3. 整理结果
        open_time = res_json.get("opendate")
        if open_time is None:
            try:
                open_time = res2.json().get("defBindnumInfo").get("mydetailinfo").get("opendate")
            except Exception as e:
                self.logger.error(u"[3003] 账户信息页面返回内容异常")
                self.logger.error(str(e))
                open_time = ""
            else:
                open_time = open_time.replace(u"年", "-").replace(u"月", "-").replace(u"日", "").strip()
        else:
            open_time = open_time[:4] + '-' + open_time[4:6] + '-' + open_time[6:8]

        result = dict()
        result["name"] = res_json.get("custName")
        result["carrier"] = "CHINA_UNICOM"
        result["level"] = res_json.get("vip_level")
        result["state"] = -1
        result["open_time"] = open_time
        result["package_name"] = res_json.get("packageName")

        if result["level"] is None:
            try:
                res = self.ses.post("https://uac.10010.com/cust/userinfo/userInfo")
                level_json = res.json()
            except Exception as e:
                self.logger.error(u"[3002] 无法获取用户VIP等级")
                result["level"] = ""
                self.logger.error(str(e))
            else:
                result["level"] = level_json.get("vipLevel")

        if result["level"] is None:
            result["level"] = ""

        if res2_json is not None:
            try:
                result["available_balance"] = int(float(res2_json.get("balance")) * 100)
            except Exception as e:
                self.logger.error(u"[3003] 获取的账户余额数值异常: " + str(res2_json.get("balance")))
                self.logger.error(str(e))
                result["available_balance"] = None
        else:
            result["available_balance"] = None
        result["last_modify_time"] = ""

        if result["available_balance"] is None:
            result["available_balance"] = ''

        # 获取归属地
        try:
            result["province"], result["city"] = location_scrape(self.phone)
        except Exception as e:
            self.logger.error(u"[3004] 获取号码归属地的程序出现异常")
            self.logger.error(str(e))
            result["province"], result["city"] = ["", ""]

        file_name = "{tid}_basic.json".format(tid=self.task_id)
        file_path = os.path.join(self.parent_path, "output", self.task_id, file_name)

        # with open(file_path, "wb") as f:
        #     json.dump(result, f)

        return True

    def save_data(self):
        pass


if __name__ == '__main__':
    unicom = Unicom('18513622865', '861357')
    # unicom.login()
    unicom.start()
    pass