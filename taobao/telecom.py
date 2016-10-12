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

            self.waiter_fordisplayed(self.driver, 'txtPassword')

            self.driver.find_element_by_id('txtPassword').send_keys(self.passwd)

            #点击登录
            self.driver.find_element_by_id('loginbtn').click()

            self.waiter_fordisplayed(self.driver, 'loginShow')

            ActionChains(self.driver).move_to_element(self.driver.find_element_by_id('vec_servpasswd')).perform()

            self.detail_url = 'http://js.189.cn/service/bill?tabFlag=billing1'
            self.ses = requests.Session()
            for cookie in self.driver.get_cookies():
                self.ses.cookies.set(cookie['name'], cookie['value'])
                self.logger.info(u'获取半年账单数据，设置请求前的cookie。 ' + cookie['name'] + ": " + cookie['value'])


        except Exception, e:
            print traceback.print_exc()
            self.track_back_err_print(sys.exc_info())


    def waiter_fordisplayed(self, browser, element):
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


if __name__ == '__main__':
    telecom = TelecomSpider('18115606158', '526280')
    telecom.login()