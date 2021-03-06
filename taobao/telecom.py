# -*- coding:utf-8 -*-
"""
File Name : 'telecom'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/10/12' '10:04'
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
import json

from union import Union
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import requests

import traceback
import datetime
from dateutil.relativedelta import relativedelta
import calendar

reload(sys)
sys.setdefaultencoding("utf-8")

from union import Union



class TelecomSpider(Union):
    def __init__(self, username, passwd):
        Union.__init__(self, username)
        self.task_id = Union.get_task_no(self, username)
        self.phone_num = str(username)
        self.passwd = passwd

        self.homepage = 'http://ww.189.cn'
        self.login_url = 'http://login.189.cn/login'

        # self.driver = webdriver.PhantomJS()
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.ses = requests.session()

        #账单日期
        self.bill_date_list = TelecomSpider.get_bill_date_list()



    def __exit__(self, exc_type, exc_val, exc_tb):
        Union.__exit__(self.exc_type, exc_val, exc_tb)

    def login(self):

        try:
            #打开登录页面
            self.driver.get(self.login_url)

            #用户名
            self.driver.find_element_by_id('txtAccount').clear()
            self.driver.find_element_by_id('txtAccount').send_keys(self.phone_num)

            #登录密码
            # self.driver.find_element_by_id('txtShowPwd').clear()
            self.driver.find_element_by_id('txtShowPwd').click()

            self.waiter_for_displayed_id(self.driver, 'txtPassword')

            self.driver.find_element_by_id('txtPassword').send_keys(self.passwd)

            #点击登录
            self.driver.find_element_by_id('loginbtn').click()

            self.waiter_for_displayed_id(self.driver, 'tologinId')

            #抓电话信息
            self.get_call_detail()

            self.get_sms_datail()

            # #跳转后确实当前的TAB页为清单查询页
            # if self.waiter_for_displayed_id(self.driver, 'billing2') == False:
            #     self.logger(u'tab页清单查询没有加载成功')
            # self.driver.find_element_by_id('billing2').click()
            #
            # self.waiter_for_displayed_id(self.driver, 'orderListId')
            # self.driver.find_element_by_id('billing2').find_element_by_xpath('//option[@value="1"]').click()
            # self.driver.find_element_by_id('queryId').click()

        except Exception, e:
            print traceback.print_exc()
            self.track_back_err_print(sys.exc_info())

    def get_sms_detail(self):
        # 取短信的内容
        self.driver.find_element_by_id('uniMsgDiv')

        #取短信数据
        self.driver.find_element_by_id('messgeTable')


    def get_call_detail(self):
            #移动到业务btn下
            # ActionChains(self.driver).move_to_element(self.driver.find_element_by_xpath('//li[@class="down_05"]')).perform()

            self.detail_url = 'http://js.189.cn/service/bill?tabFlag=billing4'
            self.ses = requests.Session()
            print self.driver.get_cookies()
            for cookie in self.driver.get_cookies():
                self.ses.cookies.set(cookie['name'], cookie['value'])
                self.logger.info(u'获取半年账单数据，设置请求前的cookie。 ' + cookie['name'] + ": " + cookie['value'])

            # 登录成功后的操作，取用户的话单和基本信息
            # 找到页面中详单查询的URL，然后跳转
            detail_url = self.driver.find_element_by_xpath('//span[@class="span_font_a"]/a[text()="上网详单"]').get_attribute(
                'href')
            self.driver.get(detail_url)

            self.waiter_for_displayed_id(self.driver, 'orderListId')

            if self.waiter_for_displayed_xpath(self.driver, '//select[@id="orderListId"]/option[@value="1"]') == False:
                self.logger.info(u'没有找到元素' + '//select[@id="orderListId"]/option[@value="1"]')

            #1通话
            #2短信
            self.driver.find_element_by_xpath('//select[@id="orderListId"]/option[@value="1"]').click()

            #查询条件输入提示
            if self.waiter_for_displayed_id('searchget') == True:
                self.logger.info(u'页面加载完毕，提示输入查询条件，查询详细信息')
            else:
                self.logger.info(u'没有出现输入查询条件的DIV，错误')

            #循环6个月的日期
            for begin, end in self.bill_date_list:
                print begin, end

            #开始查询
            if self.waiter_for_displayed_id(self.driver, 'queryId') == False:
                self.logger.info(u'queryId 没有加载，错误')
            self.driver.find_element_by_id('queryId').click()


            #错误展示div
            if self.waiter_for_displayed_id('errorShow') == True:
                self.logger.info(u'页面加载完毕，提示输入查询条件，查询详细信息')

            #数据div
            if self.waiter_for_displayed_id('messgeDiv') == True:
                self.logger.info(u'话单数据加载完毕')

            #取语音清单内容
            self.driver.find_element_by_id('vDiv')


            self.waiter_for_displayed_id(self.driver, 'vDiv')


    def waiter_for_displayed_xpath(self, browser, selector):
        count = 0
        while (True):
            count = count + 1
            if count > 2:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver: driver.find_element_by_xpath(selector))
                break
            except Exception, e:
                pass
                print('元素没有展示' + selector)
                self.logger.error(u'元素没有展示' + selector)

        return True

    def waiter_for_displayed_id(self, browser, element):
        count = 0
        while (True):
            count = count + 1
            if count > 2:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver: driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                pass
                print('元素没有展示' + element)
                self.logger.error(u'元素没有展示' + element)

        return True


    def waiter_for_not_displayed_id(self, browser, element):
        count = 0
        while (True):
            count = count + 1
            if count > 2:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver: not driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                pass
                print('元素仍然展示' + element)
                self.logger.error(u'元素仍然展示' + element)

        return True

    @staticmethod
    def get_bill_date_list():
        today = datetime.date.today()
        bill_date_list = list(map(lambda delta: str(today + relativedelta(months=delta))[:7], range(-6, 1, 1)))

        bill_date_tuple = []
        for date in bill_date_list:
            month_bill_date_tuple = TelecomSpider.get_begin_end_date(date)
            bill_date_tuple.append(month_bill_date_tuple)

        return bill_date_tuple

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


if __name__ == '__main__':
    telecom = TelecomSpider('18115606158', '526280')
    telecom.login()