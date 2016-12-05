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

    def init_driver(self):
        try:
            # self.driver = webdriver.PhantomJS()
            # self.driver = webdriver.Chrome()
            self.driver = webdriver.Firefox()
            self.driver.maximize_window()

            self.driver.delete_all_cookies()
        except Exception, e:
            self.write_log(traceback.format_exc())

    def exit(self):
        if self.driver != None:
            self.driver.exit()

    def start(self):
        self.login()

        self.spider()


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
        wait = ui.WebDriverWait(self.driver, 10)
        wait.until(lambda driver: self.driver.find_element_by_class_name('mall'))

        myUnionUrl = 'https://uac.10010.com/cust/userinfo/userInfoInit'
        self.driver.get(myUnionUrl)

        if self.waiter_fordisplayed(self.driver, 'balance') == False:
            self.logger.info(u'跳转我的联通页面失败' + self.phone_num)
        else:
            self.logger.info(u'跳转我的联通页面成功' + self.phone_num)

    def save_data(self):
        pass


if __name__ == '__main__':
    unicom = Unicom('18513622865', '861357')
    unicom.login()
    pass