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
import json

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import traceback

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

        self.logger = comm_log.CommLog(1)

        # self.driver = webdriver.Firefox()
        # self.driver = webdriver.PhantomJS()

        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        # self.driver.delete_all_cookies()

        #selenium 登录
        self.homepage = 'http://www.10086.com'
        # login_url = 'https://login.10086.cn/html/login/login.html'
        # login_url = 'https://login.10086.cn/login.html'
        # login_url = 'https://login.10086.cn/html/login/login.html?channelID=12002&backUrl=http%3A%2F%2Fshop.10086.cn%2Fmall_290_290.html%3Fforcelogin%3D1'
        login_url = 'https://login.10086.cn/login.html?channelID=12003&backUrl=http://shop.10086.cn/i/'
        # login_url = 'https://www.10086.cn'
        self.login_mobile(login_url, "13649258904", "728672")



    def login_mobile(self, login_url, user, passwd):
        """
        登录移动商城
        :param login_url:
        :param username:
        :param passwd:
        :return:
        """

        #鼠标移动到登录入口
        # self.driver.get(login_url)
        #
        # ActionChains(self.driver).move_to_element(self.driver.find_element_by_id('dropdownMenu2')).perform()
        # self.logger.info(u'鼠标移动到登录坐标附近')
        # ActionChains(self.driver).move_to_element(self.driver.find_element_by_id('loginYDSC')).perform()
        # self.logger.info(u'鼠标移动到登录网上商城')
        #
        # self.waiter_fordisplayed(self.driver, 'loginYDSC')
        #
        # self.driver.find_element_by_id('loginYDSC').click()
        # self.logger.info(u'点击移动商城入口，登录移动商城' + user)


        self.driver.get(login_url)
        self.logger.info(u'登录移动,用户名： ' + user + u'， 密码： ')

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
        time.sleep(5)
        self.get_call_detail(user, passwd)

    def get_call_detail(self, user, passwd):
        """
        获取用户的半年通话详单
        :param user:
        :param passwd:
        :return:
        """
        self.trigger_call_detail_sms(user, passwd)

    def get_call_detail_from_month(self, li, page_source, call_list):
        """

        :param page_source:
        :param call_list:
        :return:
        """

        while (True):
            try:
                call_list = []
                self.get_call_detail_from_month_sub_page(page_source, call_list)

                self.logger.info(li.text + u'月，通话详单：当前页的数据抓取完成')
                self.logger.info(li.text + u'月，通话详单：当前页码' + self.driver.find_element_by_id(
                    'page-demo').find_element_by_xpath('//a[@class="gs-page on"]').text)

                if EC.element_to_be_clickable((By.XPATH, '//div[@id="page-demo"]//a[@class="next"]')):

                    m = re.match('.*(\d+)/(\d+).*', self.driver.find_element_by_id('notes1').text)
                    if m:
                        curr_page = long(m.group(1))
                        total_page = long(m.group(2))
                        if curr_page == total_page:
                            print('到尾页')
                            self.logger.info(li.text + u'月, 通话详单，已经到最后一页')
                            break
                        else:
                            self.driver.find_element_by_xpath(
                                '//div[@id="page-demo"]//a[@class="next"]').click()
                            self.logger.info(li.text + u'月, 通话详单，加载下一页')
                    else:
                        print(u'没有匹配')
                        self.logger.info(li.text + u'月, 通话详单，正则查找当前页和总页数出错，没有匹配到结果')

                else:
                    self.logger.info(li.text + u'月, //div[@id="page-demo"]//a[@class="next"] 不能点击')
                    break

                self.logger.info(li.text + u'月，通话详单：下一页数据加载完成')
            except Exception, e:
                print e
                traceback.print_exc()

                self.logger.info(li.text + u'月，通话详单：没有找到下一页')
                break

    def get_call_detail_from_month_sub_page(self, page_source, call_list):
        """
        获取记录中每条记录
        :param page_source:
        :param call_list:
        :return:
        """
        soup = bs(page_source)
        call_list_tag = [item for item in soup.find('table', id='tmpl-data').find('tbody').find_all('tr')]
        call_list = []
        call_detail_list = {}
        try:
            for call in call_list_tag:
                call_detail = [item.text for item in call.find_all('td')]
                call_detail_list['call_time'] = call_detail[0]
                call_detail_list['call_type'] = call_detail[2]
                call_detail_list['receive_phone'] = call_detail[3]
                call_detail_list['trade_addr'] = call_detail[1]
                call_detail_list['trade_time'] = call_detail[4]
                call_detail_list['trade_type'] = call_detail[5]
                self.logger.info(u'下载通话详单 ' + str(call_detail_list))
                call_list.append(call_detail_list)
        except Exception, e:
            pass


    def trigger_call_detail_sms(self, user, passwd):
        """
        触发用户详单的短信验证
        :return:
        """

        #触发第二次验证码
        try:

            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "我的账户")]')))
        except Exception, e:
            print e

        for item in self.driver.find_elements_by_xpath('//ul[@class="list-c1 js_list_active"]'):
            if u'我的账户' in item.text:
                item.click()
                self.logger.info(u'移动，详单查询，点击' + item.text)
                print('点击我的账户')
            else:
                self.logger.info(u'移动，详单查询，跳转过程中...' + item.text)
                print('点解' + item.text)

        wait = WebDriverWait(self.driver, 10)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@alis="billdetailqry"]')))
        self.driver.find_element_by_xpath('//a[@alis="billdetailqry"]').click()

        self.logger.info(u'移动，详单查询，点击详单查询')

        wait = WebDriverWait(self.driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@eventcode="UCenter_billdetailqry_type_THXD"]')))

        self.driver.find_element_by_xpath('//li[@eventcode="UCenter_billdetailqry_type_THXD"]').click()
        self.logger.info(u'移动，登录后，点击通话详单tab页，查询用户通话详单')

        for li in self.driver.find_elements_by_xpath('//ul[@id="month-data"]//li[starts-with(@id, "month")]'):
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except Exception, e:
                print("not has alert")
                pass

            self.logger.info(u'移动，查询详单,点击' + li.text)
            li.click()
            time.sleep(2)

            try:
                if self.driver.find_element_by_xpath('//div[starts-with(@id, "content")]').is_displayed() \
                            or self.driver.find_element_by_id('stc-send-sms').is_displayed():
                    ActionChains(self.driver).move_to_element(self.driver.find_element_by_id('vec_servpasswd')).perform()
                    self.logger.info(u'移动->查询详单->移动到服务密码输入框')

                    self.driver.find_element_by_id('vec_servpasswd').clear()
                    self.driver.find_element_by_id('vec_servpasswd').send_keys(passwd)
                    time.sleep(1)

                    aa = self.driver.find_element_by_id('stc-jf-sms-count').text

                    #触发二次验证码
                    time.sleep(40)
                    for cookie in self.driver.get_cookies():
                        if cookie['name'] == 'ss':
                            tt = cookie['value']
                            linux_time = long(tt) / 1000

                    self.driver.find_element_by_id('stc-send-sms').click()
                    time.sleep(2)

                    #处理弹出的模态对话框
                    try:
                        alert = self.driver.switch_to.alert
                        alert.accept()
                    except Exception, e:
                        print e

                    cookies_str = json.dumps(self.driver.get_cookies())
                    self.logger.info(u'移动->查询详单->点击获取查询详单的短信验证码' + cookies_str)

                    stc_sms_id = raw_input("please input image code:")
                    self.logger.info(u'移动->查询详单->输入详单查询短信随机码')

                    self.driver.find_element_by_id('vec_smspasswd').send_keys(stc_sms_id)

                    self.driver.find_element_by_id('vecbtn').click()

                    #处理弹出的dialog对话框
                    # try:
                    #     wait = WebDriverWait(self.driver, 10)
                    #     wait.until(EC.staleness_of((By.XPATH, '//div[@i="dialog"]')))
                    # except Exception, e:
                    #     print("dialog,没有被移除")
                    #     err_msg = self.driver.find_element_by_xpath('//span[contains(text(), "认证失败")]').text
                    #     wait = WebDriverWait(self.driver, 60)
                    #     element = wait.until(EC.element_to_be_clickable((By.ID, 'stc-send-sms')))
                    #
                    #     self.logger.info(u'移动->查询详单->详单查询，登录认证失败，重新触发')
                    #     print e
                    #     continue

                    #等待页面加载通话记录完成
                    self.logger.info(u'移动，查询详单,触发再次登录验证对话框')

            except Exception, e:
                print e

                print traceback.print_exc()

            try:
                #等待数据加载完成
                wait = WebDriverWait(self.driver, 10)
                wait.until(EC.element_to_be_clickable((By.XPATH, '//table[@id="tmpl-data"]//thead')))
            except Exception, e:
                print e
                traceback.print_exc()

            self.logger.info(u'移动，查询详单,开始爬取详单，' + li.text)

            # 取数据
            self.get_call_detail_from_month(li, self.driver.page_source, user)


    def waiter_for_displayed_by_xpath(self, browser, regex):
        count = 0
        while(True):
            count = count + 1
            if count > 2:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver : driver.find_element_by_xpath(regex).is_displayed())
                break
            except Exception, e:
                pass
                print('元素没有展示' + regex)
                self.logger.error(u'元素没有展示' + regex)

        return True


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
    try:
        transfer_accounts = TransferAccounts()
    except Exception, e:
        print e
        print traceback.print_exc()



if __name__ == '__main__':
    main()
    pass