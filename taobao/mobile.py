# -*- coding:utf-8 -*-
"""
File Name : 'mobile'.py
Description:
Author: 'wanglongzhen'
Date: '2016/9/5' '9:23'
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

reload(sys)
sys.setdefaultencoding("utf-8")



class TransferAccounts(object):
    def __init__(self, username = '18662726006', passwd = '526280'):
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'
        }

        #数据库连接
        # sql_pool = self.sql_connect()

        #不同类型
        self.keyword_call_type = {
            1: u"主叫",
            2: u"被叫",
        }

        self.keyword_trade_type = {
            1: u"本地",
            2: u"国内漫游",
            3: u"其他",
        }

        self.keyword_trade_away = {
            1: u"发送",
            2: u"接收",
            3: u"未知",
        }

        #selenium 登录
        self.homepage = 'http://www.10086.com'
        login_url = 'https://login.10086.cn/login.html'
        self.login_mobile(login_url, "13649258904", "728672")

    def login_mobile(self, login_url, user, passwd):
        """
        登录移动商城
        :param login_url:
        :param username:
        :param passwd:
        :return:
        """
        driver = webdriver.Firefox()
        driver.maximize_window()

        driver.delete_all_cookies()

        self.logger = comm_log.CommLog(1)
        self.logger.info(u'登录移动,用户名： ' + user + u'， 密码： ')

        driver.get(login_url)
        driver.find_element_by_id('p_name').clear()
        driver.find_element_by_id('p_name').click()
        driver.find_element_by_id('p_name').send_keys(user)
        time.sleep(2)

        driver.find_element_by_id('p_pwd').clear()
        driver.find_element_by_id('p_pwd').send_keys(passwd)
        time.sleep(2)

        try:
            element = driver.find_element_by_id('smspwdbord')

            if element.is_displayed():
                print("输入短信验证码:")
                driver.find_element_by_id('getSMSPwd').click()
                sms_id = raw_input("please input image code:")
                driver.find_element_by_id('sms_pwd').send_keys(sms_id)
            else:
                print("不需要验证码")
        except Exception, e:
            pass
        driver.find_element_by_id('submit_bt').click()

        self.waiter_fordisplayed(driver, 'divLogin')

        pass

    def waiter_fordisplayed(self, browser, element):
        count = 0
        while(True):
            count = count + 1
            if count > 20:
                return False
            try:
                ui.WebDriverWait(browser, 10).until(lambda driver : driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                pass
                print('元素没有展示' + element)
                self.logger.error(u'元素没有展示' + element)

        return True


def main():
    transfer_accounts = TransferAccounts()



if __name__ == '__main__':
    main()
    pass