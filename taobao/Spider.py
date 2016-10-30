# -*- coding:utf-8 -*-
"""
File Name : 'Spider'.py
Description:
Author: 'wanglongzhen'
Date: '2016/9/24' '21:00'
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

from union import Union

reload(sys)
sys.setdefaultencoding("utf-8")



class UnicomSpider(Union):
    def __init__(self, username, passwd):
        print 'MobileSpider init'
        Union.__init__(self, username)
        self.task_id = Union.get_task_no(self, username)
        self.phone_num = str(username)
        self.passwd = passwd

        self.homepage = 'http://www.10010.com'
        self.login_url = 'https://uac.10010.com/portal/homeLogin'

    def __exit__(self, exc_type, exc_val, exc_tb):
        Union.__exit__(self.exc_type, exc_val, exc_tb)

    def login(self, img_sms = None):
        """
        登录入口
        :return:
        """
        if img_sms == None:
            return self.login_with_no_sms()
        else:
            return self.login_with_sms(img_sms)

    def login_with_sms(self, img_sms):

        self.driver.find_element_by_xpath("//input[@id='verifyCode']").clear()
        self.driver.find_element_by_xpath("//input[@id='verifyCode']").send_keys(img_sms)

        self.driver.find_element_by_xpath("//input[@id='login1']").click()
        self.waiter_fordisplayed(self.driver, 'nickSpan')

        if self.driver.current_url == self.login_url:
            # 没有跳转
            message = ""
            try:
                message = self.driver.find_element_by_xpath('//span[@class="error left mt35mf32"]').text
            except:
                pass
            try:
                message = self.driver.find_element_by_xpath('//span[@class="error left mt10mf32"]').text
            except:
                self.recordErrImg()
                self.logger.info(traceback.format_exc())

            print("登录失败")
            return 2, '登录跳转时失败'

        self.logger.info(u'登录成功， 用户名： ' + self.phone_num)

        return 0, '登录成功'


    def login_with_no_sms(self):
        print 'MobileSpider login'
        try:
            self.driver = webdriver.PhantomJS()
            # self.driver = webdriver.Chrome()
            self.driver.maximize_window()

            self.driver.delete_all_cookies()

            self.logger.info(u'登录联通,用户名： ' + self.phone_num + u'， 密码： ')
            self.driver.get(self.login_url)

            # time.sleep(2)
            try:
                self.driver.find_element_by_xpath("//input[@id='userName']").clear()
                self.driver.find_element_by_xpath("//input[@id='userName']").send_keys(self.phone_num)

                self.logger.info(u'登录联通,输入用户名： ' + self.phone_num + u'， 密码： ')

                self.driver.find_element_by_xpath("//input[@id='userPwd']").clear()
                self.driver.find_element_by_xpath("//input[@id='userPwd']").send_keys(self.passwd)

                self.logger.info(u'登录联通,输入密码： ' + self.phone_num + u'， 密码： ')
            except Exception, e:
                self.recordErrImg()
                self.logger.info(traceback.format_exc())
                return False, u'登录页面加载失败'

            try:
                time.sleep(2)
                if self.driver.find_element_by_xpath("//img[@id='loginVerifyImg']").is_displayed():
                    self.driver.maximize_window()
                    #不可用，图片请求一次会变化一次
                    # s = requests.session()
                    # html = s.get(self.driver.find_element_by_xpath("//img[@id='loginVerifyImg']").get_attribute('src')).content
                    # f = open('verifyCode.jpg', 'wb')
                    # f.write(html)
                    # f.close()

                    element = self.driver.find_element_by_id('loginVerifyImg')
                    src_file = self.phone_num + '_img.jpg'
                    dst_file = self.phone_num + '_img_corp.jpg'
                    # src_file = 'aaa' + 'aaaimg.jpg'
                    self.driver.save_screenshot(src_file)

                    location = element.location
                    size = element.size
                    im = Image.open(src_file)
                    # left = location['x'] + fram_rect['x']
                    # top = location['y'] + fram_rect['y']
                    # right = location['x']  + fram_rect['x'] + size['width']
                    # bottom = location['y']  + fram_rect['y'] + size['height']
                    left = location['x']
                    top = location['y']
                    right = location['x'] + size['width']
                    bottom = location['y'] + size['height']

                    box = (left, top, right, bottom)
                    im.crop(box).save(dst_file)

                    f = open(dst_file, 'rb')  # 二进制方式打开图文件
                    ls_f = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
                    f.close()
                    return 1, ls_f
                    # print("输入验证码")
                    # self.logger.error(u'登录失败，输入验证码' + self.phone_num)
            except Exception, e:
                self.recordErrImg()
                self.logger.info(traceback.format_exc())
                print traceback.print_exc()
                print("登录成功")

            self.recordErrImg()

            self.driver.find_element_by_xpath("//input[@id='login1']").click()
            self.waiter_fordisplayed(self.driver, 'nickSpan')
            if self.driver.current_url == self.login_url:
                #没有跳转
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

                print("登录失败")
                return 2, message

            self.logger.info(u'登录成功， 用户名： ' + self.phone_num)

            return 0, '登录成功'

        except Exception, e:
            return 2, '登录失败'


    def login_old(self):
        print 'MobileSpider login'
        # self.driver = webdriver.PhantomJS()
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

        self.driver.delete_all_cookies()

        self.logger.info(u'登录联通,用户名： ' + self.phone_num + u'， 密码： ')
        self.driver.get(self.login_url)

        # time.sleep(2)
        self.driver.find_element_by_xpath("//input[@id='userName']").clear()
        self.driver.find_element_by_xpath("//input[@id='userName']").send_keys(self.phone_num)

        self.logger.info(u'登录联通,输入用户名： ' + self.phone_num + u'， 密码： ')
        time.sleep(2)
        self.driver.find_element_by_xpath("//input[@id='userPwd']").clear()
        self.driver.find_element_by_xpath("//input[@id='userPwd']").send_keys(self.passwd)

        self.logger.info(u'登录联通,输入密码： ' + self.phone_num + u'， 密码： ')


        try:
            if self.driver.find_element_by_xpath("//img[@id='loginVerifyImg']").is_displayed():
                self.driver.maximize_window()
                #不可用，图片请求一次会变化一次
                # s = requests.session()
                # html = s.get(self.driver.find_element_by_xpath("//img[@id='loginVerifyImg']").get_attribute('src')).content
                # f = open('verifyCode.jpg', 'wb')
                # f.write(html)
                # f.close()

                element = self.driver.find_element_by_id('loginVerifyImg')
                self.driver.save_screenshot('img1.jpg')
                location = element.location
                size = element.size
                im = Image.open('img1.jpg')
                # left = location['x'] + fram_rect['x']
                # top = location['y'] + fram_rect['y']
                # right = location['x']  + fram_rect['x'] + size['width']
                # bottom = location['y']  + fram_rect['y'] + size['height']
                left = location['x']
                top = location['y']
                right = location['x'] + size['width']
                bottom = location['y'] + size['height']

                box = (left, top, right, bottom)
                im.crop(box).save('img_crop.jpg')

                print("输入验证码")
                self.logger.error(u'登录失败，输入验证码' + self.phone_num)
        except Exception, e:
            print traceback.print_exc()
            print("登录成功")

        time.sleep(2)
        self.driver.find_element_by_xpath("//input[@id='login1']").click()
        self.waiter_fordisplayed(self.driver, 'nickSpan')

        if self.driver.current_url == self.login_url:
            print("登录失败")
            return False, '登录跳转时失败'

        self.logger.info(u'登录成功， 用户名： ' + self.phone_num)

        return True, '登录成功'


    def spider_detail(self):

        wait = ui.WebDriverWait(self.driver, 10)
        wait.until(lambda driver: self.driver.find_element_by_class_name('mall'))

        myUnionUrl = 'https://uac.10010.com/cust/userinfo/userInfoInit'
        self.driver.get(myUnionUrl)

        if self.waiter_fordisplayed(self.driver, 'balance') == False:
            self.logger.info(u'跳转我的联通页面失败' + self.phone_num)
        else:
            self.logger.info(u'跳转我的联通页面成功' + self.phone_num)

        user_info = {}

        #抓我的交易信息
        soup = bs(self.driver.page_source)
        phone_remain = soup.find('div', id = 'balance').find('span', class_='c_orange fs_18').text
        user_info['phone_remain'] = phone_remain

        # 拼接用户个人信息URL

        infoURL = soup.find('a', id='infomgrURL').get('href')
        joinURL = urlparse.urljoin(self.driver.current_url, infoURL)
        self.driver.get(joinURL)
        # self.driver.find_element_by_id('infomgrURL').click()

        if self.waiter_fordisplayed(self.driver, 'realname') == False:
            self.logger.info(u'跳转个人信息页面失败' + self.phone_num)
        else:
            self.logger.info(u'跳转个人信息页面成功' + self.phone_num)

        soup = bs(self.driver.page_source)
        try:

            real_name = soup.find('p', id = 'realname').text
            id_card = soup.find('p', id = 'psptno').text
            addr = soup.find('div', id = 'psptaddr').text
            usersource = '联通'

            user_info['real_name'] = real_name
            user_info['id_card'] = id_card
            user_info['addr'] = addr
            user_info['user_source'] = usersource
            user_info['task_no'] = self.task_id

            self.logger.info(u'获取个人信息: realname: ' + real_name + u' idcard : ' + id_card + u' addr : ' + addr + u'usersource: ' + usersource)
        except Exception, e:
            self.recordErrImg()
            self.logger.info(traceback.format_exc())
            self.logger.error(u'获取个人信息失败: ' + self.phone_num + e)
            pass

        #历史账单
        ret = self.get_history(self.driver, self.phone_num)

        #通话详单
        detail_bill = 'http://iservice.10010.com/e3/query/call_dan.html'
        self.driver.get(detail_bill)
        self.waiter_not_displayed(self.driver, 'center_loadingGif')
        self.logger.info(u'跳转通话详情成功' + self.phone_num)

        try:
            call_dan, callsms = self.get_call_dan(self.driver, self.phone_num)
        except Exception, e:
            print e
            self.recordErrImg()
            self.logger.info(traceback.format_exc())

        #存数据到数据库中\
        self.logger.info(u'保存用户的信息到数据库，开始' + self.phone_num)
        if len(user_info) > 0:
            Union.save_basic(self, self.task_id, self.phone_num, [user_info])
        if len(ret) > 0:
            Union.save_bill(self, self.task_id, self.phone_num, ret)
        if len(call_dan) > 0:
            Union.save_calls(self, self.task_id, self.phone_num, call_dan)
        if len(callsms) > 0:
            Union.save_sms(self, self.task_id, self.phone_num, callsms)

        self.logger.info(u'保存用户的信息到数据库，完成。 ' + self.phone_num)

        self.driver.quit()

    def waiter_not_displayed(self, browser, element):
        """
        等待元素隐藏
        :param browser:
        :param element:
        :return:
        """
        count = 0
        while(True):
            count = count + 1
            if count > 4:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver : not self.driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                pass
                print('元素没有隐藏' + element)
                self.logger.error(u'元素没有隐藏' + element)

        return True

    def waiter_fordisplayed(self, browser, element):
        count = 0
        while(True):
            count = count + 1
            if count > 3:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver : driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                print('元素没有展示' + element)
                self.logger.info(u'元素没有展示' + element)

        return True

    def waiter_displayed(self, browser, element):
        """
        等待元素展示
        :param browser:
        :param element:
        :return:
        """
        count = 0
        while(True):
            count = count + 1
            if count > 3:
                return False
            try:
                ui.WebDriverWait(browser, 5).until(lambda driver : self.driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                print('元素没有显示' + element)
                self.logger.info(u'元素没有显示' + element)

        return True

    def get_call_dan(self, driver, user):
        """
        获取半年内的通话详单和短信记录
        :param driver:
        :param user:
        :return:
        """
        time.sleep(2)
        soup = bs(driver.page_source)
        call_dan_maths = [item.get('value') for item in soup.find('div', id='searchTime').find_all('li')]

        call_dan = []
        call_sms = []
        #通话详单
        for item in call_dan_maths:
            try:
                self.waiter_not_displayed(driver, 'center_loadingBg')
                driver.find_element_by_xpath('//div/ul/li[@value="' + item + '"]').click()
                self.waiter_not_displayed(driver, 'center_loadingBg')
                self.logger.info(item + u'月，通话详单：记录页面加载完成')
            except Exception, e:
                self.logger.info(item + u'月，通话详单：记录页面加载失败，跳过')
                continue

            while(True):
                try:
                    self.get_call_detail(driver.page_source, call_dan)
                    self.logger.info(item + u'月，通话详单：当前页的数据抓取完成')
                    self.logger.info(item + u'月，通话详单：当前页码' + driver.find_element_by_id('select_op').find_element_by_xpath('//option[@selected="selected"]').text)

                    self.waiter_displayed(driver, 'callDetailContent')
                    next_page_element = driver.find_element_by_xpath('//div[@class="score_page"]/div[@class="score_page_r"][text()="下一页"]')
                    next_page_element.click()
                    self.waiter_displayed(driver, 'callDetailContent')
                    self.logger.info(item + u'月，通话详单：下一页数据加载完成')
                except Exception, e:
                    self.logger.info(item + u'月，通话详单：没有找到下一页')
                    break

        #短信详单
        #跳转短信详单页面
        time.sleep(2)
        try:
            driver.get('http://iservice.10010.com/e3/query/call_sms.html')
            self.waiter_displayed(driver, 'smsmmsResultTab')
        except:
            self.logger.info(u'跳转短信详单页面报错')
            self.recordErrImg()
            self.logger.info(traceback.format_exc())

        for item in call_dan_maths:
            try:
                driver.find_element_by_xpath('//div/ul/li[@value="' + item + '"]').click()
                time.sleep(1)
                self.waiter_not_displayed(driver, 'center_loadingBg')
                self.logger.info(item + u'月，短信彩信:记录页面加载完成')
            except Exception, e:
                self.logger.info(item + u'月，短信彩信:记录页面加载失败，跳过')
                continue

            while(True):
                try:
                    if self.waiter_displayed(driver, 'smsmmsResultTab') == False:
                        try:
                            self.logger.info(item + self.driver.find_element_by_id('queryError').text)
                        except:
                            self.logger.info(item + u'queryErrorDOM不存在')
                            self.logger.info(sys.exc_info())

                    self.get_sms_detail(driver.page_source, call_sms)
                    self.logger.info(item + u'月，短信彩信:当前页的数据抓取完成')
                    self.logger.info(item + u'月，通话详单：当前页码' + driver.find_element_by_id('select_op').find_element_by_xpath('//option[@selected="selected"]').text)

                    self.waiter_displayed(driver, 'smsmmsResultTab')
                    next_page_element = driver.find_element_by_xpath('//div[@class="score_page"]/div[@class="score_page_r"][text()="下一页"]')
                    next_page_element.click()
                    self.waiter_displayed(driver, 'smsmmsResultTab')
                    self.logger.info(item + u'月，短信彩信:下一页数据加载完成')
                except Exception, e:
                    self.logger.info(item + u'月，短信彩信:没有找到下一页')
                    break

        return call_dan, call_sms

    def get_sms_detail(self, page_source, call_sms):
        """
        抽取页面中短信彩信数据
        :param page_source:
        :param call_sms:
        :return:
        """
        soup = bs(page_source)
        call_data = [call_map for call_map in soup.find('div', id='smsmmsResultTab').find('tbody').find_all('tr')]

        for tr_data in call_data:
            host = {}
            call_list = [re.sub('<(\S|\s)*>|\s|/+', '', item.text)  for item in tr_data.find_all('th')]
            if len(call_list) == 4:
                host['send_time'] = call_list[0]
                host['trade_way'] = u'发送'
                host['receive_phone'] = call_list[2]
            elif len(call_list) == 5:
                host['send_time'] = call_list[0]
                host['trade_way'] = call_list[2]
                host['receive_phone'] = call_list[3]

            self.logger.info(u'下载短信彩信详单 ' + str(host))
            call_sms.append(host)


    def get_call_detail(self, page_source, call_dan):
        """
        抽取页面中通话详单数据，并存储到call_dan中
        :param page_source:
        :param call_dan:
        :return:
        """
        soup = bs(page_source)
        call_data = [call_map for call_map in soup.find('div', id='callDetailContent').find('tbody').find_all('tr')]

        for tr_data in call_data:
            host = {}
            call_list = [item.text for item in tr_data.find_all('th')]
            host['call_time'] = call_list[0]
            host['call_type'] = call_list[2]
            host['receive_phone'] = call_list[3]
            host['trade_addr'] = call_list[1]
            host['trade_time'] = call_list[4]
            host['trade_type'] = call_list[5]
            self.logger.info(u'下载通话详单 ' + str(host))
            call_dan.append(host)

    def get_history(self, driver, user):
        """
        获取历史账单
        :param driver:
        :param user:
        :return:
        """
        time.sleep(2)
        history_list = 'http://iservice.10010.com/e3/query/history_list_ctrl.html?menuId=000100020001'
        driver.get(history_list)

        self.logger.info(u'跳转到历史账单' + user)

        self.waiter_displayed(self.driver, 'score_list_ul')
        self.waiter_displayed(self.driver, 'historylistContext')
        soup = bs(driver.page_source)
        call_math = soup.find('ul', id='score_list_ul').find('li', class_='on').text
        call_pay = soup.find('div', id='historylistContext').find('td', class_='bg fn', style=None).text


        #查询6个月的账单
        call_maths = [item.get('value') for item in soup.find('ul', id='score_list_ul').find_all('li')]

        history_host = []
        for item in call_maths:
            driver.find_element_by_xpath('//li[@value="' + item + '"]').click()
            self.waiter_not_displayed(driver, 'center_loadingGif')
            call_math = soup.find('ul', id='score_list_ul').find('li', class_='on').text
            call_pay = soup.find('div', id='historylistContext').find('td', class_='bg fn', style=None).text
            host = {}
            host['month'] = call_math
            host['call_pay'] = call_pay
            history_host.append(host)
            print item
        return history_host


