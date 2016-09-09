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
    def __init__(self, username = '13720257610', passwd = '883515'):
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

        self.driver = webdriver.Firefox()
        self.driver.maximize_window()
        self.driver.delete_all_cookies()

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

        self.logger = comm_log.CommLog(1)
        self.logger.info(u'登录移动,用户名： ' + user + u'， 密码： ')

        self.driver.get(login_url)
        self.driver.find_element_by_id('p_name').clear()
        self.driver.find_element_by_id('p_name').click()
        self.driver.find_element_by_id('p_name').send_keys(user)
        time.sleep(2)

        self.logger.info(u'登录移动,填充手机号，用户名： ' + user + u'， 密码： ')

        self.driver.find_element_by_id('p_pwd').clear()
        self.driver.find_element_by_id('p_pwd').send_keys(passwd)
        time.sleep(2)
        self.logger.info(u'登录移动,填充服务密码，用户名： ' + user + u'， 密码： ')

        try:
            element = self.driver.find_element_by_id('smspwdbord')

            if element.is_displayed():
                print("输入短信验证码:")
                self.driver.find_element_by_id('getSMSPwd').click()
                sms_id = raw_input("please input image code:")
                self.driver.find_element_by_id('sms_pwd').send_keys(sms_id)
                self.logger.info(u'登录移动,填充短信验证码，用户名： ' + user + u'， 密码： ')
            else:
                print("不需要验证码")
        except Exception, e:
            pass
        self.driver.find_element_by_id('submit_bt').click()
        self.logger.info(u'登录移动,点击登录，用户名： ' + user + u'， 密码： ')


        if not self.waiter_fordisplayed(self.driver, 'divLogin') :
            self.logger.info(u'登录移动，超时失败' + user)
            self.driver.refresh()

        if not self.waiter_fordisplayed(self.driver, 'stc_myaccount'):
            self.logger.info(u'登录移动，超时失败' + user)
            self.driver.refresh()

        self.logger.info(u'登录移动,完成登录，用户名： ' + user + u'， 密码： ')

        #获取半年通话详单
        self.get_call_detail(user, passwd)

    def get_call_detail(self, user, passwd):
        """
        获取用户半年通话详单
        :return:
        """
        for item in self.driver.find_elements_by_xpath('//ul[@class="list-c1 js_list_active"]'):
            if u'我的账户' in item.text:
                item.click()
                self.logger.info(u'移动，详单查询，点击' + item.text)
            else:
                self.logger.info(u'移动，详单查询，跳转过程中...' + item.text)

        # self.driver.find_element_by_xpath('//ul[@class="list-c1 js_list_active"]').click()
        self.driver.find_element_by_xpath('//a[@alis="billdetailqry"]').click()
        self.logger.info(u'移动，详单查询，点击详单查询')

        time.sleep(2)
        self.driver.find_element_by_xpath('//li[@eventcode="UCenter_billdetailqry_type_THXD"]').click()
        self.logger.info(u'移动，详单查询，点击通话详单查询tab')
        for li in self.driver.find_elements_by_xpath('//ul[@id="month-data"]//li[starts-with(@id, "month")]'):
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except Exception, e:
                print("not has alert")
                pass

            self.logger.info(u'移动，查询详单,点击' + li.text)
            li.click()
            time.sleep(20)

            while(True):
                if self.driver.find_element_by_xpath('//div[starts-with(@id, "content")]').is_displayed()\
                        or self.driver.find_element_by_id('stc-send-sms').is_displayed():

                    try:

                        self.driver.find_element_by_id('stc-send-sms').click()
                        try:
                            alert = self.driver.switch_to.alert
                            alert.accept
                        except Exception, e:
                            print e

                        aa = self.driver.find_element_by_id('stc-jf-sms-count').text

                        stc_sms_id = raw_input("please input image code:")
                        self.logger.info(u'移动->查询详单->输入详单查询短信随机码')

                        self.driver.find_element_by_id('vec_servpasswd').clear()
                        self.driver.find_element_by_id('vec_servpasswd').send_keys(passwd)

                        self.driver.find_element_by_id('vec_smspasswd').send_keys(stc_sms_id)

                        self.driver.find_element_by_id('vecbtn').click()

                        self.logger.info(u'移动->查询详单->详单查询，点击认证登录')

                        self.logger.info(u'移动，查询详单,触发再次登录验证对话框')


                    except Exception, e:
                        print e
                        alert = self.driver.switch_to.alert
                        alert.accept()

                        pass
                else:
                    self.logger.info(u'移动，查询详单,开始爬取详单')

                #test
                li.click()


        pass

    def waiter_fordisplayed(self, browser, element):
        count = 0
        while(True):
            count = count + 1
            if count > 2:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver : driver.find_element_by_id(element).is_displayed())
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