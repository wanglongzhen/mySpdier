# -*- coding:utf-8 -*-
"""
File Name : 'mobileSpider'.py 
Description:
Author: 'wanglongzhen' 
Date: '2016/9/26' '9:14'
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



class MobileSpider(Union):
    def __init__(self, username, passwd):
        print 'MobileSpider init'
        Union.__init__(self, username)
        self.task_id = Union.get_task_no(self, username)
        self.phone_num = str(username)
        self.passwd = passwd

        self.homepage = 'http://www.10086.com'
        self.login_url = 'https://login.10086.cn/login.html?channelID=12003&backUrl=http://shop.10086.cn/i/'
        #
        self.driver = webdriver.PhantomJS()

        # self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.ses = requests.session()



    def __exit__(self, exc_type, exc_val, exc_tb):
        Union.__exit__(self.exc_type, exc_val, exc_tb)

    def login(self):
        try:
            self.driver.get(self.login_url)
            self.logger.info(u'登录移动,用户名： ' + self.phone_num + u'， 密码： ')

            self.driver.find_element_by_id('p_name').clear()
            self.driver.find_element_by_id('p_name').click()
            self.driver.find_element_by_id('p_name').send_keys(self.phone_num)

            self.logger.info(u'登录移动,填充手机号，用户名： ' + self.phone_num + u'， 密码： ')

            self.driver.find_element_by_id('p_pwd').clear()
            self.driver.find_element_by_id('p_pwd').send_keys(self.passwd)
            time.sleep(2)
            self.logger.info(u'登录移动,填充服务密码，用户名： ' + self.phone_num + u'， 密码： ')
        except Exception, e:
            return False, u'登录页面加载失败'

        try:
            element = self.driver.find_element_by_id('smspwdbord')

            if element.is_displayed():
                print("输入短信验证码:")
                self.driver.find_element_by_id('getSMSPwd').click()
                self.logger.info(u'登录移动,触发登录短信验证码，用户名： ' + self.phone_num + u'， 密码： ')
            else:
                print("不需要验证码")
        except Exception, e:
            return False, u'登录验证码点击失败'
        return True, u'触发登录验证码成功'



    def login_first_sms(self, sms):
        self.driver.find_element_by_id('sms_pwd').send_keys(sms)
        self.logger.info(u'登录移动,填充短信验证码，用户名： ' + self.phone_num + u'， 密码： ')

        self.driver.find_element_by_id('submit_bt').click()
        self.logger.info(u'登录移动,点击登录，用户名： ' + self.phone_num + u'， 密码： ')

        if not self.waiter_fordisplayed(self.driver, 'divLogin') or not self.waiter_fordisplayed(self.driver, 'stc_myaccount'):
            message = ""
            try:
                msg = self.driver.find_element_by_id('phonepwd_error').text
                if msg != u'':
                    message = msg
            except:
                pass
            try:
                msg = self.driver.find_element_by_id('smspwd_error').text
                if msg != u'':
                    message = msg
            except:
                pass
            try:
                msg = self.driver.find_element_by_id('phone_error').text
                if msg != u'':
                    message = msg
            except:
                pass

            self.logger.info(u'登录移动，超时失败' + self.phone_num)
            self.driver.refresh()

            # 登录失败，重新触发验证码
            try:
                element = self.driver.find_element_by_id('smspwdbord')
                if element.is_displayed():
                    print("输入短信验证码:")
                    self.driver.find_element_by_id('getSMSPwd').click()
                else:
                    print("不需要验证码")
            except Exception, e:
                return False, u'登录验证码点击失败。 ' + message

            return False, message
        #
        # if not self.waiter_fordisplayed(self.driver, 'stc_myaccount'):
        #     self.logger.info(u'登录移动，超时失败' + self.phone_num)
        #     self.driver.refresh()


        self.logger.info(u'登录移动,完成登录，用户名： ' + self.phone_num + u'， 密码： ')

        # 跳转到通话详情菜单
        self.translate_to_call_detail_btn(self.phone_num, self.passwd)


        self.waiter_fordisplayed(self.driver, 'tmpl-data')
        #触发第二次短信验证
        try:
            for li in self.driver.find_elements_by_xpath('//ul[@id="month-data"]//li[starts-with(@id, "month")]'):
                self.logger.info(u'移动，查询详单,点击' + li.text)
                li.click()

                ret = self.trigger_call_detail_sms(self.phone_num, self.passwd)
                if ret == True:
                    self.logger.info(u'登录移动，触发通话详单短信验证成功，等待详单短信验证码' + self.phone_num)
                    break
                else:
                    self.logger.info(u'登录移动，触发通话详单短信验证失败' + self.phone_num)
        except Exception, e:
            self.logger.info(u'登录移动，触发通话详单短信验证码失败' + self.phone_num)
            print e
            print traceback.print_exc()

        return True, u'触发第二次验证码成功'


    def login_sec_sms(self, sms):
        self.logger.info(u'移动->查询详单->输入详单查询短信随机码' + sms)

        self.driver.find_element_by_id('vec_smspasswd').send_keys(sms)

        self.driver.find_element_by_id('vecbtn').click()

        # 等待页面加载通话记录完成
        self.logger.info(u'移动，查询详单,触发再次登录验证对话框，验证成功')

        #获取半年通话详单
        time.sleep(5)
        self.get_info_detail(self.phone_num, self.passwd)

        return True, '登录成功下载数据完成'



    def login_mobile(self, login_url, user, passwd):
        """
        登录移动商城
        :param login_url:
        :param username:
        :param passwd:
        :return:
        """

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
            self.driver.save_screenshot('divLogin.jpg')
            self.logger.info(u'登录移动，超时失败' + user)
            self.driver.refresh()

        if not self.waiter_fordisplayed(self.driver, 'stc_myaccount'):
            self.logger.info(u'登录移动，超时失败' + user)
            self.driver.refresh()

        self.logger.info(u'登录移动,完成登录，用户名： ' + user + u'， 密码： ')

        #跳转到通话详情菜单
        self.translate_to_call_detail_btn(user, passwd)



    def get_info_detail(self, user, passwd):
        """
        获取用户的半年通话详单
        :param user:
        :param passwd:
        :return:
        """

        #通话记录
        call_list = self.get_call_detail(user, passwd)

        #获取短信
        sms_list = self.get_sms_detail(user, passwd)

        #取账单数据
        bill_list = self.get_bill_detail(user, passwd)

        #取个人数据
        user_info = self.get_user_info(user, passwd)

        user_info['billData'] = bill_list
        # user_info['msgData'] = call_list
        # user_info['telData'] = sms_list


        Union.save_basic(self, self.task_id, self.phone_num, [user_info])
        Union.save_bill(self, self.task_id, self.phone_num, bill_list)
        Union.save_calls(self, self.task_id, self.phone_num, call_list)
        Union.save_sms(self, self.task_id, self.phone_num, sms_list)

        self.driver.quit()



    def get_bill_detail(self, user, passwd):
        """
        获取半年账单数据
        :param user:
        :param passwd:
        :return:
        """

        bill_data = []

        #自建request请求数据
        self.ses = requests.Session()
        for cookie in self.driver.get_cookies():
            self.ses.cookies.set(cookie['name'], cookie['value'])
            self.logger.info(u'获取半年账单数据，设置请求前的cookie。 ' + cookie['name'] + ": " + cookie['value'])

        self.bill_url = 'http://shop.10086.cn/i/v1/fee/billinfo/' + user + '?_='
        url = self.bill_url + self.get_timestamp()
        self.logger.info(u'发送半年账单的请求，url : ' + url)
        try:
            response = self.ses.get(url)
        except Exception, e:
            self.logger.info(u'发送半年账单的请求，出现异常，url : ' + url)
            self.track_back_err_print(sys.exc_info())

        try:
            data = response.content
            json_data = json.loads(data)

            if json_data['retCode'] == '000000':
                self.logger.info(u'请求账单数据成功')
            else:
                self.logger.info(u'请求账单数据失败', + json_data['retMsg'])

            for month_item in json_data['data']:
                month_bill_data = {}
                month_bill_data['month'] = month_item['billMonth']
                month_bill_data['call_pay'] = month_item['billFee']
                bill_data.append(month_bill_data)
                self.logger.info(u'账单数据 ' + str(month_bill_data))
        except Exception, e:
            pass

        return bill_data


    def get_user_info(self, user, passwd):
        """
        获取用户的个人信息
        :param user:
        :param passwd:
        :return:
        """

        user_info = {}
        user_info['phone'] = user

        #获取余额
        self.real_url = 'http://shop.10086.cn/i/v1/fee/real/' + user + '?_='
        url = self.real_url + self.get_timestamp()
        self.logger.info(u'发送余额的请求，url : ' + url)
        try:
            response = self.ses.get(url)
            data = response.content
            json_data = json.loads(data)

            if json_data['retCode'] == '000000':
                self.logger.info(u'请求余额数据成功')
            else:
                self.logger.info(u'请求余额数据失败', + json_data['retMsg'])
            user_info['phone_remain'] = json_data['data']['curFee']

        except Exception, e:
            self.logger.info(u'实时话费查询接口的请求，出现异常，url : ' + url)
            self.track_back_err_print(sys.exc_info())


        self.personal_info_url = 'http://shop.10086.cn/i/v1/cust/info/' + user + '?_='

        url = self.personal_info_url + self.get_timestamp()
        self.logger.info(u'发送个人信息的请求，url : ' + url)
        try:
            response = self.ses.get(url)
            if json_data['retCode'] == '000000':
                self.logger.info(u'请求余额数据成功')
            else:
                self.logger.info(u'请求余额数据失败', + json_data['retMsg'])

            data = response.content
            json_data = json.loads(data)

            user_info['real_name'] = json_data['data']['name']
            user_info['task_no'] = self.task_id
            user_info['user_source'] = u'移动'
            user_info['addr'] = json_data['data']['address']
            user_info['id_card'] = ''

        except Exception, e:
            self.logger.info(u'发送个人信息的请求，出现异常，url : ' + url)
            self.track_back_err_print(sys.exc_info())

        self.logger.info(u'个人信息数据 ' + str(user_info))
        return user_info

    def save_data_2_database(self, data):
        """

        :param data:
        :return:
        """

    def get_timestamp(self):
        """
        获取时间戳
        :return: 一个时间戳
        """
        return str(time.time()).replace(".", "0")

    def get_sms_detail(self, user, passwd):

        try:
            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@eventcode="UCenter_billdetailqry_type_DCXD"]')))

            self.driver.find_element_by_xpath('//li[@eventcode="UCenter_billdetailqry_type_DCXD"]').click()
            self.logger.info(u'移动，登录后，点击短信详单tab页，查询用户短信详单')
        except Exception, e:
            pass

        sms_list = []
        for li in self.driver.find_elements_by_xpath('//ul[@id="month-data"]//li[starts-with(@id, "month")]'):
            self.logger.info(u'移动，查询短信详单,点击' + li.text)

            li.click()
            time.sleep(2)

            if self.dealwith_trigger_sms(user, passwd) == True:
                self.logger.info(u'移动，查询详单,开始爬取短信详单，' + li.text)
            else:
                self.logger.info(u'移动，查询详单,短信验证失败，触发下一个月数据点击' + li.text)
                continue

            self.get_sms_detail_from_month(li, self.driver.page_source, sms_list)

        return sms_list


    def get_sms_detail_from_month(self, li, page_source, sms_list):
        """
        按月抓取短信详单
        :param li:
        :param page_source:
        :param sms_list:
        :return:
        """
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[@class="gs-page on"]')))
        except Exception, e:
            self.logger.error(u'加载月份数据失败')
            self.track_back_err_print(sys.exc_info())
            return False

        while (True):
            try:
                self.get_sms_detail_from_month_sub_page(page_source, sms_list)

                self.logger.info(li.text + u'月，短信详单：当前页的数据抓取完成')
                self.logger.info(li.text + u'月，短信详单：当前页码' + self.driver.find_element_by_id(
                    'page-demo').find_element_by_xpath('//a[@class="gs-page on"]').text)

                if EC.element_to_be_clickable((By.XPATH, '//div[@id="page-demo"]//a[@class="next"]')):
                    m = re.match('.*?(\d+)/(\d+).*', self.driver.find_element_by_id('notes1').text)
                    if m:
                        curr_page = long(m.group(1))
                        total_page = long(m.group(2))
                        if curr_page == total_page:
                            print(u'到尾页')
                            self.logger.info(li.text + u'月, 短信详单，已经到最后一页')
                            break
                        else:
                            self.driver.find_element_by_xpath(
                                '//div[@id="page-demo"]//a[@class="next"]').click()
                            self.logger.info(li.text + u'月, 短信详单，加载下一页')

                            if self.wait_for_data_ready() == True:
                                self.logger.info(li.text + u'月, 短信详单，加载下一页数据完成')
                            else:
                                self.logger.info(li.text + u'月, 短信详单，加载下一页数据失败，加载图片一直存在')

                    else:
                        print(u'没有匹配')
                        self.logger.info(li.text + u'月, 短信详单，正则查找当前页和总页数出错，没有匹配到结果')

                else:
                    self.logger.info(li.text + u'月, //div[@id="page-demo"]//a[@class="next"] 不能点击')
                    break

                self.logger.info(li.text + u'月，短信详单：下一页数据加载完成')
            except Exception, e:
                print e
                traceback.print_exc()

                self.logger.info(li.text + u'月，短信详单：没有找到下一页')
                break

    def get_sms_detail_from_month_sub_page(self, page_source, sms_list):
        """
        获取记录中每条记录
        :param page_source:
        :param sms_list:
        :return:
        """
        soup = bs(page_source)
        call_list_tag = [item for item in soup.find('table', id='tmpl-data').find('tbody').find_all('tr')]

        try:
            for call in call_list_tag:
                sms_detail_list = {}
                call_detail = [item.text for item in call.find_all('td')]
                sms_detail_list['send_time'] = call_detail[0]
                sms_detail_list['trade_way'] = call_detail[3]
                sms_detail_list['receive_phone'] = call_detail[2]
                self.logger.info(u'下载短信详单 ' + str(sms_detail_list))
                sms_list.append(sms_detail_list)
        except Exception, e:
            pass


    def wait_for_data_ready(self):
        """
        等待table中的数据加载完毕
        :return:
        """
        try:
            # 加载图片存在
            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                time.sleep(2)

            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                time.sleep(5)
            # 10s之后还未加载，过滤掉当前月份数据
            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                self.logger.info(u'移动->查询详单，加载图片一直存在，加载失败')
                return False
        except Exception, e:
            pass

        return True


    def get_call_detail_from_month(self, li, call_list):
        """

        :param page_source:
        :param call_list:
        :return:
        """
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[@class="gs-page on"]')))
        except Exception, e:
            self.logger.error(u'加载月份数据失败')
            self.track_back_err_print(sys.exc_info())
            return False

        while (True):
            try:
                self.get_call_detail_from_month_sub_page(self.driver.page_source, call_list)

                if len(call_list) == 0:
                    self.logger.info(li.text + u'月，通话详单：当前页的记录为0')

                self.logger.info(li.text + u'月，通话详单：当前页的数据抓取完成')
                self.logger.info(li.text + u'月，通话详单：当前页码' + self.driver.find_element_by_id(
                    'page-demo').find_element_by_xpath('//a[@class="gs-page on"]').text)

                if EC.element_to_be_clickable((By.XPATH, '//div[@id="page-demo"]//a[@class="next"]')):

                    m = re.match('.*?(\d+)/(\d+).*', self.driver.find_element_by_id('notes1').text)
                    if m:
                        curr_page = long(m.group(1))
                        total_page = long(m.group(2))
                        if curr_page == total_page:
                            self.logger.info(li.text + u'月, 通话详单，已经到最后一页')
                            break
                        else:
                            self.driver.find_element_by_xpath(
                                '//div[@id="page-demo"]//a[@class="next"]').click()
                            self.logger.info(li.text + u'月, 通话详单，加载下一页')
                            if self.wait_for_data_ready() == True:
                                self.logger.info(li.text + u'月, 通话详单，加载下一页数据完成')
                            else:
                                self.logger.info(li.text + u'月, 通话详单，加载下一页数据失败，加载图片一直存在')

                    else:
                        self.logger.info(li.text + u'月, 通话详单，正则查找当前页和总页数出错，没有匹配到结果')

                else:
                    self.logger.info(li.text + u'月, //div[@id="page-demo"]//a[@class="next"] 不能点击')
                    break
            except Exception, e:
                print e
                traceback.print_exc()

                self.logger.info(li.text + u'月，通话详单：没有找到下一页')
                self.track_back_err_print(sys.exc_info())
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

        try:
            for call in call_list_tag:
                call_detail_list = {}
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

        return call_list

    def trigger_call_detail_sms(self, user, passwd):
        """
        触发用户箱单的短信验证，并处理验证
        :param user:
        :param passwd:
        :return:
        """

        try:
            # 加载图片存在
            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                time.sleep(10)
            # 10s之后还未加载，过滤掉当前月份数据
            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                self.logger.info(u'移动->查询详单，加载图片一直存在，加载失败' + user)
                return False
        except Exception, e:
            pass

        #判断短信验证码的对话框是否已经展现
        try:
            element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, 'stc-send-sms')))
            self.logger.info(u'移动->查询详单，发现短信验证码对话框' + user)
        except Exception, e:
            # self.logger.info(u'移动->查询详单，没有发现短信验证码对话框， ' + sys.exc_info()[0] + ": " + sys.exc_info()[1])
            self.track_back_err_print(sys.exc_info())
            print e
            traceback.print_exc()
            return True

        # finally:
        #     self.logger.info(u'移动->查询详单，没有发现短信验证对话框，已经验证成功' + user)
        #     return True


        if self.driver.find_element_by_xpath('//div[starts-with(@id, "content")]').is_displayed() \
                or self.driver.find_element_by_id('stc-send-sms').is_displayed():
            ActionChains(self.driver).move_to_element(self.driver.find_element_by_id('vec_servpasswd')).perform()
            self.logger.info(u'移动->查询详单->移动到服务密码输入框')

            self.driver.find_element_by_id('vec_servpasswd').clear()
            self.driver.find_element_by_id('vec_servpasswd').send_keys(passwd)
            time.sleep(1)

            aa = self.driver.find_element_by_id('stc-jf-sms-count').text

            # 触发二次验证码
            time.sleep(40)
            self.logger.info(u'移动->查询详单->等待40s，等待第二次触发短信验证码' + user)

            # for cookie in self.driver.get_cookies():
            #     if cookie['name'] == 'ss':
            #         tt = cookie['value']
            #         linux_time = long(tt) / 1000

            self.driver.find_element_by_id('stc-send-sms').click()
            time.sleep(2)

            # 处理弹出的模态对话框
            try:
                alert = self.driver.switch_to.alert
                alert.accept()
            except Exception, e:
                print e

            cookies_str = json.dumps(self.driver.get_cookies())
            self.logger.info(u'移动->查询详单->点击获取查询详单的短信验证码' + cookies_str)



            # stc_sms_id = raw_input("please input image code:")
            # self.logger.info(u'移动->查询详单->输入详单查询短信随机码' + stc_sms_id)
            #
            # self.driver.find_element_by_id('vec_smspasswd').send_keys(stc_sms_id)
            #
            # self.driver.find_element_by_id('vecbtn').click()
            #
            # # 等待页面加载通话记录完成
            # self.logger.info(u'移动，查询详单,触发再次登录验证对话框')

        return True

    def translate_to_call_detail_btn(self, user, passwd):
        """
        登录后，跳转到用户通话详情页菜单


        :param user:
        :param passwd:
        :return:
        """


        try:

            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "我的账户")]')))
        except Exception, e:
            print e
            self.logger.info(u'移动，详单查询，点击我的账户异常， 没有加载我的账户btn')
            return False

        try:
            for item in self.driver.find_elements_by_xpath('//ul[@class="list-c1 js_list_active"]'):
                if u'我的账户' in item.text:
                    item.click()
                    ActionChains(self.driver).move_to_element(item).click(item).perform()
                    self.driver.save_screenshot(self.phone_num + '_billdetailqry1.jpg')
                    self.logger.info(u'移动，详单查询，点击' + item.text)
                    print('点击我的账户')
                else:
                    self.logger.info(u'移动，详单查询，跳转过程中...' + item.text)
                    print('点击' + item.text)

            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@alis="billdetailqry"]')))
            self.driver.find_element_by_xpath('//a[@alis="billdetailqry"]').click()

            self.logger.info(u'移动，详单查询，点击详单查询')
        except Exception, e:
            self.driver.save_screenshot(self.phone_num + '_billdetailqry.jpg')
            self.logger.info(u'移动，详单查询，点击详单查询失败')
            self.track_back_err_print(sys.exc_info())


        return True



    def get_call_detail(self, user, passwd):
        """
        触发用户详单的短信验证
        :return:
        """

        #触发第二次验证码
        wait = WebDriverWait(self.driver, 10)
        element = wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@eventcode="UCenter_billdetailqry_type_THXD"]')))

        self.driver.find_element_by_xpath('//li[@eventcode="UCenter_billdetailqry_type_THXD"]').click()
        self.logger.info(u'移动，登录后，点击通话详单tab页，查询用户通话详单')

        call_list = []
        for li in self.driver.find_elements_by_xpath('//ul[@id="month-data"]//li[starts-with(@id, "month")]'):
            self.logger.info(u'移动，查询详单,点击' + li.text)
            li.click()
            time.sleep(2)

            if self.dealwith_trigger_sms(user, passwd) == True:
                pass
                self.logger.info(u'移动，查询详单,开始爬取详单，' + li.text)
            else:
                self.logger.info(u'移动，查询详单,短信验证失败，触发下一个月数据点击' + li.text)
                continue

            # 取数据
            self.get_call_detail_from_month(li, call_list)

        return call_list

    def dealwith_trigger_sms(self, user, passwd):
        """
        处理触发短信二次验证前后的一些操作
        :param user:
        :param passwd:
        :return:
        """

        try:
            self.trigger_call_detail_sms(user, passwd)
            self.logger.info(u'登录移动，触发通话详单，验证成功' + user)
        except Exception, e:
            self.logger.info(u'登录移动，触发通话详单短信验证码失败' + user)
            print e
            print traceback.print_exc()

        try:
            # 加载图片存在
            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                time.sleep(10)
            # 10s之后还未加载，过滤掉当前月份数据
            if self.driver.find_element_by_xpath('//img[@src="/i/nresource/image/loading.gif"]').is_displayed():
                self.logger.info(u'移动->查询详单，加载图片一直存在，加载失败' + user)
                return False
        except Exception, e:
            pass

        try:
            # 等待数据加载完成
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//table[@id="tmpl-data"]//thead')))
        except Exception, e:
            print e
            traceback.print_exc()

        return True



    def track_back_err_print(self, info):
        """
        格式化输出异常信息
        :param info:
        :return:
        """
        self.logger.info(info[1])
        for file, lineno, function, text in traceback.extract_tb(info[2]):
            self.logger.info(file+"line:" + str(lineno) + "in" + str(function))
            self.logger.info(text)


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
