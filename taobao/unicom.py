# -*- coding:utf-8 -*-
"""
File Name : 'transferAccounts'.py
Description:
Author: 'wanglongzhen'
Date: '2016/8/1' '11:46'
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

reload(sys)
sys.setdefaultencoding("utf-8")

class TransferAccounts(object):
    def __init__(self, username = '18513622865', passwd = '861357'):
        self.headers = {
            'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36'
        }

        #数据库连接
        sql_pool = self.sql_connect()

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
        self.homepage = 'http://www.10010.com'
        login_url = 'http://www.10010.com/'
        self.login_unicom(login_url, username, passwd)

    def sql_connect(self):
        #database
        cfg_filename = 'db.conf'
        path_dirname = os.path.dirname(os.path.realpath(__file__))
        cfg_path = path_dirname + "/" + cfg_filename

        conf = ConfigParser.ConfigParser()
        conf.read(cfg_path)
        print conf.sections()

        host = conf.get('unicom', 'host')
        user = conf.get('unicom', 'username')
        passwd = conf.get('unicom', 'passwd')
        database = conf.get('unicom', 'database')

        try:
            conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=database, charset="utf8")
            # dbpool = PooledDB(MySQLdb, 2, host=host, user=user, passwd=passwd, db=database, port=3306, charset="utf8")
        except Exception as e:
            print u"数据库连接发生错误: " + str(e)
            return None
        else:
            # print u"数据库连接成功"
            return conn

    def login_unicom(self, login_url, user, passwd):
        # driver = webdriver.PhantomJS()
        driver = webdriver.Firefox()
        driver.maximize_window()

        driver.delete_all_cookies()

        self.logger = comm_log.CommLog(1)
        self.logger.info(u'登录联通,用户名： ' + user + u'， 密码： ')
        driver.get(login_url)

        if not driver.find_element_by_xpath("//a[@id='pleaseLogin']").is_displayed():
            url = driver.find_element_by_xpath("//a[@id='pleaseLogin']").get_attribute("href")
            driver.get(url)

        frame = driver.find_element_by_xpath('//iframe[@class="login_iframe"]')
        fram_rect = frame.rect
        driver.switch_to.frame(frame)

        time.sleep(2)
        driver.find_element_by_xpath("//input[@id='userName']").clear()
        driver.find_element_by_xpath("//input[@id='userName']").send_keys(user)

        self.logger.info(u'登录联通,输入用户名： ' + user + u'， 密码： ')
        time.sleep(2)
        driver.find_element_by_xpath("//input[@id='userPwd']").clear()
        driver.find_element_by_xpath("//input[@id='userPwd']").send_keys(passwd)

        self.logger.info(u'登录联通,输入密码： ' + user + u'， 密码： ')

        try:
            if driver.find_element_by_xpath("//img[@id='loginVerifyImg']").is_displayed():
                driver.maximize_window()
                #不可用，图片请求一次会变化一次
                # s = requests.session()
                # html = s.get(driver.find_element_by_xpath("//img[@id='loginVerifyImg']").get_attribute('src')).content
                # f = open('verifyCode.jpg', 'wb')
                # f.write(html)
                # f.close()


                element = driver.find_element_by_id('loginVerifyImg')
                driver.save_screenshot('img1.jpg')
                location = element.location
                size = element.size
                im = Image.open('img1.jpg')
                left = location['x'] + fram_rect['x']
                top = location['y'] + fram_rect['y']
                right = location['x']  + fram_rect['x'] + size['width']
                bottom = location['y']  + fram_rect['y'] + size['height']

                box = (left, top, right, bottom)
                im.crop(box).save('img_crop.jpg')

                print("输入验证码")
                self.logger.error(u'登录失败，输入验证码' + user)
        except Exception, e:
            print "aaa"
            print traceback.print_exc()
            print("登录成功")

        time.sleep(2)
        driver.find_element_by_xpath("//input[@id='login1']").click()
        if driver.current_url == login_url:
            print("登录失败")
            pass

        self.logger.info(u'登录成功， 用户名： ' + user)

        wait = ui.WebDriverWait(driver, 10)
        wait.until(lambda driver: driver.find_element_by_class_name('mall'))

        myUnionUrl = 'https://uac.10010.com/cust/userinfo/userInfoInit'
        driver.get(myUnionUrl)

        while(True):
            try:
                ui.WebDriverWait(driver, 1).until(lambda driver : driver.find_element_by_id('balance').is_displayed())
                break
            except Exception, e:
                pass
                print('没找到元素')
        self.logger.info(u'跳转我的联通页面成功' + user)


        #抓我的交易信息
        soup = bs(driver.page_source)
        phone_remain = soup.find('div', id = 'balance').find('span', class_='c_orange fs_18').text

        # 拼接用户个人信息URL
        infoURL = soup.find('a', id='infomgrURL').get('href')
        joinURL = urlparse.urljoin(driver.current_url, infoURL)
        driver.get(joinURL)
        # driver.find_element_by_id('infomgrURL').click()
        while(True):
            try:
                ui.WebDriverWait(driver, 1).until(lambda driver : driver.find_element_by_id('realname'))
                break
            except Exception, e:
                pass
                print('没找到个人信息元素')
        self.logger.info(u'跳转个人信息页面' + user)

        soup = bs(driver.page_source)
        try:

            real_name = soup.find('p', id = 'realname').text
            id_card = soup.find('p', id = 'psptno').text
            addr = soup.find('div', id = 'psptaddr').text
            usersource = '联通'
            self.logger.info(u'获取个人信息: realname: ' + real_name + u' idcard : ' + id_card + u' addr : ' + addr + u'usersource: ' + usersource)
        except Exception, e:
            self.logger.error(u'获取个人信息失败: ' + user + e)
            pass

        #历史账单
        ret = self.get_history(driver, user)

        #通话详单
        detail_bill = 'http://iservice.10010.com/e3/query/call_dan.html'
        driver.get(detail_bill)
        self.waiter_not_displayed(driver, 'center_loadingGif')
        self.logger.info(u'跳转通话详情成功' + user)

        call_dan, callsms = self.get_call_dan(driver, user)

        #存数据到数据库中


        driver.quit()

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
            if count > 20:
                return False
            try:
                ui.WebDriverWait(browser, 2).until(lambda driver : not driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                pass
                print('元素没有隐藏' + element)
                self.logger.error(u'元素没有隐藏' + element)

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
            if count > 20:
                return False
            try:
                ui.WebDriverWait(browser, 2).until(lambda driver : driver.find_element_by_id(element).is_displayed())
                break
            except Exception, e:
                pass
                print('元素没有显示' + element)
                self.logger.error(u'元素没有显示' + element)

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
            self.waiter_not_displayed(driver, 'center_loadingBg')
            driver.find_element_by_xpath('//div/ul/li[@value="' + item + '"]').click()
            self.waiter_not_displayed(driver, 'center_loadingBg')
            self.logger.info(item + u'月，通话详单：记录页面加载完成')

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
        driver.get('http://iservice.10010.com/e3/query/call_sms.html')
        self.waiter_displayed(driver, 'smsmmsResultTab')
        for item in call_dan_maths:
            driver.find_element_by_xpath('//div/ul/li[@value="' + item + '"]').click()
            time.sleep(1)
            self.waiter_not_displayed(driver, 'center_loadingBg')
            self.logger.info(item + u'月，短信彩信:记录页面加载完成')

            while(True):
                try:
                    self.waiter_displayed(driver, 'smsmmsResultTab')
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
        host = {}
        for tr_data in call_data:
            call_list = [re.sub('<(\S|\s)*>|\s|/+', '', item.text)  for item in tr_data.find_all('th')]
            if len(call_list) == 4:
                host['send_time'] = call_list[0]
                host['trade_away'] = u'发送'
                host['receiver_phone'] = call_list[2]
            elif len(call_list) == 5:
                host['send_time'] = call_list[0]
                host['trade_away'] = call_list[2]
                host['receiver_phone'] = call_list[3]

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
        host = {}
        for tr_data in call_data:
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
        # self.waiter_not_displayed(driver, 'center_loadingGif')
        # while(True):
        #     try:
        #         ui.WebDriverWait(driver, 1).until(lambda driver : not driver.find_element_by_id('center_loadingGif').is_displayed())
        #         break
        #     except Exception, e:
        #         pass
        #         print('没找到个人信息元素')

        self.logger.info(u'跳转到历史账单' + user)

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
            host['call_math'] = call_math
            host['call_pay'] = call_pay
            history_host.append(host)
            print item
        return history_host



def main():
    transfer_accounts = TransferAccounts()



if __name__ == '__main__':
    main()
    pass